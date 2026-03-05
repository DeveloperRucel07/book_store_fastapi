from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.models import Book


def get_book(book_id:int, db: Session):
    book = db.query(Book).filter(Book.id == book_id).first()
    return book