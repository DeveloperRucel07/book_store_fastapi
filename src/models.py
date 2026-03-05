from sqlalchemy import Column, ForeignKey, Integer, String, Float, Integer, DateTime, UniqueConstraint
from database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum
from sqlalchemy import Enum as SQLEnum

class OrderStatus(str, Enum):
    bought = "bought"
    return_requested = "return_requested"
    returned = "returned"
    cancel = "cancel"

class UserRole(str, Enum):
    reader = "reader"
    staff = "staff"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(SQLEnum(UserRole), default=UserRole.reader)
    books = relationship("src.models.Book", back_populates="owner")
    likes = relationship("src.models.Like", back_populates="user")
    orders = relationship("src.models.Order", back_populates="user")
    member_since = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    price = Column(Float)
    publishedYear = Column(Integer)
    genre = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("src.models.User", back_populates="books")
    likes = relationship("src.models.Like", back_populates="book")
    orders = relationship("src.models.Order", back_populates="book")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("src.models.User", back_populates="orders")
    book_id = Column(Integer, ForeignKey("books.id"))
    book = relationship("src.models.Book", back_populates="orders")
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.bought)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("src.models.User", back_populates="likes")
    book_id = Column(Integer, ForeignKey("books.id"))
    book = relationship("src.models.Book", back_populates="likes")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="unique_user_book_like"),
    )