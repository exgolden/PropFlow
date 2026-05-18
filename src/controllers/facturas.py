"""
Controller para la gestión de facturas.
Maneja consulta, generación automática, registro de pago y eliminación de facturas.
La generación de facturas es invocada por el scheduler en el día de cobro del contrato.
"""
from datetime import datetime, date
from db.init import get_db
from src.logger import get_logger

logger = get_logger()


def get_all_invoices() -> list[dict]:
    """
    Returns all invoices that have not been soft deleted.
    """
    logger.debug("Fetching all invoices")
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM facturas WHERE eliminado_en IS NULL ORDER BY id"
        )
        return [dict(row) for row in cursor.fetchall()]


def get_invoice(invoice_id: int) -> dict | None:
    """
    Returns a single invoice by ID, or None if not found or deleted.
    """
    logger.debug("Fetching invoice invoice_id=%s", invoice_id)
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM facturas WHERE id = ? AND eliminado_en IS NULL",
            (invoice_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_invoices_by_contract(contract_id: int) -> list[dict]:
    """
    Returns all invoices for a given contract.
    """
    logger.debug("Fetching invoices for contract_id=%s", contract_id)
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM facturas
            WHERE contrato_id = ? AND eliminado_en IS NULL
            ORDER BY fecha_emision DESC
            """,
            (contract_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def get_overdue_invoices() -> list[dict]:
    """
    Returns all unpaid invoices whose due date has passed.
    """
    logger.debug("Fetching overdue invoices")
    today = date.today().isoformat()
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM facturas
            WHERE pagado_en IS NULL
            AND fecha_vencimiento <= ?
            AND eliminado_en IS NULL
            ORDER BY fecha_vencimiento ASC
            """,
            (today,)
        )
        return [dict(row) for row in cursor.fetchall()]


def generate_invoice(contract: dict) -> dict | None:
    """
    Generates a monthly invoice for a given contract.
    Called automatically by the scheduler on dia_cobro.
    Skips generation if an invoice already exists for the current period.
    """
    today = date.today()
    period_start = today.replace(day=1).isoformat()
    period_end = today.replace(day=28).isoformat()
    with get_db() as conn:
        existing = conn.execute(
            """
            SELECT id FROM facturas
            WHERE contrato_id = ? AND periodo_inicio = ? AND eliminado_en IS NULL
            """,
            (contract["id"], period_start)
        ).fetchone()
        if existing:
            logger.warning("Invoice already exists for contrato_id=%s period=%s — skipped", contract["id"], period_start)
            return None
        cursor = conn.execute(
            """
            INSERT INTO facturas (contrato_id, fecha_emision, fecha_vencimiento,
                                  periodo_inicio, periodo_fin, monto)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                contract["id"],
                today.isoformat(),
                today.replace(day=contract["dia_cobro"]).isoformat(),
                period_start,
                period_end,
                contract["renta_mensual"],
            )
        )
        invoice_id = cursor.lastrowid
    logger.info("Invoice generated invoice_id=%s contrato_id=%s monto=%s periodo=%s", invoice_id, contract["id"], contract["renta_mensual"], period_start)
    return get_invoice(invoice_id)


def update_invoice(invoice_id: int, data: dict) -> dict | None:
    """
    Updates an invoice. Handles payment by setting pagado_en to now
    when metodo_pago is provided. Returns the updated invoice or None if not found.
    Raises ValueError if trying to modify an already paid invoice.
    """
    invoice = get_invoice(invoice_id)
    if not invoice:
        logger.warning("Invoice not found invoice_id=%s", invoice_id)
        return None
    if invoice["pagado_en"]:
        logger.warning("Attempted to modify already paid invoice invoice_id=%s", invoice_id)
        raise ValueError("No se puede modificar una factura ya pagada")
    allowed_fields = ["metodo_pago", "referencia_pago"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return invoice
    if "metodo_pago" in updates:
        updates["pagado_en"] = datetime.now().isoformat()
    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [invoice_id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE facturas SET {columns} WHERE id = ? AND eliminado_en IS NULL", # nosec B608
            values
        )
    logger.info("Invoice updated invoice_id=%s metodo_pago=%s pagado_en=%s", invoice_id, data.get("metodo_pago"), updates.get("pagado_en"))
    return get_invoice(invoice_id)


def delete_invoice(invoice_id: int) -> bool:
    """
    Soft deletes an invoice. Not allowed if the invoice has been paid.
    Returns True if deleted, False if not found.
    """
    invoice = get_invoice(invoice_id)
    if not invoice:
        logger.warning("Invoice not found for deletion invoice_id=%s", invoice_id)
        return False
    if invoice["pagado_en"]:
        logger.warning("Attempted to delete paid invoice invoice_id=%s", invoice_id)
        raise ValueError("No se puede eliminar una factura ya pagada")
    with get_db() as conn:
        conn.execute(
            "UPDATE facturas SET eliminado_en = datetime('now') WHERE id = ?",
            (invoice_id,)
        )
    logger.info("Invoice soft deleted invoice_id=%s", invoice_id)
    return True
