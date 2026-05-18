"""
Controller para la gestión de inquilinos.
Maneja creación, consulta, actualización y eliminación de inquilinos.
"""
import re
from db.init import get_db
from src.logger import get_logger

logger = get_logger()

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_tenant_fields(data: dict) -> None:
    """
    Validates correo, telefono and rfc formats.
    Raises ValueError if any field is invalid.
    """
    if "correo" in data and data["correo"]:
        if not _EMAIL_RE.match(data["correo"]):
            raise ValueError("El campo 'correo' no tiene un formato válido")
    if "telefono" in data and data["telefono"]:
        if not str(data["telefono"]).isdigit() or len(str(data["telefono"])) != 10:
            raise ValueError("El campo 'telefono' debe tener exactamente 10 dígitos")
    if "rfc" in data and data["rfc"]:
        if len(str(data["rfc"])) not in (12, 13):
            raise ValueError("El campo 'rfc' debe tener 12 o 13 caracteres")


def get_all_tenants() -> list[dict]:
    """
    Returns all tenants that have not been soft deleted.
    """
    logger.debug("Fetching all tenants")
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM inquilinos WHERE eliminado_en IS NULL ORDER BY id"
        )
        return [dict(row) for row in cursor.fetchall()]


def get_tenant(tenant_id: int) -> dict | None:
    """
    Returns a single tenant by ID, or None if not found or deleted.
    """
    logger.debug("Fetching tenant tenant_id=%s", tenant_id)
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM inquilinos WHERE id = ? AND eliminado_en IS NULL",
            (tenant_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_tenant(data: dict) -> dict:
    """
    Creates a new tenant. Returns the created tenant.
    Raises ValueError if required fields are missing or field formats are invalid.
    """
    required_fields = ["empresa", "nombre_contacto", "correo"]
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"El campo '{field}' es requerido")
    _validate_tenant_fields(data)
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO inquilinos (empresa, nombre_contacto, correo, telefono, rfc)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["empresa"],
                data["nombre_contacto"],
                data["correo"],
                data.get("telefono"),
                data.get("rfc"),
            )
        )
        tenant_id = cursor.lastrowid
    logger.info("Tenant created tenant_id=%s empresa=%s correo=%s", tenant_id, data["empresa"], data["correo"])
    return get_tenant(tenant_id)


def update_tenant(tenant_id: int, data: dict) -> dict | None:
    """
    Updates an existing tenant. Only updates fields that are provided.
    Raises ValueError if field formats are invalid.
    Returns the updated tenant, or None if not found.
    """
    tenant = get_tenant(tenant_id)
    if not tenant:
        logger.warning("Tenant not found tenant_id=%s", tenant_id)
        return None
    _validate_tenant_fields(data)
    allowed_fields = ["empresa", "nombre_contacto", "correo", "telefono", "rfc"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return tenant
    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [tenant_id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE inquilinos SET {columns} WHERE id = ? AND eliminado_en IS NULL", # nosec B608
            values
        )
    logger.info("Tenant updated tenant_id=%s fields=%s", tenant_id, list(updates.keys()))
    return get_tenant(tenant_id)


def delete_tenant(tenant_id: int) -> bool:
    """
    Soft deletes a tenant by setting eliminado_en to the current timestamp.
    Returns True if deleted, False if not found.
    """
    if not get_tenant(tenant_id):
        logger.warning("Tenant not found for deletion tenant_id=%s", tenant_id)
        return False
    with get_db() as conn:
        conn.execute(
            "UPDATE inquilinos SET eliminado_en = datetime('now') WHERE id = ?",
            (tenant_id,)
        )
    logger.info("Tenant soft deleted tenant_id=%s", tenant_id)
    return True
