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
from src.controllers.unidades import get_unit
from src.controllers.inquilinos import get_tenant
from src.controllers.facturas import get_invoices_by_contract
from src.controllers.documentos import get_all_documents
from src.routes.usuarios import require_auth, require_admin, require_auth_page

contratos_bp = Blueprint("contratos", __name__, url_prefix="/contratos")


@contratos_bp.get("/")
@require_auth
def list_contracts():
    return jsonify(get_all_contracts()), 200


@contratos_bp.get("/<int:id>")
@require_auth
def retrieve_contract(id: int):
    contract = get_contract(id)
    if not contract:
        return jsonify({"error": "Contrato no encontrado"}), 404
    return jsonify(contract), 200


@contratos_bp.get("/unidad/<int:unit_id>")
@require_auth
def retrieve_active_contract_by_unit(unit_id: int):
    contract = get_active_contract_by_unit(unit_id)
    if not contract:
        return jsonify({"error": "No hay contrato activo para esta unidad"}), 404
    return jsonify(contract), 200


@contratos_bp.post("/")
@require_auth
def add_contract():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        contract = create_contract(data)
        return jsonify(contract), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@contratos_bp.put("/<int:id>")
@require_auth
def modify_contract(id: int):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        contract = update_contract(id, data)
        if not contract:
            return jsonify({"error": "Contrato no encontrado"}), 404
        return jsonify(contract), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@contratos_bp.put("/<int:id>/terminar")
@require_auth
def end_contract(id: int):
    try:
        contract = terminate_contract(id)
        if not contract:
            return jsonify({"error": "Contrato no encontrado"}), 404
        return jsonify(contract), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@contratos_bp.delete("/<int:id>")
@require_admin
def remove_contract(id: int):
    try:
        if not delete_contract(id):
            return jsonify({"error": "Contrato no encontrado"}), 404
        return jsonify({"mensaje": "Contrato eliminado correctamente"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
@contratos_bp.get("/vista")
@require_auth_page
def contracts_view():
    contracts = get_all_contracts()
    return render_template("contratos/index.html", contracts=contracts)


@contratos_bp.get("/vista/<int:contract_id>")
@require_auth_page
def contract_detail_view(contract_id: int):
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