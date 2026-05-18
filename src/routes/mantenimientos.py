"""
Rutas para la gestión de mantenimientos.
Expone endpoints REST y vistas HTML para crear, consultar,
actualizar y eliminar solicitudes de mantenimiento.
"""
from flask import Blueprint, request, jsonify, render_template
from src.controllers.unidades import get_all_units
from src.controllers.mantenimientos import (
    get_all_maintenance,
    get_maintenance,
    create_maintenance,
    update_maintenance,
    delete_maintenance
)
from src.routes.usuarios import require_auth, require_admin, require_auth_page

mantenimientos_bp = Blueprint("mantenimientos", __name__, url_prefix="/mantenimientos")


@mantenimientos_bp.get("/")
@require_auth
def list_maintenance():
    """Returns all maintenance requests, optionally filtered by unidad_id, estado or prioridad."""
    unidad_id = request.args.get("unidad_id", type=int)
    estado = request.args.get("estado")
    prioridad = request.args.get("prioridad")
    return jsonify(get_all_maintenance(unidad_id, estado, prioridad)), 200


@mantenimientos_bp.get("/<int:maintenance_id>")
@require_auth
def retrieve_maintenance(maintenance_id: int):
    """Returns a single maintenance request by ID."""
    maintenance = get_maintenance(maintenance_id)
    if not maintenance:
        return jsonify({"error": "Mantenimiento no encontrado"}), 404
    return jsonify(maintenance), 200


@mantenimientos_bp.post("/")
@require_auth
def add_maintenance():
    """Creates a new maintenance request."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        maintenance = create_maintenance(data)
        return jsonify(maintenance), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@mantenimientos_bp.put("/<int:maintenance_id>")
@require_auth
def modify_maintenance(maintenance_id: int):
    """Updates an existing maintenance request."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        maintenance = update_maintenance(maintenance_id, data)
        if not maintenance:
            return jsonify({"error": "Mantenimiento no encontrado"}), 404
        return jsonify(maintenance), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@mantenimientos_bp.delete("/<int:maintenance_id>")
@require_admin
def remove_maintenance(maintenance_id: int):
    """Soft deletes a maintenance request. Only allowed if resolved."""
    try:
        if not delete_maintenance(maintenance_id):
            return jsonify({"error": "Mantenimiento no encontrado"}), 404
        return jsonify({"mensaje": "Mantenimiento eliminado correctamente"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@mantenimientos_bp.get("/vista")
@require_auth_page
def maintenance_view():
    """Renders the maintenance list page."""
    maintenance = get_all_maintenance()
    units = get_all_units()
    return render_template("mantenimientos/index.html", maintenance=maintenance, units=units)

