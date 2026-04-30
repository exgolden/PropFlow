# db/init.py
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "property.db")
SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "schemas")

# Order matters — tables with foreign keys must come after the tables they reference
SCHEMA_FILES = [
    "usuarios.sql",
    "unidades.sql",
    "inquilinos.sql",
    "contratos.sql",
    "facturas.sql",
    "mantenimientos.sql",
    "documentos.sql",
    "notificaciones_log.sql",
]


def get_connection() -> sqlite3.Connection:
    """
    Opens a single connection to the DB with the required PRAGMAs.
    Use this directly only in init_db(). 
    Everywhere else in the app, use get_db() instead.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """
    Context manager for database access. Use this for every DB operation
    in the app — it ensures the connection is always properly closed,
    and rolls back automatically if something goes wrong.

    Usage:
        with get_db() as conn:
            conn.execute("SELECT * FROM unidades")
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Creates all tables by running each schema file in order.
    Safe to run multiple times — all statements use CREATE TABLE IF NOT EXISTS.
    """
    conn = get_connection()

    try:
        for filename in SCHEMA_FILES:
            filepath = os.path.join(SCHEMAS_DIR, filename)
            with open(filepath, "r") as f:
                sql = f.read()
            conn.executescript(sql)
            print(f"✓ {filename}")

        print(f"\nBase de datos lista en: {DB_PATH}")

    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    init_db()