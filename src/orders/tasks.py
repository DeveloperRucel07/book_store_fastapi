from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.models import Book, Order, OrderStatus


def list_orders(db: Session,skip:int=0, limit:int=100):
    return db.query(Order).offset(skip).limit(limit).all()


def list_user_orders(user_id:int, db: Session,skip:int=0, limit:int=100):
    return db.query(Order).filter(Order.user_id == user_id).offset(skip).limit(limit).all()


def create_order(db: Session, user_id: int, book_id: int ):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    order = Order(
        user_id = user_id,
        book_id = book_id,
        status = OrderStatus.bought
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def update_order(db: Session, order_id, new_status: OrderStatus, user):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Order not Found"
    )
    if user.role != "staff" and order.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this order"
        )
    order.status = new_status
    db.commit()
    db.refresh(order)
    return order


def delete_order(db: Session, order_id):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Order not Found"
    )
    db.delete(order)
    db.commit()
    return {"message": "Order deleted successfully"}

