# src/scheduler.py
"""
Scheduler de tareas periódicas.
Ejecuta la generación automática de facturas diariamente a las 00:05
para todos los contratos activos cuyo día de cobro coincide con el día actual.
"""
import os
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
from db.init import get_db
from src.controllers.facturas import generate_invoice
from src.logger import get_logger

logger = get_logger()


def generate_monthly_invoices() -> None:
    """
    Runs daily. Finds all active contracts whose dia_cobro matches
    today's date and generates an invoice for each one.
    """
    today = date.today()
    logger.info("Scheduler running — checking invoices for day %s", today.day)
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM contratos
            WHERE estado = 'activo'
            AND dia_cobro = ?
            AND eliminado_en IS NULL
            """,
            (today.day,)
        )
        contracts = [dict(row) for row in cursor.fetchall()]
    logger.info("Scheduler found %s contracts due today", len(contracts))
    for contract in contracts:
        invoice = generate_invoice(contract)
        if invoice:
            logger.info("Invoice generated contrato_id=%s factura_id=%s", contract["id"], invoice["id"])
        else:
            logger.warning("Invoice already exists for contrato_id=%s — skipped", contract["id"])


def start_scheduler() -> None:
    """
    Starts the background scheduler.
    Registered in create_app() so it starts with the Flask app.
    Only runs in the main Werkzeug process to avoid double-start in debug mode.
    """
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        generate_monthly_invoices,
        trigger="cron",
        hour=0,
        minute=5
    )
    scheduler.start()
    logger.info("Scheduler started")
