import os
import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
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
    article_id = Column(String, primary_key=True) # uuid, call a function to generate a unique ID
    google_drive_id = Column(String)
    url = Column(String, unique=True, nullable=False)
    creation_date= Column(DateTime, default=datetime.datetime.utcnow)


class Category(Base):
    __tablename__ = 'categories'
    category_name = Column(String, primary_key=True)
    min_relevance_threshold = Column(Float, nullable=False)
    min_wordcount_threshold = Column(Integer, nullable=False)


class Article_Scores(Base):
    __tablename__ = 'article_scores'
    article_id = Column(String, ForeignKey("articles.article_id", ondelete = "CASCADE"), primary_key=True)
    category_name = Column(String, ForeignKey("categories.category_name", ondelete = "CASCADE"), primary_key=True)
    relevance_score = Column(Float, nullable=False)


class Sources(Base):
    __tablename__ = 'sources'
    netloc = Column(String, primary_key=True)
    category = Column(String, ForeignKey("categories.category_name", ondelete = "CASCADE"), primary_key=True) # a topic that the source is trusted for
    path = Column(String, nullable=False)
    depth = Column(Integer, default=0) # depth of the source in the hierarchy, 0 for top-level sources
    target = Column(String, nullable=True) # pdf, website, etc

# NOTE: we should consider this table if we want articles to be associated with their sources
# which could be useful for deleting articles if a source is deleted
# we could also consider adding both the source and the category as attributes to the Article model
# but this would require each article to be associated with only a single source and category

# class Sources_For_Categories(Base):
#     # join table for sources and categories
#     # allows a source to be associated with multiple categories
#     __tablename__ = 'sources_for_categories'
#     netloc = Column(String, ForeignKey("sources.netloc", ondelete = "CASCADE"), primary_key=True)
#     category_name = Column(String, ForeignKey("categories.category_name", ondelete = "CASCADE"), primary_key=True)

#     sources = relationship(
#         "Sources",
#         back_populates="categories",
#         cascade="all, delete-orphan",
#     )


def create_db_tables():
    """Creates all the tables defined by models inheriting from Base."""
    print("Creating database tables for SQLAlchemy models...")
    # The create_all command checks for the existence of tables before creating them,
    # so it's safe to run multiple times.
    Base.metadata.create_all(engine)
    print("Tables created successfully.")


create_db_tables()