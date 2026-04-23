from pydantic import BaseModel


class MonitoringTokenRequest(BaseModel):
    key: str