from datetime import date
from flask import Blueprint, request, jsonify, render_template
from src.controllers.documentos import (
    get_all_documents,
    get_document,
    create_document,
    update_document,
    delete_document,
    get_expiring_documents,
)
from src.files import save_file, delete_file
from src.routes.usuarios import require_auth, require_admin, require_auth_page

documentos_bp = Blueprint("documentos", __name__, url_prefix="/documentos")


@documentos_bp.get("/")
@require_auth
def list_documents():
    unidad_id = request.args.get("unidad_id", type=int)
    contrato_id = request.args.get("contrato_id", type=int)
    inquilino_id = request.args.get("inquilino_id", type=int)
    tipo = request.args.get("tipo")
    return jsonify(get_all_documents(unidad_id, contrato_id, inquilino_id, tipo)), 200


@documentos_bp.get("/por_vencer")
@require_auth
def list_expiring_documents():
    days = request.args.get("dias", default=30, type=int)
    return jsonify(get_expiring_documents(days)), 200


@documentos_bp.get("/<int:id>")
@require_auth
def retrieve_document(id: int):
    document = get_document(id)
    if not document:
        return jsonify({"error": "Documento no encontrado"}), 404
    return jsonify(document), 200


@documentos_bp.post("/")
@require_auth
def add_document():
    if "archivo" not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400
    file = request.files["archivo"]
    if not file.filename:
        return jsonify({"error": "El archivo no tiene nombre"}), 400
    data = request.form.to_dict()
    try:
        data["url_archivo"] = save_file(file)
        document = create_document(data)
        return jsonify(document), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@documentos_bp.put("/<int:id>")
@require_auth
def modify_document(id: int):
    document = get_document(id)
    if not document:
        return jsonify({"error": "Documento no encontrado"}), 404
    data = {}
    if "archivo" in request.files:
        file = request.files["archivo"]
        if file.filename:
            try:
                delete_file(document["url_archivo"])
                data["url_archivo"] = save_file(file)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
    data.update(request.form.to_dict())
    document = update_document(id, data)
    return jsonify(document), 200


@documentos_bp.delete("/<int:id>")
@require_admin
def remove_document(id: int):
    document = get_document(id)
    if not document:
        return jsonify({"error": "Documento no encontrado"}), 404
    delete_file(document["url_archivo"])
    delete_document(id)
    return jsonify({"mensaje": "Documento eliminado correctamente"}), 200


@documentos_bp.get("/vista")
@require_auth_page
def documents_view():
    """Returns all documents rendered as HTML."""
    documents = get_all_documents()
    expiring = get_expiring_documents(days=30)
    return render_template(
        "documentos/index.html",
        documents=documents,
        expiring=expiring,
        now=date.today().isoformat(),
    )