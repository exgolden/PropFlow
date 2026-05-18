"""
Rutas para la gestión de unidades.
Expone endpoints REST y vistas HTML para crear, consultar,
actualizar y eliminar unidades.
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from src.controllers.unidades import (
    get_all_units,
    get_unit,
    create_unit,
    update_unit,
    delete_unit,
)
from src.routes.usuarios import require_auth, require_admin, require_auth_page

unidades_bp = Blueprint("unidades", __name__, url_prefix="/unidades")


@unidades_bp.get("/")
@require_auth
def list_units():
    """Returns all units."""
    return jsonify(get_all_units()), 200


@unidades_bp.get("/<int:unit_id>")
@require_auth
def retrieve_unit(unit_id: int):
    """Returns a single unit by ID."""
    unit = get_unit(unit_id)
    if not unit:
        return jsonify({"error": "Unidad no encontrada"}), 404
    return jsonify(unit), 200


@unidades_bp.post("/")
@require_auth
def add_unit():
    """Creates a new unit."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        unit = create_unit(data)
        return jsonify(unit), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@unidades_bp.put("/<int:unit_id>")
@require_auth
def modify_unit(unit_id: int):
    """Updates an existing unit."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        unit = update_unit(unit_id, data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if not unit:
        return jsonify({"error": "Unidad no encontrada"}), 404
    return jsonify(unit), 200


@unidades_bp.delete("/<int:unit_id>")
@require_admin
def remove_unit(unit_id: int):
    """Soft deletes a unit."""
    if not delete_unit(unit_id):
        return jsonify({"error": "Unidad no encontrada"}), 404
    return jsonify({"mensaje": "Unidad eliminada correctamente"}), 200


@unidades_bp.get("/vista")
@require_auth_page
def units_view():
    """Renders the units list page."""
    units = get_all_units()
    return render_template("unidades/index.html", units=units)


@unidades_bp.get("/vista/<int:unit_id>")
@require_auth_page
def unit_detail_view(unit_id: int):
    """Renders the unit detail page."""
    unit = get_unit(unit_id)
    if not unit:
        return redirect(url_for("unidades.units_view"))
    return render_template("unidades/detail.html", unit=unit)
