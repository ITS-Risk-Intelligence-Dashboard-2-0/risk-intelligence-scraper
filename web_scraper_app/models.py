import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import JSONB

# Get the database URL from the environment variable provided by docker-compose
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    # If running locally without docker-compose, you might need to load a .env file
    # or set this variable manually. For the docker setup, this should always be present.
    raise Exception("DATABASE_URL environment variable not set.")

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Base class for your declarative models
Base = declarative_base()


# --- DEFINE YOUR SQLALCHEMY MODELS BELOW ---
# Your models should inherit from the 'Base' class.
# For example:
#
# from sqlalchemy import Column, Integer, String, DateTime
# import datetime
#
# class Article(Base):
#     __tablename__ = 'articles'
#     id = Column(Integer, primary_key=True)
#     url = Column(String, unique=True, nullable=False)
#     title = Column(String)
#     scraped_at = Column(DateTime, default=datetime.datetime.utcnow)
#
# -----------------------------------------
class Article(Base):
    __tablename__ = 'articles'
    art_id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String)
    scraped_at = Column(DateTime, default=datetime.datetime.utcnow)

    embeddings = relationship(
        "EmbeddedArticle",
        back_populates="article",
        cascade="all, delete-orphan",
    )


class Config(Base):
    __tablename__ = 'configs'
    config_id = Column(Integer, primary_key=True)
    config_json = Column(JSONB, nullable=False)


class Embedded_Articles(Base):
    __tablename__ = 'embedded_articles'
    embedded_id = Column(Integer, primary_key=True)
    art_id = Column(Integer, ForeignKey("articles.art_id"), nullable=False)
    vectorized_content = Column(JSONB) # probably need to change this type later, still working on setting up pgvector
    article = relationship("Article", back_populates="embeddings")


def create_db_tables():
    """Creates all the tables defined by models inheriting from Base."""
    print("Creating database tables for SQLAlchemy models...")
    # The create_all command checks for the existence of tables before creating them,
    # so it's safe to run multiple times.
    Base.metadata.create_all(engine)
    print("Tables created successfully.")



if __name__ == "__main__":
    create_db_tables()