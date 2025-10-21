# fetch_latest.py
import os, sys, requests, json

FL_SERVER_URL = os.environ.get("FL_SERVER_URL")
OUT_PATH      = os.environ.get("OUT_PATH", "/tmp/global_weights.pt")

def main():
    if not FL_SERVER_URL:
        print("Missing FL_SERVER_URL", file=sys.stderr); sys.exit(2)

    # Ask for latest JSON (your endpoint may already return JSON; if not, EDGE can read from GCS path instead)
    r = requests.get(f"{FL_SERVER_URL}/model/latest", headers={"Accept": "application/json"}, timeout=60)
    try:
        meta = r.json()
    except Exception:
        print("model/latest is not JSON; raw:", r.text[:200], file=sys.stderr)
        sys.exit(3)

    signed = meta.get("signed_url")
    gcs    = meta.get("gcs_path")
    if not signed and not gcs:
        print("No published global model yet", file=sys.stderr); sys.exit(4)

    url = signed or gcs  # prefer signed_url if available
    if url.startswith("gs://"):
        print("This environment cannot read gs:// directly; prefer signed_url.", file=sys.stderr)
        sys.exit(5)

    b = requests.get(url, timeout=180)
    b.raise_for_status()
    with open(OUT_PATH, "wb") as f:
        f.write(b.content)
    print("Downloaded latest global model to", OUT_PATH)

if __name__ == "__main__":
    main()
