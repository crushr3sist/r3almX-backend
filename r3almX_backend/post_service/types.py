import uuid

from pydantic import BaseModel, field_validator


class Post(BaseModel):
    post_id: str | uuid.UUID
    author_id: str
    post_body: str
    post_hashtags: str
    post_mentions: str

    @field_validator("post_hashtags")
    def hashtag_filter(cls, value):
        if not value.startswith("#"):
            raise ValueError("corrupted hashtag")
        return value

    @field_validator("post_mentions")
    def hashtag_filter(cls, value):
        if not value.startswith("@"):
            raise ValueError("corrupted mentions")
        return value


class PostResponse(Post):
    post_id: str
    post_resp_id: str
    resp_body: str
