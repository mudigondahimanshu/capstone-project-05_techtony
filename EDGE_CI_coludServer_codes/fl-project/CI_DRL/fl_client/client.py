# ~/CI_DRL/fl_client/client.py
import os, requests, torch

class FLClient:
    """

    Minimal client: pull latest global weights -> load into model -> after local train push update.
    Works with model.state_dict() (recommended).
    """
    def __init__(self, server_url: str, client_id: str):
        self.server_url = server_url.rstrip("/")
        self.client_id = client_id

    # --- PULL ---
    def fetch_latest(self, dst="global.pt"):
        r = requests.get(f"{self.server_url}/model/latest", timeout=30); r.raise_for_status()
        info = r.json()
        url = info.get("signed_url", "")
        round_id = int(info.get("round", 0))
        if url:
            rr = requests.get(url, timeout=120); rr.raise_for_status()
            with open(dst, "wb") as f: f.write(rr.content)
        return round_id, dst  # ok even if no file yet (round 0)

    @staticmethod
    def load_into_model(model, path):
        if os.path.exists(path) and os.path.getsize(path) > 0:
            state = torch.load(path, map_location="cpu")
            # be lenient to avoid hard coupling to keys
            model.load_state_dict(state, strict=False)

    # --- PUSH ---
    def send_update_from_model(self, model, round_id: int, tmp_path="local_update.pt"):
        torch.save(model.state_dict(), tmp_path)
        return self.send_file(tmp_path, round_id)

    def send_file(self, path, round_id: int):
        with open(path, "rb") as f:
            files = {"file": (os.path.basename(path), f, "application/octet-stream")}
            data  = {"client_id": self.client_id, "round_id": str(round_id)}
            r = requests.post(f"{self.server_url}/update", files=files, data=data, timeout=180)
            r.raise_for_status()
            return r.json()
