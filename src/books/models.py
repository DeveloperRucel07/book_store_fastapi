from sqlalchemy import Column, ForeignKey, Integer, String, Float, Integer, DateTime
from database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="reader")
    books = relationship("src.books.models.Book", back_populates="owner")
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
    owner = relationship("src.books.models.User", back_populates="books")
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

