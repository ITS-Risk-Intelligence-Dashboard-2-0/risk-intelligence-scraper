from sqlalchemy.orm import sessionmaker
from shared.core_lib.models import engine, Article, Sources
import uuid

Session = sessionmaker(bind=engine)

# ------------------ ARTICLE TABLE FUNCTIONS ------------------
def sqlInsertArticle(url, netloc, path):
    """
    Inserts a new article into the database and create a unique ID for it.
    """
    session = Session()
    try:
        session.execute(text("""
            INSERT INTO sources (netloc, category, path)
            VALUES (:netloc, 'general', :path)
            ON CONFLICT (netloc, category) DO NOTHING
        """), {"netloc": netloc, "path": path})

        article_id = str(uuid.uuid4())
        session.execute(text("""
            INSERT INTO articles (article_id, url, creation_date)
            VALUES (:article_id, :url, NOW())
        """), {"article_id": article_id, "url": url})

        session.commit()
        return article_id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def sqlDeleteArticle(article_id):
    """
    Deletes an article given its unique ID.
    """
    session = Session()
    try:
        session.execute(text("""
            DELETE FROM articles WHERE article_id = :article_id
        """), {"article_id": article_id})
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


# ------------------ CATEGORY TABLE FUNCTIONS ------------------
def sqlInsertCategory(category, min_relevance_threshold=0.8, min_wordcount=200):
    session = Session()
    try:
        # Insert category with given config
        # If the category already exists, update old entry with the new values
        session.execute(text("""
            INSERT INTO categories (category_name, min_relevance_threshold, min_wordcount_threshold)
            VALUES (:name, :relevance, :wordcount)
            ON CONFLICT (category_name)
            DO UPDATE SET min_relevance_threshold = EXCLUDED.min_relevance_threshold,
                          min_wordcount_threshold = EXCLUDED.min_wordcount_threshold
        """), {
            "name": category,
            "relevance": min_relevance_threshold,
            "wordcount": min_wordcount
        })
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()



def sqlUpdateCategory(category, parameter, value):
    """
    Updates the config settings on a specified parameter for a given category.
    Only updates one specified parameter at a time.
    """
    session = Session()
    try:
        # Make sure the parameter is valid
        if parameter not in {"min_relevance_threshold", "min_wordcount_threshold"}:
            raise ValueError(f"Invalid parameter: {parameter}")

        sql = text(f"""
            UPDATE categories
            SET {parameter} = :value
            WHERE category_name = :category
        """)
        session.execute(sql, {"value": value, "category": category})
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def sqlDeleteCategory(category):
    """
    Deletes a category by name.
    """
    session = Session()
    try:
        session.execute(text("""
            DELETE FROM categories WHERE category_name = :name
        """), {"name": category})
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()



# ------------------ ARTICLE SCORE TABLE FUNCTIONS ------------------
def sqlInsertArticleScore(article_id: str, category: str, score: float):
  
    session = Session()
    try:
        # inserts a new article score or updates the existing one
        session.execute(text("""
            INSERT INTO article_scores (article_id, category_name, relevance_score)
            VALUES (:article_id, :category, :score)
            ON CONFLICT (article_id, category_name)
            DO UPDATE SET relevance_score = excluded.relevance_score
        """), {"article_id": article_id, "category": category, "score": score})
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()



# ------------------ SOURCE TABLE FUNCTIONS ------------------

def sqlSelectAllSeeds() -> list[tuple[str, str]]:
    """
    Return every unique (netloc, path) pair in sources (no duplicates).
    """
    session = Session()
    try:
        rows = session.execute(text("""
            SELECT DISTINCT netloc, path FROM sources
        """))
        return [(row.netloc, row.path) for row in rows]
    finally:
        session.close()


def sqlSeedHasCategory(netloc: str, path: str, category: str) -> bool:
    """
    Returns True if the (netloc, path) pair is associated with the given category (is trusted source). 
    Else returns False.
    """
    session = Session()
    try:
        row = session.execute(text("""
            SELECT 1 FROM sources
            WHERE netloc = :netloc AND path = :path AND category = :category
            LIMIT 1
        """), {"netloc": netloc, "path": path, "category": category}).first()
        return row is not None
    finally:
        session.close()


def sqlSelectSeedsWithCategory(category: str) -> list[tuple[str, str]]:
    """
    Return all seeds that are trusted for the given category.
    """
    session = Session()
    try:
        rows = session.execute(text("""
            SELECT netloc, path
            FROM sources
            WHERE category = :category
        """), {"category": category})
        return [(row.netloc, row.path) for row in rows]
    finally:
        session.close()


def sqlInsertSeed(netloc: str, path: str, categories: list[str]):
    """
    Insert the same (netloc, path) for multiple categories.
    “categories” can be an empty list – nothing happens.
    """
    if not categories:
        return
    session = Session()
    try:
        session.execute(text("""
            INSERT INTO sources (netloc, category, path)
            SELECT :netloc, c, :path
            FROM unnest(:cats::text[]) AS c
            ON CONFLICT (netloc, category) DO UPDATE
            SET path = EXCLUDED.path 
        """), {"netloc": netloc, "path": path, "cats": categories})
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def sqlDeleteSeeds(netloc: str, path: str):
    """
    Remove all (netloc, path) pairs from sources.
    (This will delete all categories associated with that (netloc, path).)
    """
    session = Session()
    try:
        session.execute(text("""
            DELETE FROM sources
            WHERE netloc = :netloc AND path = :path
        """), {"netloc": netloc, "path": path})
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def sqlUnassociateSeed(netloc: str, path: str, category: str):
    """
    Remove only the (netloc, category) row for that path.
    """
    session = Session()
    try:
        session.execute(text("""
            DELETE FROM sources
            WHERE netloc = :netloc
              AND path   = :path
              AND category = :category
        """), {"netloc": netloc, "path": path, "category": category})
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def sqlUpdateSeeds(netloc: str, path: str, category: str = None, parameter: str, value):
    """
    Updates the config settings on a specified parameter for a given source.
    Can choose to specify category or do it for the source in general.
    Only updates one specified parameter at a time.
    """
    session = Session()
    try:
        # Make sure the parameter is valid
        if parameter not in {"depth", "target"}:
            raise ValueError(f"Invalid parameter: {parameter}")

        if category is None:
            # If no category is specified, update it for all sources with that netloc and path
            sql = text(f"""
                UPDATE sources
                SET {parameter} = :value
                WHERE netloc = :netloc AND path = :path
            """)
            session.execute(sql, {"value": value, "netloc": netloc, "path": path})
        else:
            # If category is specified, update it for the specific source and in that category
            sql = text(f"""
                UPDATE sources
                SET {parameter} = :value
                WHERE category_name = :category
                AND netloc = :netloc AND path = :path
            """)
            session.execute(sql, {"value": value, "category": category, "netloc": netloc, "path": path})
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
