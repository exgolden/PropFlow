# src/routes/dashboard.py
from flask import Blueprint, render_template, session, redirect, url_for
from src.routes.usuarios import require_auth
from src.controllers.unidades import get_all_units
from src.controllers.inquilinos import get_all_tenants
from src.controllers.contratos import get_all_contracts
from src.controllers.facturas import get_all_invoices, get_overdue_invoices
from src.controllers.mantenimientos import get_all_maintenance

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
def root():
    """
    Redirects root to dashboard if logged in, otherwise to login.
    """
    if "user_id" not in session:
        return redirect(url_for("usuarios.login"))
    return redirect(url_for("dashboard.index"))


@dashboard_bp.get("/dashboard")
@require_auth
def index():
    """
    Main dashboard — summary stats and recent records.
    """
    units = get_all_units()
    tenants = get_all_tenants()
    contracts = get_all_contracts()
    invoices = get_all_invoices()
    overdue = get_overdue_invoices()
    maintenance = get_all_maintenance()
    stats = {
        "total_units":        len(units),
        "occupied_units":     len([u for u in units if u["estado"] == "ocupada"]),
        "vacant_units":       len([u for u in units if u["estado"] == "disponible"]),
        "total_tenants":      len(tenants),
        "active_contracts":   len([c for c in contracts if c["estado"] == "activo"]),
        "pending_invoices":   len([i for i in invoices if not i["pagado_en"]]),
        "overdue_invoices":   len(overdue),
        "open_maintenance":   len([m for m in maintenance if m["estado"] == "abierto"]),
        "urgent_maintenance": len([m for m in maintenance if m["prioridad"] == "urgente" and m["estado"] != "resuelto"]),
    }
    return render_template(
        "dashboard.html",
        stats=stats,
        recent_units=units[:5],
        recent_contracts=contracts[:5],
        overdue_invoices=overdue[:5],
    )