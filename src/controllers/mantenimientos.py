# src/controllers/mantenimientos.py
from datetime import date
from db.init import get_db
from src.controllers.unidades import get_unit
from src.logger import get_logger

logger = get_logger()


def get_all_maintenance(
    unidad_id: int | None = None,
    estado: str | None = None,
    prioridad: str | None = None,
) -> list[dict]:
    """
    Returns all maintenance requests that have not been soft deleted.
    Optionally filters by unidad_id, estado, or prioridad.
    """
    logger.debug(f"Fetching all maintenance unidad_id={unidad_id} estado={estado} prioridad={prioridad}")
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


def get_maintenance(id: int) -> dict | None:
    """
    Returns a single maintenance request by ID, or None if not found or deleted.
    """
    logger.debug(f"Fetching maintenance id={id}")
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM mantenimientos WHERE id = ? AND eliminado_en IS NULL",
            (id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_maintenance(data: dict) -> dict:
    """
    Creates a new maintenance request.
    If the unit is disponible, updates its estado to mantenimiento.
    Raises ValueError if required fields are missing or unit does not exist.
    """
    required_fields = ["unidad_id", "titulo", "prioridad"]
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"El campo '{field}' es requerido")
    unit = get_unit(data["unidad_id"])
    if not unit:
        logger.warning(f"Unit not found unidad_id={data['unidad_id']}")
        raise ValueError("La unidad no existe")
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO mantenimientos (unidad_id, titulo, descripcion,
                                        prioridad, costo, fecha_programada)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data["unidad_id"],
                data["titulo"],
                data.get("descripcion"),
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
            logger.info(f"Unit estado updated to mantenimiento unidad_id={data['unidad_id']}")
    logger.info(f"Maintenance created id={maintenance_id} unidad_id={data['unidad_id']} prioridad={data['prioridad']}")
    return get_maintenance(maintenance_id)


def update_maintenance(id: int, data: dict) -> dict | None:
    """
    Updates an existing maintenance request. Only updates fields that are provided.
    If estado is set to resuelto, sets fecha_resolucion to today and
    restores the unit estado to disponible if it was in mantenimiento.
    Returns the updated request, or None if not found.
    """
    maintenance = get_maintenance(id)
    if not maintenance:
        logger.warning(f"Maintenance not found id={id}")
        return None
    allowed_fields = ["titulo", "descripcion", "prioridad", "costo",
                      "estado", "fecha_programada", "fecha_resolucion"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return maintenance
    if updates.get("estado") == "resuelto" and not updates.get("fecha_resolucion"):
        updates["fecha_resolucion"] = date.today().isoformat()
    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE mantenimientos SET {columns} WHERE id = ? AND eliminado_en IS NULL",
            values
        )
        if updates.get("estado") == "resuelto":
            unit = get_unit(maintenance["unidad_id"])
            if unit and unit["estado"] == "mantenimiento":
                conn.execute(
                    "UPDATE unidades SET estado = 'disponible' WHERE id = ?",
                    (maintenance["unidad_id"],)
                )
                logger.info(f"Unit estado restored to disponible unidad_id={maintenance['unidad_id']}")
    logger.info(f"Maintenance updated id={id} fields={list(updates.keys())}")
    return get_maintenance(id)


def delete_maintenance(id: int) -> bool:
    """
    Soft deletes a maintenance request.
    Not allowed if the request is still open or in progress.
    Returns True if deleted, False if not found.
    """
    maintenance = get_maintenance(id)
    if not maintenance:
        logger.warning(f"Maintenance not found for deletion id={id}")
        return False
    if maintenance["estado"] != "resuelto":
        logger.warning(f"Attempted to delete unresolved maintenance id={id} estado={maintenance['estado']}")
        raise ValueError("No se puede eliminar un mantenimiento que no ha sido resuelto")
    with get_db() as conn:
        conn.execute(
            "UPDATE mantenimientos SET eliminado_en = datetime('now') WHERE id = ?",
            (id,)
        )
    logger.info(f"Maintenance soft deleted id={id}")
    return True