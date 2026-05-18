# src/__init__.py
"""
App factory para PropFlow.
Configura Flask, blueprints, logger, scheduler y rutas globales.
"""
import os
from datetime import date
from werkzeug.exceptions import HTTPException
from flask import Flask, request, jsonify, session, render_template, redirect
from flask_wtf.csrf import CSRFProtect
from src.scheduler import start_scheduler
from src.logger import setup_logger, get_logger
from src.routes.dashboard import dashboard_bp
from src.routes.unidades import unidades_bp
from src.routes.inquilinos import inquilinos_bp
from src.routes.contratos import contratos_bp
from src.routes.facturas import facturas_bp
from src.routes.mantenimientos import mantenimientos_bp
from src.routes.documentos import documentos_bp
from src.routes.usuarios import usuarios_bp
from src.controllers.tokens_descarga import get_document_by_token

csrf = CSRFProtect()


def create_app() -> Flask:
    """
    App factory — creates and configures the Flask application.
    All blueprints, logger and scheduler are registered here.
    """
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY environment variable is not set")
    app.secret_key = secret_key
    setup_logger()
    logger = get_logger()

    csrf.init_app(app)
    csrf.exempt(usuarios_bp)
    csrf.exempt(unidades_bp)
    csrf.exempt(inquilinos_bp)
    csrf.exempt(contratos_bp)
    csrf.exempt(facturas_bp)
    csrf.exempt(mantenimientos_bp)
    csrf.exempt(documentos_bp)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(unidades_bp)
    app.register_blueprint(inquilinos_bp)
    app.register_blueprint(contratos_bp)
    app.register_blueprint(facturas_bp)
    app.register_blueprint(mantenimientos_bp)
    app.register_blueprint(documentos_bp)
    app.register_blueprint(usuarios_bp)

    @app.context_processor
    def inject_now():
        return {"now": date.today()}

    @app.before_request
    def log_request():
        logger.info("REQUEST  %s %s — user_id: %s", request.method, request.path, session.get("user_id", "anonymous"))

    @app.after_request
    def after_request(response):
        logger.info("RESPONSE %s %s — status: %s", request.method, request.path, response.status_code)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "font-src 'self' cdn.jsdelivr.net; "
            "img-src 'self' data:;"
        )
        return response

    @app.route("/descargar/<string:token>")
    def download_by_token(token: str):
        """Public endpoint — serves a document file using a signed token. No auth required."""
        document = get_document_by_token(token)
        if not document:
            return render_template("errors/404.html"), 404
        return redirect(document["url_archivo"])

    @app.errorhandler(404)
    def handle_not_found(e):
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({"error": "No encontrado"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        if isinstance(e, HTTPException):
            return e
        logger.error("UNEXPECTED ERROR %s %s — %s: %s", request.method, request.path, type(e).__name__, e)
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({"error": "Error interno del servidor"}), 500
        return render_template("errors/500.html"), 500

    start_scheduler()
    logger.info("Aplicación iniciada correctamente")
    return app
