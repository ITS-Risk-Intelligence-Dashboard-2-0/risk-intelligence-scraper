from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session # class, need to use SessionLocal
from db import SessionLocal, engine
from models import Base, User
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    # add any other origins you need, including deployed URLs
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow all (not recommended in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session is the base class, used for type hints only
# SessionLocal is the class that makes sessions
# SessionLocal() is a session object with add, commit, query, close

# Create tables if they don't exist yet
Base.metadata.create_all(bind=engine)

# creates new db session for each request, cleans up automatically after request is done. Injected into routes using Depends(get_db)
def get_db():
    db = SessionLocal() 
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def get_all_users(db: Session = Depends(get_db)):
    users_query = db.query(User)
    return users_query.all() # SELECT *

@app.post("/create")
async def create_user(username: str, email: str, db: Session = Depends(get_db)):
    user = User(username=username, email=email)
    db.add(user)
    db.commit()
    return {"user added": user.username}

@app.put("/update/{id}")
async def update_user(id: int, new_username: str="", new_email: str = "", db: Session = Depends(get_db)):
    users_query = db.query(User).filter(User.id==id)
    user = users_query.first()
    if new_username:
        user.username = new_username
    if new_email:
        user.email = new_email

    db.add(user)
    db.commit()
    return {"message": f"User {user.username} updated successfully"}

@app.delete("/delete/{id}")
async def delete_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id==id).first()
    if not user:
        return {"error": "User not found"}
    db.delete(user)
    db.commit()
    return({"user deleted": user.username})