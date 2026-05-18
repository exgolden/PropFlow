# src/routes/contratos.py
"""
Rutas para la gestión de contratos.
Expone endpoints REST y vistas HTML para crear, consultar, actualizar,
terminar y eliminar contratos.
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from src.controllers.contratos import (
    get_all_contracts,
    get_contract,
    get_active_contract_by_unit,
    create_contract,
    update_contract,
    terminate_contract,
    delete_contract,
)
from src.controllers.unidades import get_unit, get_all_units
from src.controllers.inquilinos import get_tenant, get_all_tenants
from src.controllers.facturas import get_invoices_by_contract
from src.controllers.documentos import get_all_documents
from src.routes.usuarios import require_auth, require_admin, require_auth_page

contratos_bp = Blueprint("contratos", __name__, url_prefix="/contratos")


@contratos_bp.get("/")
@require_auth
def list_contracts():
    """Returns all contracts."""
    return jsonify(get_all_contracts()), 200


@contratos_bp.get("/<int:contract_id>")
@require_auth
def retrieve_contract(contract_id: int):
    """Returns a single contract by ID."""
    contract = get_contract(contract_id)
    if not contract:
        return jsonify({"error": "Contrato no encontrado"}), 404
    return jsonify(contract), 200


@contratos_bp.get("/unidad/<int:unit_id>")
@require_auth
def retrieve_active_contract_by_unit(unit_id: int):
    """Returns the active contract for a given unit."""
    contract = get_active_contract_by_unit(unit_id)
    if not contract:
        return jsonify({"error": "No hay contrato activo para esta unidad"}), 404
    return jsonify(contract), 200


@contratos_bp.post("/")
@require_auth
def add_contract():
    """Creates a new contract."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        contract = create_contract(data)
        return jsonify(contract), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@contratos_bp.put("/<int:contract_id>")
@require_auth
def modify_contract(contract_id: int):
    """Updates an existing contract."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        contract = update_contract(contract_id, data)
        if not contract:
            return jsonify({"error": "Contrato no encontrado"}), 404
        return jsonify(contract), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@contratos_bp.put("/<int:contract_id>/terminar")
@require_auth
def end_contract(contract_id: int):
    """Terminates an active contract."""
    try:
        contract = terminate_contract(contract_id)
        if not contract:
            return jsonify({"error": "Contrato no encontrado"}), 404
        return jsonify(contract), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@contratos_bp.delete("/<int:contract_id>")
@require_admin
def remove_contract(contract_id: int):
    """Soft deletes a contract. Only allowed if not active."""
    try:
        if not delete_contract(contract_id):
            return jsonify({"error": "Contrato no encontrado"}), 404
        return jsonify({"mensaje": "Contrato eliminado correctamente"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@contratos_bp.get("/vista")
@require_auth_page
def contracts_view():
    """Renders the contracts list page."""
    contracts = get_all_contracts()
    units = get_all_units()
    tenants = get_all_tenants()
    return render_template("contratos/index.html", contracts=contracts, units=units, tenants=tenants)


@contratos_bp.get("/vista/<int:contract_id>")
@require_auth_page
def contract_detail_view(contract_id: int):
    """Renders the contract detail page."""
    contract = get_contract(contract_id)
    if not contract:
        return redirect(url_for("contratos.contracts_view"))
    unit = get_unit(contract["unidad_id"])
    tenant = get_tenant(contract["inquilino_id"])
    invoices = get_invoices_by_contract(contract_id)
    documents = get_all_documents(contrato_id=contract_id)
    return render_template(
        "contratos/detail.html",
        contract=contract,
        unit=unit,
        tenant=tenant,
        invoices=invoices,
        documents=documents,
    )
