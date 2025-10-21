import json, os, tempfile, time
from google.cloud import storage

BUCKET = os.environ["BUCKET"]  # GCS bucket name (no gs://)
client = storage.Client()
bucket = client.bucket(BUCKET)

def gcs_path(*parts):  # join with '/'
    return "/".join(parts)

def upload_bytes(data: bytes, path: str, content_type="application/octet-stream"):
    blob = bucket.blob(path)
    blob.upload_from_string(data, content_type=content_type)
    return f"gs://{BUCKET}/{path}"

def upload_file(local_path: str, path: str):
    blob = bucket.blob(path)
    blob.upload_from_filename(local_path)
    return f"gs://{BUCKET}/{path}"

def download_to_file(path: str, dst_local: str):
    blob = bucket.blob(path)
    blob.download_to_filename(dst_local)

def sign_url(path: str, ttl_seconds: int):
    blob = bucket.blob(path)
    return blob.generate_signed_url(expiration=ttl_seconds)

def write_latest(round_id: int, weights_rel_path: str):
    latest = {"round": round_id, "path": weights_rel_path, "updated_at": int(time.time())}
    blob = bucket.blob("global_models/latest.json")
    blob.upload_from_string(json.dumps(latest, indent=2), content_type="application/json")

def read_latest():
    blob = bucket.blob("global_models/latest.json")
    if not blob.exists():
        return None
    return json.loads(blob.download_as_text())
