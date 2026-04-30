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
    return jsonify(get_all_invoices()), 200


@facturas_bp.get("/vencidas")
@require_auth
def list_overdue_invoices():
    return jsonify(get_overdue_invoices()), 200


@facturas_bp.get("/<int:id>")
@require_auth
def retrieve_invoice(id: int):
    invoice = get_invoice(id)
    if not invoice:
        return jsonify({"error": "Factura no encontrada"}), 404
    return jsonify(invoice), 200


@facturas_bp.get("/contrato/<int:contract_id>")
@require_auth
def retrieve_invoices_by_contract(contract_id: int):
    return jsonify(get_invoices_by_contract(contract_id)), 200


@facturas_bp.put("/<int:id>")
@require_auth
def modify_invoice(id: int):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        invoice = update_invoice(id, data)
        if not invoice:
            return jsonify({"error": "Factura no encontrada"}), 404
        return jsonify(invoice), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@facturas_bp.delete("/<int:id>")
@require_admin
def remove_invoice(id: int):
    try:
        if not delete_invoice(id):
            return jsonify({"error": "Factura no encontrada"}), 404
        return jsonify({"mensaje": "Factura eliminada correctamente"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    
@facturas_bp.get("/vista")
@require_auth_page
def invoices_view():
    """Returns all invoices rendered as HTML."""
    invoices = get_all_invoices()
    return render_template(
        "facturas/index.html",
        invoices=invoices,
        now=date.today().isoformat(),
    )