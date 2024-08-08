from pydantic import BaseModel
from pydantic import Field


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str | None = Field(max_length=100)
    priority: int = Field(ge=0, le=5)
    complete: bool = False
