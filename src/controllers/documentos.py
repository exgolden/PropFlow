# src/controllers/documentos.py
from db.init import get_db
from src.logger import get_logger

logger = get_logger()


def get_all_documents(
    unidad_id: int | None = None,
    contrato_id: int | None = None,
    inquilino_id: int | None = None,
    tipo: str | None = None,
) -> list[dict]:
    """
    Returns all documents that have not been soft deleted.
    Optionally filters by unidad_id, contrato_id, inquilino_id or tipo.
    """
    logger.debug(f"Fetching all documents unidad_id={unidad_id} contrato_id={contrato_id} inquilino_id={inquilino_id} tipo={tipo}")
    query = "SELECT * FROM documentos WHERE eliminado_en IS NULL"
    params = []
    if unidad_id:
        query += " AND unidad_id = ?"
        params.append(unidad_id)
    if contrato_id:
        query += " AND contrato_id = ?"
        params.append(contrato_id)
    if inquilino_id:
        query += " AND inquilino_id = ?"
        params.append(inquilino_id)
    if tipo:
        query += " AND tipo = ?"
        params.append(tipo)
    query += " ORDER BY id"
    with get_db() as conn:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_document(id: int) -> dict | None:
    """
    Returns a single document by ID, or None if not found or deleted.
    """
    logger.debug(f"Fetching document id={id}")
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM documentos WHERE id = ? AND eliminado_en IS NULL",
            (id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_document(data: dict) -> dict:
    """
    Creates a new document.
    Requires at least one FK (unidad_id, contrato_id or inquilino_id)
    and subido_por to track who uploaded it.
    Raises ValueError if required fields are missing.
    """
    required_fields = ["subido_por", "nombre", "tipo", "url_archivo"]
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"El campo '{field}' es requerido")
    if not any([data.get("unidad_id"), data.get("contrato_id"), data.get("inquilino_id")]):
        logger.warning("Document creation failed — no FK provided")
        raise ValueError("El documento debe estar asociado a una unidad, contrato o inquilino")
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO documentos (unidad_id, contrato_id, inquilino_id,
                                    subido_por, nombre, tipo, url_archivo, vence_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("unidad_id"),
                data.get("contrato_id"),
                data.get("inquilino_id"),
                data["subido_por"],
                data["nombre"],
                data["tipo"],
                data["url_archivo"],
                data.get("vence_en"),
            )
        )
        document_id = cursor.lastrowid
    logger.info(f"Document created id={document_id} nombre={data['nombre']} subido_por={data['subido_por']}")
    return get_document(document_id)


def update_document(id: int, data: dict) -> dict | None:
    """
    Updates an existing document. Only nombre, tipo, url_archivo
    and vence_en are updatable after creation.
    Returns the updated document, or None if not found.
    """
    document = get_document(id)
    if not document:
        logger.warning(f"Document not found id={id}")
        return None
    allowed_fields = ["nombre", "tipo", "url_archivo", "vence_en"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return document
    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE documentos SET {columns} WHERE id = ? AND eliminado_en IS NULL",
            values
        )
    logger.info(f"Document updated id={id} fields={list(updates.keys())}")
    return get_document(id)


def delete_document(id: int) -> bool:
    """
    Soft deletes a document by setting eliminado_en to the current timestamp.
    Returns True if deleted, False if not found.
    """
    if not get_document(id):
        logger.warning(f"Document not found for deletion id={id}")
        return False
    with get_db() as conn:
        conn.execute(
            "UPDATE documentos SET eliminado_en = datetime('now') WHERE id = ?",
            (id,)
        )
    logger.info(f"Document soft deleted id={id}")
    return True


def get_expiring_documents(days: int = 30) -> list[dict]:
    """
    Returns all documents expiring within the given number of days.
    Useful for sending reminders before documents lapse.
    """
    logger.debug(f"Fetching documents expiring within {days} days")
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM documentos
            WHERE vence_en IS NOT NULL
            AND eliminado_en IS NULL
            AND vence_en <= date('now', ? || ' days')
            AND vence_en >= date('now')
            ORDER BY vence_en ASC
            """,
            (str(days),)
        )
        return [dict(row) for row in cursor.fetchall()]