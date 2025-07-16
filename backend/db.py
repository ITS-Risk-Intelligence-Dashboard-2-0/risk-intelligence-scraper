from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base

# add username and password into this
url = URL.create(
    drivername="postgresql",
    username="alvinjg",
    host="localhost",
    database="userdb",
    port=5432
)

engine = create_engine(url)
# Best practice: use SessionLocal so FastAPI can inject it later
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()