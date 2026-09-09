from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import Base, engine, get_db
import models
from auth import hash_password, verify_password, create_access_token, get_current_username

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


@app.get('/')
def root():
    return 'Hello World'


@app.get('/items/{item_id}')
def read_item(item_id: int):
    return {"item_id": item_id}


@app.post('/register')
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"id": new_user.id, "username": new_user.username, "email": new_user.email}


@app.post('/login')
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get('/me')
def read_current_user(username: str = Depends(get_current_username), db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": db_user.id, "username": db_user.username, "email": db_user.email}