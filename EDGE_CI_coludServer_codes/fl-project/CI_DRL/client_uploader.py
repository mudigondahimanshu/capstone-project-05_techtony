# client_uploader.py
import os, sys, time, requests

FL_SERVER_URL = os.environ.get("FL_SERVER_URL")
CLIENT_ID     = os.environ.get("CLIENT_ID", "edge-unknown")
ROUND_ID      = os.environ.get("ROUND_ID")  # must be string/int
WEIGHTS_PATH  = os.environ.get("WEIGHTS_PATH", "/tmp/weights.pt")

def post_update():
    if not FL_SERVER_URL or not ROUND_ID:
        print("Missing FL_SERVER_URL or ROUND_ID", file=sys.stderr)
        sys.exit(2)
    if not os.path.exists(WEIGHTS_PATH):
        print(f"weights file not found: {WEIGHTS_PATH}", file=sys.stderr)
        sys.exit(3)

    url = f"{FL_SERVER_URL}/update"
    for attempt in range(5):
        try:
            with open(WEIGHTS_PATH, "rb") as f:
                r = requests.post(url, files={
                    "file": ("weights.pt", f, "application/octet-stream"),
                }, data={
                    "round_id": str(ROUND_ID),
                    "client_id": CLIENT_ID,
                }, timeout=120)
            print("POST /update:", r.status_code, r.text[:200])
            if r.ok:
                return 0
        except Exception as e:
            print("upload attempt failed:", e, file=sys.stderr)
        time.sleep(3 * (attempt + 1))
    return 1

if __name__ == "__main__":
    sys.exit(post_update())
