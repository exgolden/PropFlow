# src/controllers/inquilinos.py
from db.init import get_db
from src.logger import get_logger

logger = get_logger()


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


def get_tenant(id: int) -> dict | None:
    """
    Returns a single tenant by ID, or None if not found or deleted.
    """
    logger.debug(f"Fetching tenant id={id}")
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM inquilinos WHERE id = ? AND eliminado_en IS NULL",
            (id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_tenant(data: dict) -> dict:
    """
    Creates a new tenant. Returns the created tenant.
    Raises ValueError if required fields are missing.
    """
    required_fields = ["empresa", "nombre_contacto", "correo"]
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"El campo '{field}' es requerido")
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
    logger.info(f"Tenant created id={tenant_id} empresa={data['empresa']} correo={data['correo']}")
    return get_tenant(tenant_id)


def update_tenant(id: int, data: dict) -> dict | None:
    """
    Updates an existing tenant. Only updates fields that are provided.
    Returns the updated tenant, or None if not found.
    """
    tenant = get_tenant(id)
    if not tenant:
        logger.warning(f"Tenant not found id={id}")
        return None
    allowed_fields = ["empresa", "nombre_contacto", "correo", "telefono", "rfc"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return tenant
    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE inquilinos SET {columns} WHERE id = ? AND eliminado_en IS NULL",
            values
        )
    logger.info(f"Tenant updated id={id} fields={list(updates.keys())}")
    return get_tenant(id)


def delete_tenant(id: int) -> bool:
    """
    Soft deletes a tenant by setting eliminado_en to the current timestamp.
    Returns True if deleted, False if not found.
    """
    if not get_tenant(id):
        logger.warning(f"Tenant not found for deletion id={id}")
        return False
    with get_db() as conn:
        conn.execute(
            "UPDATE inquilinos SET eliminado_en = datetime('now') WHERE id = ?",
            (id,)
        )
    logger.info(f"Tenant soft deleted id={id}")
    return True