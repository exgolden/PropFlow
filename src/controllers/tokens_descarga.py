# src/controllers/tokens_descarga.py
"""
Controller para la gestión de tokens de descarga firmados.
Permite generar enlaces temporales para que inquilinos descarguen
documentos sin necesidad de autenticación.
"""
import secrets
from datetime import datetime, timedelta
from db.init import get_db
from src.logger import get_logger

logger = get_logger()


def create_token(document_id: int) -> dict:
    """
    Generates a signed download token for a given document.
    The token expires after the given number of days (default 7).
    Returns the token record.
    """
    token = secrets.token_urlsafe(32)
    expira_en = (datetime.now() + timedelta(days=7)).isoformat()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO tokens_descarga (token, documento_id, expira_en)
            VALUES (?, ?, ?)
            """,
            (token, document_id, expira_en)
        )
    logger.info("Download token created documento_id=%s expira_en=%s", document_id, expira_en)
    return {"token": token, "expira_en": expira_en}


def get_document_by_token(token: str) -> dict | None:
    """
    Validates a token and returns the associated document, or None if
    the token is invalid or expired.
    Also records the access time on first use.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT t.token, t.expira_en, t.usado_en, d.*
            FROM tokens_descarga t
            JOIN documentos d ON d.id = t.documento_id
            WHERE t.token = ?
            AND t.expira_en > datetime('now')
            AND d.eliminado_en IS NULL
            """,
            (token,)
        )
        row = cursor.fetchone()
        if not row:
            logger.warning("Invalid or expired token token=%s", token)
            return None
        if not row["usado_en"]:
            conn.execute(
                "UPDATE tokens_descarga SET usado_en = datetime('now') WHERE token = ?",
                (token,)
            )
        return dict(row)
