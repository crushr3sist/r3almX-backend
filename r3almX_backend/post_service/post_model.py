import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from r3almX_backend.database import Base


class PostModel(Base):
    __tablename__ = "posts"
    id = Column(UUID(as_uuid=True), default=uuid.uuid4(), primary_key=True)
    post_name = Column(String(), nullable=False)
    post_body = Column(String(), nullable=False)
    post_hashtags = Column(String(), nullable=False)
    post_mentions = Column(String(), nullable=True)
    author = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    post_relationship = relationship("User", back_populates="posts_created")

    def __init__(self, post_name, post_body, post_hashtags, post_mentions):
        self.post_name = post_name
        self.post_body = post_body
        self.post_hashtags = post_hashtags
        self.post_mentions = post_mentions
