# src/controllers/contratos.py
from db.init import get_db
from src.controllers.unidades import get_unit
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


def get_contract(id: int) -> dict | None:
    """
    Returns a single contract by ID, or None if not found or deleted.
    """
    logger.debug(f"Fetching contract id={id}")
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM contratos WHERE id = ? AND eliminado_en IS NULL",
            (id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_active_contract_by_unit(unit_id: int) -> dict | None:
    """
    Returns the active contract for a given unit, or None if there isn't one.
    """
    logger.debug(f"Fetching active contract for unit_id={unit_id}")
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
    Raises ValueError if required fields are missing or unit is not available.
    """
    required_fields = ["unidad_id", "inquilino_id", "fecha_inicio", "fecha_fin", "renta_mensual"]
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"El campo '{field}' es requerido")
    unit = get_unit(data["unidad_id"])
    if not unit:
        logger.warning(f"Unit not found unidad_id={data['unidad_id']}")
        raise ValueError("La unidad no existe")
    if unit["estado"] != "disponible":
        logger.warning(f"Unit not available unidad_id={data['unidad_id']} estado={unit['estado']}")
        raise ValueError(f"La unidad no está disponible — estado actual: {unit['estado']}")
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
                data.get("dia_cobro", 1),
            )
        )
        contract_id = cursor.lastrowid
        conn.execute(
            "UPDATE unidades SET estado = 'ocupada' WHERE id = ?",
            (data["unidad_id"],)
        )
    logger.info(f"Contract created id={contract_id} unidad_id={data['unidad_id']} inquilino_id={data['inquilino_id']}")
    return get_contract(contract_id)


def update_contract(id: int, data: dict) -> dict | None:
    """
    Updates an existing contract. Only updates fields that are provided.
    Returns the updated contract, or None if not found.
    """
    contract = get_contract(id)
    if not contract:
        logger.warning(f"Contract not found id={id}")
        return None
    allowed_fields = ["fecha_fin", "renta_mensual", "deposito", "dia_cobro"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return contract
    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE contratos SET {columns} WHERE id = ? AND eliminado_en IS NULL",
            values
        )
    logger.info(f"Contract updated id={id} fields={list(updates.keys())}")
    return get_contract(id)


def terminate_contract(id: int) -> dict | None:
    """
    Terminates a contract by setting its estado to 'terminado'
    and updates the unit status back to 'disponible'.
    Returns the updated contract, or None if not found.
    """
    contract = get_contract(id)
    if not contract:
        logger.warning(f"Contract not found for termination id={id}")
        return None
    if contract["estado"] != "activo":
        logger.warning(f"Contract not active id={id} estado={contract['estado']}")
        raise ValueError(f"El contrato no está activo — estado actual: {contract['estado']}")
    with get_db() as conn:
        conn.execute(
            "UPDATE contratos SET estado = 'terminado' WHERE id = ?",
            (id,)
        )
        conn.execute(
            "UPDATE unidades SET estado = 'disponible' WHERE id = ?",
            (contract["unidad_id"],)
        )
    logger.info(f"Contract terminated id={id} unidad_id={contract['unidad_id']}")
    return get_contract(id)


def delete_contract(id: int) -> bool:
    """
    Soft deletes a contract by setting eliminado_en to the current timestamp.
    Only allowed if the contract is not active — terminate it first.
    Returns True if deleted, False if not found.
    """
    contract = get_contract(id)
    if not contract:
        logger.warning(f"Contract not found for deletion id={id}")
        return False
    if contract["estado"] == "activo":
        logger.warning(f"Attempted to delete active contract id={id}")
        raise ValueError("No se puede eliminar un contrato activo — termínalo primero")
    with get_db() as conn:
        conn.execute(
            "UPDATE contratos SET eliminado_en = datetime('now') WHERE id = ?",
            (id,)
        )
    logger.info(f"Contract soft deleted id={id}")
    return True