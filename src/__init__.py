# src/__init__.py
import os
from flask import Flask, request, g, jsonify, session
from src.scheduler import start_scheduler
from src.logger import setup_logger, get_logger
from src.routes.dashboard import dashboard_bp
from src.routes.unidades import unidades_bp
from src.routes.inquilinos import inquilinos_bp
from src.routes.contratos import contratos_bp
from src.routes.facturas import facturas_bp
from src.routes.mantenimientos import mantenimientos_bp
from src.routes.documentos import documentos_bp
# from src.routes.notificaciones_log import notificaciones_bp
from src.routes.usuarios import usuarios_bp


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
    app.secret_key = os.environ.get("SECRET_KEY", "cambia-esto-en-produccion")
    setup_logger()
    logger = get_logger()

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(unidades_bp)
    app.register_blueprint(inquilinos_bp)
    app.register_blueprint(contratos_bp)
    app.register_blueprint(facturas_bp)
    app.register_blueprint(mantenimientos_bp)
    app.register_blueprint(documentos_bp)
    # app.register_blueprint(notificaciones_bp)
    app.register_blueprint(usuarios_bp)

    @app.before_request
    def log_request():
        logger.info(f"REQUEST  {request.method} {request.path} — user_id: {session.get('user_id', 'anonymous')}")

    @app.after_request
    def log_response(response):
        logger.info(f"RESPONSE {request.method} {request.path} — status: {response.status_code}")
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        logger.error(f"UNEXPECTED ERROR {request.method} {request.path} — {type(e).__name__}: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

    start_scheduler()
    logger.info("Aplicación iniciada correctamente")
    return app