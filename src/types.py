from typing import Optional
from pydantic import BaseModel, Field

class UserType(BaseModel):
    email:str
    username:str
    password:str
    role:str


class BookType(BaseModel):
    title:Optional[str] = Field(None, min_length=4)
    author:Optional[str]= None
    price:Optional[float]= None
    publishedYear: Optional[int]= None
    genre:Optional[str]= None

    class config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginType(BaseModel):
    username:str
    password:str