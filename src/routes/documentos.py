# src/routes/documentos.py
"""
Rutas para la gestión de documentos.
Expone endpoints REST y vistas HTML para subir, consultar,
actualizar y eliminar documentos asociados a unidades, contratos o inquilinos.
También expone endpoints para generar y consumir tokens de descarga firmados.
"""
from datetime import date
from flask import Blueprint, request, jsonify, render_template, redirect
from src.controllers.documentos import (
    get_all_documents,
    get_document,
    create_document,
    update_document,
    delete_document,
    get_expiring_documents,
)
from src.controllers.unidades import get_all_units
from src.controllers.contratos import get_all_contracts
from src.controllers.inquilinos import get_all_tenants
from src.controllers.tokens_descarga import create_token, get_document_by_token
from src.files import save_file, delete_file
from src.routes.usuarios import require_auth, require_auth_page

documentos_bp = Blueprint("documentos", __name__, url_prefix="/documentos")


@documentos_bp.get("/")
@require_auth
def list_documents():
    """Returns all documents, optionally filtered by unidad_id, contrato_id, inquilino_id or tipo."""
    unidad_id = request.args.get("unidad_id", type=int)
    contrato_id = request.args.get("contrato_id", type=int)
    inquilino_id = request.args.get("inquilino_id", type=int)
    tipo = request.args.get("tipo")
    return jsonify(get_all_documents(unidad_id, contrato_id, inquilino_id, tipo)), 200


@documentos_bp.get("/por_vencer")
@require_auth
def list_expiring_documents():
    """Returns all documents expiring within the given number of days (default 30)."""
    days = request.args.get("dias", default=30, type=int)
    return jsonify(get_expiring_documents(days)), 200


@documentos_bp.get("/<int:document_id>")
@require_auth
def retrieve_document(document_id: int):
    """Returns a single document by ID."""
    document = get_document(document_id)
    if not document:
        return jsonify({"error": "Documento no encontrado"}), 404
    return jsonify(document), 200


@documentos_bp.post("/")
@require_auth
def add_document():
    """Uploads a new document and creates the database record."""
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


@documentos_bp.put("/<int:document_id>")
@require_auth
def modify_document(document_id: int):
    """Updates an existing document, replacing the file if a new one is provided."""
    document = get_document(document_id)
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
    document = update_document(document_id, data)
    return jsonify(document), 200


@documentos_bp.delete("/<int:document_id>")
@require_auth
def remove_document(document_id: int):
    """Deletes a document and removes the associated file from storage."""
    document = get_document(document_id)
    if not document:
        return jsonify({"error": "Documento no encontrado"}), 404
    delete_file(document["url_archivo"])
    delete_document(document_id)
    return jsonify({"mensaje": "Documento eliminado correctamente"}), 200


@documentos_bp.post("/<int:document_id>/token")
@require_auth
def generate_token(document_id: int):
    """Generates a signed download token for a document. Valid for 7 days."""
    document = get_document(document_id)
    if not document:
        return jsonify({"error": "Documento no encontrado"}), 404
    token = create_token(document_id)
    url = f"{request.host_url}descargar/{token['token']}"
    return jsonify({"url": url, "expira_en": token["expira_en"]}), 201


@documentos_bp.get("/vista")
@require_auth_page
def documents_view():
    """Renders the documents list page."""
    documents = get_all_documents()
    expiring = get_expiring_documents(days=30)
    units = get_all_units()
    contracts = get_all_contracts()
    tenants = get_all_tenants()
    return render_template(
        "documentos/index.html",
        documents=documents,
        expiring=expiring,
        units=units,
        contracts=contracts,
        tenants=tenants,
    )
