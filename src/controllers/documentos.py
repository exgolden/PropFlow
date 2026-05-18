"""
Controller para la gestión de documentos.
Maneja creación, consulta, actualización y eliminación de documentos
asociados a unidades, contratos o inquilinos.
"""
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
    logger.debug("Fetching all documents unidad_id=%s contrato_id=%s inquilino_id=%s tipo=%s", unidad_id, contrato_id, inquilino_id, tipo)
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


def get_document(document_id: int) -> dict | None:
    """
    Returns a single document by ID, or None if not found or deleted.
    """
    logger.debug("Fetching document document_id=%s", document_id)
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM documentos WHERE id = ? AND eliminado_en IS NULL",
            (document_id,)
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
        if not all([data.get("unidad_id"), data.get("contrato_id"), data.get("inquilino_id")]):
            logger.warning("Document creation failed — missing FK")
            raise ValueError("El documento debe estar asociado a una unidad, contrato e inquilino")
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
    logger.info("Document created document_id=%s nombre=%s subido_por=%s", document_id, data["nombre"], data["subido_por"])
    return get_document(document_id)


def update_document(document_id: int, data: dict) -> dict | None:
    """
    Updates an existing document. Only nombre, tipo, url_archivo
    and vence_en are updatable after creation.
    Returns the updated document, or None if not found.
    """
    document = get_document(document_id)
    if not document:
        logger.warning("Document not found document_id=%s", document_id)
        return None
    allowed_fields = ["nombre", "tipo", "url_archivo", "vence_en"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return document
    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [document_id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE documentos SET {columns} WHERE id = ? AND eliminado_en IS NULL", # nosec B608
            values
        )
    logger.info("Document updated document_id=%s fields=%s", document_id, list(updates.keys()))
    return get_document(document_id)


def delete_document(document_id: int) -> bool:
    """
    Soft deletes a document by setting eliminado_en to the current timestamp.
    Returns True if deleted, False if not found.
    """
    if not get_document(document_id):
        logger.warning("Document not found for deletion document_id=%s", document_id)
        return False
    with get_db() as conn:
        conn.execute(
            "UPDATE documentos SET eliminado_en = datetime('now') WHERE id = ?",
            (document_id,)
        )
    logger.info("Document soft deleted document_id=%s", document_id)
    return True


def get_expiring_documents(days: int = 30) -> list[dict]:
    """
    Returns all documents expiring within the given number of days.
    Useful for sending reminders before documents lapse.
    """
    logger.debug("Fetching documents expiring within %s days", days)
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
