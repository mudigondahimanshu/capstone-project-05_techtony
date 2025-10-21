import io, os, tempfile, glob
from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.responses import PlainTextResponse
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from server.schemas import StartRoundReq, StartRoundResp, LatestResp, UpdateResp, CloseResp
from server.storage import upload_file, sign_url, write_latest, read_latest, gcs_path, download_to_file, client, bucket
from server.aggregate import fedavg
from server.auth import check_admin
import torch

app = FastAPI(title="FL Server", version="0.1.0")

# ENV
BUCKET = os.environ["BUCKET"]
SIGN_URL_TTL = int(os.environ.get("SIGN_URL_TTL", "900"))

# In-GCS structure:
# updates/round-XXXX/<client_id>.pt
# global_models/round-XXXX/weights.pt
# global_models/latest.json

# Simple round counter persisted in GCS
ROUND_STATE_BLOB = "global_models/round_state.txt"

def _get_current_round():
    blob = bucket.blob(ROUND_STATE_BLOB)
    if not blob.exists():
        return 0
    return int(blob.download_as_text().strip())

def _set_current_round(r):
    blob = bucket.blob(ROUND_STATE_BLOB)
    blob.upload_from_string(str(r), content_type="text/plain")

# Prometheus metrics
REG = CollectorRegistry()
FL_ROUND_GAUGE   = Gauge("fl_round_current", "Current round", registry=REG)
FL_UPDATES_TOTAL = Counter("fl_updates_total", "Total client updates received", ["round_id"], registry=REG)

@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"

@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(REG), media_type=CONTENT_TYPE_LATEST)

@app.get("/model/latest", response_model=LatestResp)
def model_latest():
    latest = read_latest()
    if not latest:
        # Nothing seeded yet; return empty round 0
        return LatestResp(round=0, gcs_path="", signed_url="")
    url = sign_url(latest["path"], ttl_seconds=SIGN_URL_TTL)
    return LatestResp(round=latest["round"], gcs_path=f"gs://{BUCKET}/{latest['path']}", signed_url=url)

@app.post("/round/start", response_model=StartRoundResp)
def start_round(body: StartRoundReq, _=Depends(check_admin)):
    r = _get_current_round() + 1
    _set_current_round(r)
    FL_ROUND_GAUGE.set(r)
    # ensure updates folder exists implicitly on first upload
    return StartRoundResp(round_id=r)

@app.post("/update", response_model=UpdateResp)
def submit_update(
    round_id: int = Form(...),
    client_id: str = Form(...),
    file: UploadFile = File(...)
):
    # store client weights for this round in GCS
    rel = gcs_path(f"updates/round-{round_id:04d}", f"{client_id}.pt")
    # upload directly from stream to temp then to GCS
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp:
        tmp.write(file.file.read())
        tmp.flush()
        upload_file(tmp.name, rel)
    FL_UPDATES_TOTAL.labels(round_id=str(round_id)).inc()
    return UpdateResp(status="received")

@app.post("/round/close", response_model=CloseResp)
def close_round(_=Depends(check_admin)):
    r = _get_current_round()
    assert r > 0, "No round started"

    # download all client weights from GCS to temp dir
    prefix = f"updates/round-{r:04d}/"
    blobs = client.list_blobs(BUCKET, prefix=prefix)
    local_paths = []
    for b in blobs:
        if not b.name.endswith(".pt"):
            continue
        local_tmp = tempfile.NamedTemporaryFile(suffix=".pt", delete=False).name
        download_to_file(b.name, local_tmp)
        local_paths.append(local_tmp)

    if not local_paths:
        # No updates received, keep previous latest
        return CloseResp(round=r, gcs_path="")

    # aggregate with FedAvg
    agg_state = fedavg(local_paths)
    out_dir_rel = f"global_models/round-{r:04d}"
    os.makedirs("/tmp/out", exist_ok=True)
    out_local = "/tmp/out/weights.pt"
    torch.save(agg_state, out_local)

    dest = gcs_path(out_dir_rel, "weights.pt")
    upload_file(out_local, dest)

    # update latest.json
    write_latest(r, dest)

    return CloseResp(round=r, gcs_path=f"gs://{BUCKET}/{dest}")
