from typing import List
import torch

def fedavg(weight_paths: List[str], device="cpu"):
    """Load multiple state_dict files and average them."""
    assert len(weight_paths) > 0, "No client weights provided"
    avg_state = None
    for p in weight_paths:
        sd = torch.load(p, map_location=device)
        if avg_state is None:
            avg_state = {k: v.clone().to(device) for k, v in sd.items()}
        else:
            for k in avg_state.keys():
                avg_state[k] += sd[k].to(device)
    # divide by num
    for k in avg_state.keys():
        avg_state[k] /= float(len(weight_paths))
        avg_state[k] = avg_state[k].to("cpu")
    return avg_state
