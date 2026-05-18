"""
Rutas para la gestión de inquilinos.
Expone endpoints REST y vistas HTML para crear, consultar,
actualizar y eliminar inquilinos.
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from src.controllers.inquilinos import (
    get_all_tenants,
    get_tenant,
    create_tenant,
    update_tenant,
    delete_tenant,
)
from src.controllers.documentos import get_all_documents
from src.routes.usuarios import require_auth, require_admin, require_auth_page

inquilinos_bp = Blueprint("inquilinos", __name__, url_prefix="/inquilinos")


@inquilinos_bp.get("/")
@require_auth
def list_tenants():
    """Returns all tenants."""
    return jsonify(get_all_tenants()), 200


@inquilinos_bp.get("/<int:tenant_id>")
@require_auth
def retrieve_tenant(tenant_id: int):
    """Returns a single tenant by ID."""
    tenant = get_tenant(tenant_id)
    if not tenant:
        return jsonify({"error": "Inquilino no encontrado"}), 404
    return jsonify(tenant), 200


@inquilinos_bp.post("/")
@require_auth
def add_tenant():
    """Creates a new tenant."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        tenant = create_tenant(data)
        return jsonify(tenant), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@inquilinos_bp.put("/<int:tenant_id>")
@require_auth
def modify_tenant(tenant_id: int):
    """Updates an existing tenant."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        tenant = update_tenant(tenant_id, data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if not tenant:
        return jsonify({"error": "Inquilino no encontrado"}), 404
    return jsonify(tenant), 200


@inquilinos_bp.delete("/<int:tenant_id>")
@require_auth
def remove_tenant(tenant_id: int):
    """Soft deletes a tenant."""
    if not delete_tenant(tenant_id):
        return jsonify({"error": "Inquilino no encontrado"}), 404
    return jsonify({"mensaje": "Inquilino eliminado correctamente"}), 200


@inquilinos_bp.get("/vista")
@require_auth_page
def tenants_view():
    """Renders the tenants list page."""
    tenants = get_all_tenants()
    return render_template("inquilinos/index.html", tenants=tenants)


@inquilinos_bp.get("/vista/<int:tenant_id>")
@require_auth_page
def tenant_detail_view(tenant_id: int):
    """Renders the tenant detail page."""
    tenant = get_tenant(tenant_id)
    if not tenant:
        return redirect(url_for("inquilinos.tenants_view"))
    documents = get_all_documents(inquilino_id=tenant_id)
    return render_template(
        "inquilinos/detail.html",
        tenant=tenant,
        documents=documents,
    )
