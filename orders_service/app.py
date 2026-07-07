from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
import time
from sqlalchemy.exc import OperationalError
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/biblioteca")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de Base de Datos para las rdenes
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    book_id = Column(Integer, index=True)

# Reintentos de conexión a Postgres
retries = 5
while retries > 0:
    try:
        Base.metadata.create_all(bind=engine)
        print("Conectado a la base de datos y tabla de ordenes creada.")
        break 
    except OperationalError:
        print(f"Base de datos no lista. Reintentando en 5 segundos... (Quedan {retries} intentos)")
        retries -= 1
        time.sleep(5)

app = FastAPI(title="Servicio de Ordenes")

# Esquema de validación
class OrderCreate(BaseModel):
    user_id: int
    book_id: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- RUTAS CRUD ---
@app.post("/api/orders/")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = Order(user_id=order.user_id, book_id=order.book_id)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/api/orders/")
def read_orders(db: Session = Depends(get_db)):
    return db.query(Order).all()

@app.get("/api/orders/user/{user_id}")
def read_orders_by_user(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    if not orders:
        raise HTTPException(status_code=404, detail="No se encontraron órdenes para este usuario")
    return orders

@app.delete("/api/orders/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if db_order is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    db.delete(db_order)
    db.commit()
    return {"message": "Orden eliminada exitosamente"}