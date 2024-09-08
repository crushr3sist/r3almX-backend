import uuid

from pydantic import BaseModel


class Post(BaseModel):
    post_id: str | uuid.UUID
    author_id: str
    post_body: str
    post_hashtags: str
    post_mentions: str



class PostResponse(Post):
    post_id: str
    post_resp_id: str
    resp_body: str
