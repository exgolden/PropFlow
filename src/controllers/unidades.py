# src/controllers/unidades.py
"""
Controller para la gestión de unidades.
Maneja creación, consulta, actualización y eliminación de unidades,
incluyendo validación de campos numéricos y generación automática de número de unidad.
"""
from db.init import get_db
from src.logger import get_logger

logger = get_logger()

_TIPO_PREFIX = {
    "oficina":      "OF",
    "local":        "LC",
    "bodega":       "BD",
    "consultorio":  "CN",
    "apartamento":  "AP",
    "casa":         "CA",
    "terreno":      "TR"
}


def _generate_numero(tipo: str, conn) -> str:
    """
    Generates the next available unit number for the given tipo.
    Format: {PREFIX}-{NNN} e.g. OF-001, LC-003.
    """
    prefix = _TIPO_PREFIX.get(tipo, "UN")
    cursor = conn.execute(
        """
        SELECT numero FROM unidades
        WHERE tipo = ? AND eliminado_en IS NULL
        ORDER BY numero DESC
        """,
        (tipo,)
    )
    rows = [row["numero"] for row in cursor.fetchall()]
    max_n = 0
    for numero in rows:
        try:
            n = int(numero.split("-")[1])
            if n > max_n:
                max_n = n
        except (IndexError, ValueError):
            pass
    return f"{prefix}-{str(max_n + 1).zfill(3)}"


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


def get_unit(unit_id: int) -> dict | None:
    """
    Returns a single unit by ID, or None if not found or deleted.
    """
    logger.debug("Fetching unit unit_id=%s", unit_id)
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM unidades WHERE id = ? AND eliminado_en IS NULL",
            (unit_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_unit(data: dict) -> dict:
    """
    Creates a new unit. Generates numero automatically from tipo.
    Returns the created unit.
    Raises ValueError if required fields are missing.
    """
    required_fields = ["area_m2", "tipo", "renta_base"]
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"El campo '{field}' es requerido")
    if float(data["area_m2"]) <= 0:
        raise ValueError("El campo 'area_m2' debe ser mayor a 0")
    if float(data["renta_base"]) <= 0:
        raise ValueError("El campo 'renta_base' debe ser mayor a 0")
    with get_db() as conn:
        numero = _generate_numero(data["tipo"], conn)
        cursor = conn.execute(
            """
            INSERT INTO unidades (numero, area_m2, tipo, renta_base)
            VALUES (?, ?, ?, ?)
            """,
            (
                numero,
                data["area_m2"],
                data["tipo"],
                data["renta_base"],
            )
        )
        unit_id = cursor.lastrowid
    logger.info("Unit created unit_id=%s numero=%s", unit_id, numero)
    return get_unit(unit_id)


def update_unit(unit_id: int, data: dict) -> dict | None:
    """
    Updates an existing unit. Only updates fields that are provided.
    Returns the updated unit, or None if not found.
    """
    unit = get_unit(unit_id)
    if not unit:
        logger.warning("Unit not found unit_id=%s", unit_id)
        return None
    if "area_m2" in data and float(data["area_m2"]) <= 0:
        raise ValueError("El campo 'area_m2' debe ser mayor a 0")
    if "renta_base" in data and float(data["renta_base"]) <= 0:
        raise ValueError("El campo 'renta_base' debe ser mayor a 0")
    allowed_fields = ["area_m2", "tipo", "renta_base", "estado"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return unit
    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [unit_id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE unidades SET {columns} WHERE id = ? AND eliminado_en IS NULL", # nosec B608
            values
        )
    logger.info("Unit updated unit_id=%s fields=%s", unit_id, list(updates.keys()))
    return get_unit(unit_id)


def delete_unit(unit_id: int) -> bool:
    """
    Soft deletes a unit by setting eliminado_en to the current timestamp.
    Returns True if deleted, False if not found.
    """
    if not get_unit(unit_id):
        logger.warning("Unit not found for deletion unit_id=%s", unit_id)
        return False
    with get_db() as conn:
        conn.execute(
            "UPDATE unidades SET eliminado_en = datetime('now') WHERE id = ?",
            (unit_id,)
        )
    logger.info("Unit soft deleted unit_id=%s", unit_id)
    return True
