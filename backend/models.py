from pydantic import BaseModel


class StoryCreate(BaseModel):
    title: str
    summary: str
    category: str
    current_status: str
    source: str


class SubscribeRequest(BaseModel):
    email: str
    story_ids: list[str] = []
    lang: str = "en"


class WatchRequest(BaseModel):
    story_id: str
    token: str
