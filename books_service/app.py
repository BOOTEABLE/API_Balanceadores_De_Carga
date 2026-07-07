from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
import time
from sqlalchemy.exc import OperationalError
import os
from typing import Optional

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/biblioteca")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True) # Esto DEBE ser Column(Integer, ...)
    title = Column(String, index=True)
    author = Column(String)
retries = 5
while retries > 0:
    try:
        Base.metadata.create_all(bind=engine)
        print("Conectado a la base de datos y tablas creadas.")
        break 
    except OperationalError:
        print(f"Base de datos no lista. Reintentando en 5 segundos... (Quedan {retries} intentos)")
        retries -= 1
        time.sleep(5) # Espera 5 segundos antes de volver a intentar
app = FastAPI(title="Servicio de Libros")
class BookCreate(BaseModel):
    id: Optional[int] = None # Aquí sí es válido usar Optional
    title: str
    author: str
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.post("/api/books/")
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    # Si envías el ID, lo toma; si no, SQLAlquemy asigna el siguiente valor autoincremental
    db_book = Book(id=book.id, title=book.title, author=book.author)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book
@app.get("/api/books/")
def read_books(db: Session = Depends(get_db)):
    return db.query(Book).all()

@app.put("/api/books/{book_id}")
def update_book(book_id: int, book: BookCreate, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    db_book.title = book.title
    db_book.author = book.author
    db.commit()
    db.refresh(db_book)
    return db_book


@app.delete("/api/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    db.delete(db_book)
    db.commit()
    return {"message": "Libro eliminado exitosamente"}

# Ruta para obtener un libro específico por su ID (GET)
@app.get("/api/books/{book_id}")
def read_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return db_book