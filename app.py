from fastapi import FastAPI, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from database import engine
from database import SessionLocal
from fastapi import Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
from src.models import Book, Base, Like, User
from src.auth.tasks import get_user, create_user
from src.auth.dependencies import get_current_user, get_user, require_roles
from src.auth.security import hash_password, verify_password, create_access_token
from src.types import BookType, LoginType, UserType, OrderCreate, OrderStatusUpdate, OrderResponse, BookResponse
from src.books.tasks import get_book
from src.orders.tasks import create_order, update_order, delete_order, list_orders, list_user_orders
from src import models
from database import get_db
#Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
app = FastAPI()


@app.post("/register/")
def register(user:UserType, db: Session = Depends(get_db)):

    hashed_password = hash_password(user.password)
    user = create_user(db, user.username, user.email, hashed_password, user.role)
    return {"username": user.username, "role": user.role, "email":user.email}

@app.post("/login/")
def login(form_data: LoginType, response: Response,  db: Session = Depends(get_db)):
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token =create_access_token({"sub": user.username, "role": user.role})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 30    
    )
    return { "detail":"Login Sucessfully", "user":{"name":user.username, "role":user.role, "id":user.id}}

@app.post("/logout/")
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
async def add_book(book: BookType, db: Session = Depends(get_db), current_user = Depends(require_roles(["admin", "staff"]))):
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
async def update_book(book_id: int, book: BookType, db: Session = Depends(get_db), current_user = Depends(require_roles(["admin", "staff"]))):
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


@app.get("/books/{book_id}/", response_model=BookResponse)
async def detail_book(book_id:int, db: Session = Depends(get_db)):
    return get_book(book_id=book_id, db=db )


@app.delete("/books/{book_id}/")
def delete_book(book_id:int, db: Session = Depends(get_db), current_user = Depends(require_roles(["admin", "staff"]))):
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


###########Orders###########
@app.get("/orders/", response_model=list[OrderResponse])
def list_all_order(db: Session= Depends(get_db), skip:int = Query(0, ge=0), limit:int = Query(20, le=100), current_user = Depends(require_roles(["staff"]))):
    if current_user.role != "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized sees this list"
        )
    return list_orders(db, skip, limit)

@app.get("/orders/my_orders/", response_model=list[OrderResponse])
def list_all_user_order(current_user = Depends(get_current_user), db: Session= Depends(get_db), skip:int = Query(0, ge=0), limit:int = Query(20, le=100)):
    return list_user_orders(user_id=current_user.id, db=db, skip=skip, limit=limit)

@app.post("/orders/", response_model=OrderResponse)
def bought_book(order: OrderCreate, db:Session= Depends(get_db), current_user = Depends(get_current_user)):
    return create_order(db, user_id=current_user.id, book_id=order.book_id)

@app.patch("/orders/{order_id}/status/")
async def update_order_status(order_id:int, data: OrderStatusUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        return update_order(db, order_id=order_id, new_status = data.status, user = current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="An error appied during the process! Please try again later")

@app.delete("/orders/{order_id}")
def order_delele(order_id, db: Session = Depends(get_db), current_user = Depends(require_roles(['staff']))):
    return delete_order(db, order_id)

##########LIKE############
@app.post("/books/{book_id}/like")
def toogle_like(book_id:int, db:Session = Depends(get_db), current_user:User = Depends(get_current_user)):
    book = db.query(Book).filter_by(id=book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    like = db.query(Like).filter_by(user_id=current_user.id, book_id=book_id).first()
    if like:
        db.delete(like)
        db.commit()
        return {"detail": "Like removed", "total_likes": db.query(Like).filter_by(book_id=book_id).count() }
    else:
        new_like = Like(user_id=current_user.id, book_id=book_id)
        db.add(new_like)
        try:
            db.commit()
        except:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not like the book, please try again later")
        return {"detail": "Book liked", "total_likes": db.query(Like).filter_by(book_id=book_id).count() }


@app.get("/protected")
def protected_route(current_user:User = Depends(require_roles(["admin", "staff"]))):
    return {
        "message": "You are authenticated",
        "username": current_user.username,
        "role": current_user.role
    }
