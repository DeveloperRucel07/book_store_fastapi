from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.models import Book, Like, User
from src.types import BookType

def get_all_books(db: Session):
    books_with_likes = (db.query(Book,func.count(Like.id).label("likes_count")
        ).outerjoin(Like, Like.book_id == Book.id)
        .group_by(Book.id)
        .all()
    )
    result = []
    for book, likes_count in books_with_likes:
        result.append({
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "price": book.price,
            "publishedYear": book.publishedYear,
            "genre": book.genre,
            "owner_id": book.owner_id,
            "created_at": book.created_at,
            "updated_at": book.updated_at,
            "likes_count": likes_count
        })

    return result


def get_book(book_id:int, db: Session):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    likes_count = len(book.likes)
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "price": book.price,
        "publishedYear": book.publishedYear,
        "genre": book.genre,
        "owner_id": book.owner_id,
        "created_at": book.created_at,
        "updated_at": book.updated_at,
        "likes_count": likes_count
    }

def create_book(book, current_user:User, db: Session):
    db_book = Book(**book.model_dump(), owner_id=current_user.id)
    if book.title is not None:
        if not isinstance(book.title, str) or len(book.title) <= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book name must be more than 3 characters"
            )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def book_update(book_id:int, current_user: User, db: Session, book: BookType ):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    if book.title is not None:
        if not isinstance(book.title, str) or len(book.title) <= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book title must be more than 3 characters"
            )
    if db_book.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this book"
        )
    update_data = book.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_book, key, value)
    db.commit()
    db.refresh(db_book)
    return db_book

def book_deleted(current_user: User, db: Session, book_id:int):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    if db_book.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this book"
        )
    db.delete(db_book)
    db.commit()
    return {"detail":"Book deleted successfully"}