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
    return jsonify(get_all_units()), 200


@unidades_bp.get("/<int:id>")
@require_auth
def retrieve_unit(id: int):
    unit = get_unit(id)
    if not unit:
        return jsonify({"error": "Unidad no encontrada"}), 404
    return jsonify(unit), 200


@unidades_bp.post("/")
@require_auth
def add_unit():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        unit = create_unit(data)
        return jsonify(unit), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@unidades_bp.put("/<int:id>")
@require_auth
def modify_unit(id: int):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    unit = update_unit(id, data)
    if not unit:
        return jsonify({"error": "Unidad no encontrada"}), 404
    return jsonify(unit), 200


@unidades_bp.delete("/<int:id>")
@require_admin
def remove_unit(id: int):
    if not delete_unit(id):
        return jsonify({"error": "Unidad no encontrada"}), 404
    return jsonify({"mensaje": "Unidad eliminada correctamente"}), 200

@unidades_bp.get("/vista")
@require_auth_page
def units_view():
    units = get_all_units()
    return render_template("unidades/index.html", units=units)


@unidades_bp.get("/vista/<int:unit_id>")
@require_auth_page
def unit_detail_view(unit_id: int):
    unit = get_unit(unit_id)
    if not unit:
        return redirect(url_for("unidades.units_view"))
    return render_template("unidades/detail.html", unit=unit)