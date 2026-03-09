from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LinkBase(BaseModel):
    original_url: HttpUrl

class LinkCreate(LinkBase):
    custom_alias: Optional[str] = Field(None, min_length=3, max_length=20)
    expires_at: Optional[datetime] = None

class LinkUpdate(BaseModel):
    original_url: HttpUrl

class LinkResponse(BaseModel):
    short_code: str
    original_url: str
    short_url: str
    created_at: datetime
    expires_at: Optional[datetime]
    clicks: int
    is_active: bool
    custom_alias: Optional[str]
    
    class Config:
        from_attributes = True

class LinkStats(LinkResponse):
    last_accessed: Optional[datetime]
    created_by: Optional[str]