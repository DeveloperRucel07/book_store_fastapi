from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from database import engine
from database import SessionLocal
from fastapi import Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
from src.books import models as model_book
from src.auth import tasks, security, dependencies, models
from src.types import BookType, LoginType, UserType

Book = model_book.Book
models.Base.metadata.create_all(bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()


@app.post("/register")
def register(user:UserType, db: Session = Depends(get_db)):

    hashed_password = security.hash_password(user.password)
    user = tasks.create_user(db, user.username, user.email, hashed_password, user.role)
    return {"username": user.username, "role": user.role, "email":user.email}

@app.post("/login")
def login(form_data: LoginType, response: Response,  db: Session = Depends(get_db)):
    user = tasks.get_user(db, form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = security.create_access_token({"sub": user.username, "role": user.role})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 30    
    )
    return { "detail":"Login Sucessfully", "user":{"name":user.username, "role":user.role, "id":user.id}}

@app.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}

@app.get("/")
def home():
    return {"message":"Hello and welcome to my bookstore"}

@app.get("/books/", response_model=list[BookType], status_code=200)
async def get_books(db: Session = Depends(get_db)):
    return db.query(Book).all()

@app.post("/books/")
async def add_book(book: BookType, db: Session = Depends(get_db), current_user = Depends(dependencies.require_roles(["admin", "staff"]))):
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

@app.patch("/books/{book_id}")
async def update_book(book_id: int, book: BookType, db: Session = Depends(get_db), current_user = Depends(dependencies.require_roles(["admin", "staff"]))):
    book_dict = book.model_dump()
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


@app.delete("/books/{book_id}")
def delete_book(book_id:int, db: Session = Depends(get_db), current_user = Depends(dependencies.require_roles(["admin", "staff"]))):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    if db_book.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this book"
        )
    db.delete(db_book)
    db.commit()
    return {"detail":"Book deleted successfully"}


@app.get("/protected")
def protected_route(current_user = Depends(dependencies.require_roles(["admin", "staff"]))):
    return {
        "message": "You are authenticated",
        "username": current_user.username,
        "role": current_user.role
    }


@app.get("/books/{book_id}")
async def detail_book(book_id:int):
    return {"book": f"this book has a id {book_id}"}