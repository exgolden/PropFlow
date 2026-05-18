"""
Controller para la gestión de contratos.
Maneja creación, consulta, actualización, terminación y eliminación de contratos,
así como la sincronización del estado de la unidad asociada.
"""
from db.init import get_db
from src.controllers.unidades import get_unit
from src.controllers.unidades import get_unit
from src.controllers.inquilinos import get_tenant
from src.logger import get_logger

logger = get_logger()


def get_all_contracts() -> list[dict]:
    """
    Returns all contracts that have not been soft deleted.
    """
    logger.debug("Fetching all contracts")
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM contratos WHERE eliminado_en IS NULL ORDER BY id"
        )
        return [dict(row) for row in cursor.fetchall()]


def get_contract(contract_id: int) -> dict | None:
    """
    Returns a single contract by ID, or None if not found or deleted.
    """
    logger.debug("Fetching contract contract_id=%s", contract_id)
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM contratos WHERE id = ? AND eliminado_en IS NULL",
            (contract_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_active_contract_by_unit(unit_id: int) -> dict | None:
    """
    Returns the active contract for a given unit, or None if there isn't one.
    """
    logger.debug("Fetching active contract for unit_id=%s", unit_id)
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM contratos
            WHERE unidad_id = ? AND estado = 'activo' AND eliminado_en IS NULL
            """,
            (unit_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_contract(data: dict) -> dict:
    """
    Creates a new contract and updates the unit status to 'ocupada'.
    Raises ValueError if required fields are missing, unit is not available,
    or inquilino does not exist.
    """
    required_fields = ["unidad_id", "inquilino_id", "fecha_inicio", "fecha_fin", "renta_mensual"]
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"El campo '{field}' es requerido")
    dia_cobro = int(data.get("dia_cobro", 1))
    if not (1 <= dia_cobro <= 28):
        raise ValueError("El campo 'dia_cobro' debe ser un valor entre 1 y 28")
    unit = get_unit(data["unidad_id"])
    if not unit:
        logger.warning("Unit not found unidad_id=%s", data["unidad_id"])
        raise ValueError("La unidad no existe")
    if unit["estado"] != "disponible":
        logger.warning("Unit not available unidad_id=%s estado=%s", data["unidad_id"], unit["estado"])
        raise ValueError(f"La unidad no está disponible — estado actual: {unit['estado']}")
    tenant = get_tenant(data["inquilino_id"])
    if not tenant:
        logger.warning("Tenant not found inquilino_id=%s", data["inquilino_id"])
        raise ValueError("El inquilino no existe")
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO contratos (unidad_id, inquilino_id, fecha_inicio, fecha_fin,
                                renta_mensual, deposito, dia_cobro)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["unidad_id"],
                data["inquilino_id"],
                data["fecha_inicio"],
                data["fecha_fin"],
                data["renta_mensual"],
                data.get("deposito", 0),
                dia_cobro,
            )
        )
        contract_id = cursor.lastrowid
        conn.execute(
            "UPDATE unidades SET estado = 'ocupada' WHERE id = ?",
            (data["unidad_id"],)
        )
    logger.info("Contract created contract_id=%s unidad_id=%s inquilino_id=%s", contract_id, data["unidad_id"], data["inquilino_id"])
    return get_contract(contract_id)


def update_contract(contract_id: int, data: dict) -> dict | None:
    """
    Updates an existing contract. Only updates fields that are provided.
    Returns the updated contract, or None if not found.
    """
    contract = get_contract(contract_id)
    if not contract:
        logger.warning("Contract not found contract_id=%s", contract_id)
        return None
    if "dia_cobro" in data:
        dia_cobro = int(data["dia_cobro"])
        if not (1 <= dia_cobro <= 28):
            raise ValueError("El campo 'dia_cobro' debe ser un valor entre 1 y 28")
    allowed_fields = ["fecha_fin", "renta_mensual", "deposito", "dia_cobro"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return contract
    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [contract_id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE contratos SET {columns} WHERE id = ? AND eliminado_en IS NULL", # nosec B608
            values 
        )
    logger.info("Contract updated contract_id=%s fields=%s", contract_id, list(updates.keys()))
    return get_contract(contract_id)


def terminate_contract(contract_id: int) -> dict | None:
    """
    Terminates a contract by setting its estado to 'terminado'
    and updates the unit status back to 'disponible'.
    Returns the updated contract, or None if not found.
    """
    contract = get_contract(contract_id)
    if not contract:
        logger.warning("Contract not found for termination contract_id=%s", contract_id)
        return None
    if contract["estado"] != "activo":
        logger.warning("Contract not active contract_id=%s estado=%s", contract_id, contract["estado"])
        raise ValueError(f"El contrato no está activo — estado actual: {contract['estado']}")
    with get_db() as conn:
        conn.execute(
            "UPDATE contratos SET estado = 'terminado' WHERE id = ?",
            (contract_id,)
        )
        conn.execute(
            "UPDATE unidades SET estado = 'disponible' WHERE id = ?",
            (contract["unidad_id"],)
        )
    logger.info("Contract terminated contract_id=%s unidad_id=%s", contract_id, contract["unidad_id"])
    return get_contract(contract_id)


def delete_contract(contract_id: int) -> bool:
    """
    Soft deletes a contract by setting eliminado_en to the current timestamp.
    Only allowed if the contract is not active — terminate it first.
    Returns True if deleted, False if not found.
    """
    contract = get_contract(contract_id)
    if not contract:
        logger.warning("Contract not found for deletion contract_id=%s", contract_id)
        return False
    if contract["estado"] == "activo":
        logger.warning("Attempted to delete active contract contract_id=%s", contract_id)
        raise ValueError("No se puede eliminar un contrato activo — termínalo primero")
    with get_db() as conn:
        conn.execute(
            "UPDATE contratos SET eliminado_en = datetime('now') WHERE id = ?",
            (contract_id,)
        )
    logger.info("Contract soft deleted contract_id=%s", contract_id)
    return True
