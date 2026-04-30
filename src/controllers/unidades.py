# src/controllers/unidades.py
from db.init import get_db
from src.logger import get_logger

logger = get_logger()


def get_all_units() -> list[dict]:
    """
    Returns all units that have not been soft deleted.
    """
    logger.debug("Fetching all units")
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM unidades WHERE eliminado_en IS NULL ORDER BY id"
        )
        return [dict(row) for row in cursor.fetchall()]


def get_unit(id: int) -> dict | None:
    """
    Returns a single unit by ID, or None if not found or deleted.
    """
    logger.debug(f"Fetching unit id={id}")
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM unidades WHERE id = ? AND eliminado_en IS NULL",
            (id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_unit(data: dict) -> dict:
    """
    Creates a new unit. Returns the created unit.
    Raises ValueError if required fields are missing.
    """
    required_fields = ["numero", "area_m2", "tipo", "renta_base"]
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"El campo '{field}' es requerido")
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO unidades (numero, area_m2, tipo, renta_base)
            VALUES (?, ?, ?, ?)
            """,
            (
                data["numero"],
                data["area_m2"],
                data["tipo"],
                data["renta_base"],
            )
        )
        unit_id = cursor.lastrowid
    logger.info(f"Unit created id={unit_id} numero={data['numero']}")
    return get_unit(unit_id)


def update_unit(id: int, data: dict) -> dict | None:
    """
    Updates an existing unit. Only updates fields that are provided.
    Returns the updated unit, or None if not found.
    """
    unit = get_unit(id)
    if not unit:
        logger.warning(f"Unit not found id={id}")
        return None
    allowed_fields = ["numero", "area_m2", "tipo", "renta_base", "estado"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return unit
    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE unidades SET {columns} WHERE id = ? AND eliminado_en IS NULL",
            values
        )
    logger.info(f"Unit updated id={id} fields={list(updates.keys())}")
    return get_unit(id)


def delete_unit(id: int) -> bool:
    """
    Soft deletes a unit by setting eliminado_en to the current timestamp.
    Returns True if deleted, False if not found.
    """
    if not get_unit(id):
        logger.warning(f"Unit not found for deletion id={id}")
        return False
    with get_db() as conn:
        conn.execute(
            "UPDATE unidades SET eliminado_en = datetime('now') WHERE id = ?",
            (id,)
        )
    logger.info(f"Unit soft deleted id={id}")
    return True