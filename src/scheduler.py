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
    logger.info(f"Scheduler running — checking invoices for day {today.day}")
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
        logger.info(f"Scheduler found {len(contracts)} contracts due today")
    for contract in contracts:
        invoice = generate_invoice(contract)
        if invoice:
            logger.info(f"Invoice generated contrato_id={contract['id']} factura_id={invoice['id']}")
        else:
            logger.warning(f"Invoice already exists for contrato_id={contract['id']} — skipped")


def start_scheduler() -> None:
    """
    Starts the background scheduler.
    Registered in create_app() so it starts with the Flask app.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        generate_monthly_invoices,
        trigger="cron",
        hour=0,
        minute=5,
    )
    scheduler.start()
    logger.info("Scheduler started")