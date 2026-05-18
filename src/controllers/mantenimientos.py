# src/controllers/mantenimientos.py
"""
Controller para la gestión de mantenimientos.
Maneja creación, consulta, actualización y eliminación de solicitudes de mantenimiento,
así como la sincronización del estado de la unidad asociada.
"""
from datetime import date
from db.init import get_db
from src.controllers.unidades import get_unit
from src.logger import get_logger

logger = get_logger()


def _append_journal(existing: str | None, entry: str) -> str:
    """
    Appends a dated entry to the journal text.
    Format: DD/MM/YY — entry
    """
    today = date.today().strftime("%d/%m/%y")
    new_line = f"{today} — {entry}"
    if existing:
        return f"{existing}\n{new_line}"
    return new_line


def _get_active_contract_id(unidad_id: int, conn) -> int | None:
    """
    Returns the active contract ID for a given unit, or None if there isn't one.
    """
    cursor = conn.execute(
        """
        SELECT id FROM contratos
        WHERE unidad_id = ? AND estado = 'activo' AND eliminado_en IS NULL
        """,
        (unidad_id,)
    )
    row = cursor.fetchone()
    return row["id"] if row else None


def get_all_maintenance(
    unidad_id: int | None = None,
    estado: str | None = None,
    prioridad: str | None = None,
) -> list[dict]:
    """
    Returns all maintenance requests that have not been soft deleted.
    Optionally filters by unidad_id, estado, or prioridad.
    """
    logger.debug("Fetching all maintenance unidad_id=%s estado=%s prioridad=%s", unidad_id, estado, prioridad)
    query = "SELECT * FROM mantenimientos WHERE eliminado_en IS NULL"
    params = []
    if unidad_id:
        query += " AND unidad_id = ?"
        params.append(unidad_id)
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    query += " ORDER BY id"
    with get_db() as conn:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_maintenance(maintenance_id: int) -> dict | None:
    """
    Returns a single maintenance request by ID, or None if not found or deleted.
    """
    logger.debug("Fetching maintenance maintenance_id=%s", maintenance_id)
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM mantenimientos WHERE id = ? AND eliminado_en IS NULL",
            (maintenance_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_maintenance(data: dict) -> dict:
    """
    Creates a new maintenance request.
    Captures the active contract on the unit at creation time.
    If descripcion is provided, it is stored as the first journal entry with today's date.
    If the unit is disponible, updates its estado to mantenimiento.
    Raises ValueError if required fields are missing or unit does not exist.
    """
    required_fields = ["unidad_id", "titulo", "prioridad"]
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"El campo '{field}' es requerido")
    unit = get_unit(data["unidad_id"])
    if not unit:
        logger.warning("Unit not found unidad_id=%s", data["unidad_id"])
        raise ValueError("La unidad no existe")
    descripcion = None
    if data.get("descripcion"):
        descripcion = _append_journal(None, data["descripcion"])
    with get_db() as conn:
        contrato_id = _get_active_contract_id(data["unidad_id"], conn)
        cursor = conn.execute(
            """
            INSERT INTO mantenimientos (unidad_id, contrato_id, titulo, descripcion,
                                        prioridad, costo, fecha_programada)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["unidad_id"],
                contrato_id,
                data["titulo"],
                descripcion,
                data["prioridad"],
                data.get("costo"),
                data.get("fecha_programada"),
            )
        )
        maintenance_id = cursor.lastrowid
        if unit["estado"] == "disponible":
            conn.execute(
                "UPDATE unidades SET estado = 'mantenimiento' WHERE id = ?",
                (data["unidad_id"],)
            )
            logger.info("Unit estado updated to mantenimiento unidad_id=%s", data["unidad_id"])
    logger.info("Maintenance created maintenance_id=%s unidad_id=%s contrato_id=%s prioridad=%s", maintenance_id, data["unidad_id"], contrato_id, data["prioridad"])
    return get_maintenance(maintenance_id)


def update_maintenance(maintenance_id: int, data: dict) -> dict | None:
    """
    Updates an existing maintenance request. Only updates fields that are provided.
    If descripcion is provided, it is appended as a new dated journal entry.
    If estado is set to resuelto, sets fecha_resolucion to today and
    restores the unit estado to disponible if it was in mantenimiento.
    Returns the updated request, or None if not found.
    """
    maintenance = get_maintenance(maintenance_id)
    if not maintenance:
        logger.warning("Maintenance not found maintenance_id=%s", maintenance_id)
        return None
    allowed_fields = ["titulo", "prioridad", "costo", "estado",
                      "fecha_programada", "fecha_resolucion"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if data.get("descripcion"):
        updates["descripcion"] = _append_journal(
            maintenance["descripcion"], data["descripcion"]
        )
    if not updates:
        return maintenance
    if updates.get("estado") == "resuelto" and not updates.get("fecha_resolucion"):
        updates["fecha_resolucion"] = date.today().isoformat()
    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [maintenance_id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE mantenimientos SET {columns} WHERE id = ? AND eliminado_en IS NULL", # nosec B608
            values
        )
        if updates.get("estado") == "resuelto":
            unit = get_unit(maintenance["unidad_id"])
            if unit and unit["estado"] == "mantenimiento":
                conn.execute(
                    "UPDATE unidades SET estado = 'disponible' WHERE id = ?",
                    (maintenance["unidad_id"],)
                )
                logger.info("Unit estado restored to disponible unidad_id=%s", maintenance["unidad_id"])
    logger.info("Maintenance updated maintenance_id=%s fields=%s", maintenance_id, list(updates.keys()))
    return get_maintenance(maintenance_id)


def delete_maintenance(maintenance_id: int) -> bool:
    """
    Soft deletes a maintenance request.
    Not allowed if the request is still open or in progress.
    Returns True if deleted, False if not found.
    """
    maintenance = get_maintenance(maintenance_id)
    if not maintenance:
        logger.warning("Maintenance not found for deletion maintenance_id=%s", maintenance_id)
        return False
    if maintenance["estado"] != "resuelto":
        logger.warning("Attempted to delete unresolved maintenance maintenance_id=%s estado=%s", maintenance_id, maintenance["estado"])
        raise ValueError("No se puede eliminar un mantenimiento que no ha sido resuelto")
    with get_db() as conn:
        conn.execute(
            "UPDATE mantenimientos SET eliminado_en = datetime('now') WHERE id = ?",
            (maintenance_id,)
        )
    logger.info("Maintenance soft deleted maintenance_id=%s", maintenance_id)
    return True
