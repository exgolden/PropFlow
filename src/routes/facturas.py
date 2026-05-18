"""
Rutas para la gestión de facturas.
Expone endpoints REST y vistas HTML para consultar, registrar pago
y eliminar facturas. La generación de facturas es automática vía scheduler.
"""
from flask import Blueprint, request, jsonify, render_template
from datetime import date
from src.controllers.facturas import (
    get_all_invoices,
    get_invoice,
    get_invoices_by_contract,
    get_overdue_invoices,
    update_invoice,
    delete_invoice,
)
from src.routes.usuarios import require_auth, require_admin, require_auth_page

facturas_bp = Blueprint("facturas", __name__, url_prefix="/facturas")


@facturas_bp.get("/")
@require_auth
def list_invoices():
    """Returns all invoices."""
    return jsonify(get_all_invoices()), 200


@facturas_bp.get("/vencidas")
@require_auth
def list_overdue_invoices():
    """Returns all overdue unpaid invoices."""
    return jsonify(get_overdue_invoices()), 200


@facturas_bp.get("/<int:invoice_id>")
@require_auth
def retrieve_invoice(invoice_id: int):
    """Returns a single invoice by ID."""
    invoice = get_invoice(invoice_id)
    if not invoice:
        return jsonify({"error": "Factura no encontrada"}), 404
    return jsonify(invoice), 200


@facturas_bp.get("/contrato/<int:contract_id>")
@require_auth
def retrieve_invoices_by_contract(contract_id: int):
    """Returns all invoices for a given contract."""
    return jsonify(get_invoices_by_contract(contract_id)), 200


@facturas_bp.put("/<int:invoice_id>")
@require_auth
def modify_invoice(invoice_id: int):
    """Registers payment on an invoice."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        invoice = update_invoice(invoice_id, data)
        if not invoice:
            return jsonify({"error": "Factura no encontrada"}), 404
        return jsonify(invoice), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@facturas_bp.delete("/<int:invoice_id>")
@require_admin
def remove_invoice(invoice_id: int):
    """Soft deletes an invoice. Not allowed if already paid."""
    try:
        if not delete_invoice(invoice_id):
            return jsonify({"error": "Factura no encontrada"}), 404
        return jsonify({"mensaje": "Factura eliminada correctamente"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@facturas_bp.get("/vista")
@require_auth_page
def invoices_view():
    """Renders the invoices list page."""
    invoices = get_all_invoices()
    overdue = get_overdue_invoices()
    return render_template(
        "facturas/index.html",
        invoices=invoices,
        overdue=overdue,
    )
