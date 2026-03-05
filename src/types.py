from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from src.models import Book, UserRole, OrderStatus

class UserType(BaseModel):
    email:str
    username:str
    password:str
    role:UserRole

class BookType(BaseModel):
    title:Optional[str] = Field(None, min_length=4)
    author:Optional[str]= None
    price:Optional[float]= None
    publishedYear: Optional[int]= None
    genre:Optional[str]= None
    class Config:
        orm_mode = True
        from_attributes = True 

class BookResponse(BookType):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    likes_count:int

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginType(BaseModel):
    username:str
    password:str

class LoggedUser(BaseModel):
    username:str
    email:str

class OrderCreate(BaseModel):
    book_id: int

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class OrderResponse(BaseModel):
    id: int
    user: LoggedUser
    book: BookType
    status: OrderStatus
    created_at: datetime
    class Config:
        from_attributes = True 

