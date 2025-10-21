from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class StartRoundReq(BaseModel):
    expected_clients: Optional[int] = Field(default=None, description="Optional expected client count")

class StartRoundResp(BaseModel):
    round_id: int

class LatestResp(BaseModel):
    round: int
    gcs_path: str
    signed_url: str

class UpdateResp(BaseModel):
    status: str

class CloseResp(BaseModel):
    round: int
    gcs_path: str
