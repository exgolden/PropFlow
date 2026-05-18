# src/routes/usuarios.py
"""
Rutas para la gestión de usuarios y autenticación.
Expone endpoints REST y vistas HTML para login, logout, y gestión de usuarios.
También define los decoradores require_auth, require_admin y require_auth_page
utilizados por el resto de las rutas.
"""
from functools import wraps
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from src.controllers.usuarios import (
    get_all_users,
    get_user,
    create_user,
    update_user,
    deactivate_user,
    reactivate_user,
    authenticate_user,
)

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def require_auth(f):
    """Decorator that blocks unauthenticated requests."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Decorator that blocks non-admin and non-root requests."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "No autenticado"}), 401
        if session.get("user_rol") not in ("admin", "root"):
            return jsonify({"error": "No autorizado"}), 403
        return f(*args, **kwargs)
    return decorated


def require_auth_page(f):
    """Decorator for template routes — redirects to login instead of returning JSON 401."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("usuarios.login_page"))
        return f(*args, **kwargs)
    return decorated


@usuarios_bp.get("/login")
def login_page():
    """Renders the login page, or redirects to dashboard if already logged in."""
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))
    return render_template("login.html")


@usuarios_bp.post("/login")
def login():
    """Authenticates a user and stores their session."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    user = authenticate_user(data.get("correo"), data.get("contrasena"))
    if not user:
        return jsonify({"error": "Credenciales inválidas"}), 401
    session["user_id"] = user["id"]
    session["user_rol"] = user["rol"]
    return jsonify(user), 200


@usuarios_bp.post("/logout")
@require_auth
def logout_page():
    """Clears the session and redirects to login."""
    session.clear()
    return redirect(url_for("usuarios.login_page"))


@usuarios_bp.get("/me")
@require_auth
def me():
    """Returns the currently authenticated user."""
    user = get_user(session["user_id"])
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user), 200


@usuarios_bp.get("/")
@require_admin
def list_users():
    """Returns all users."""
    return jsonify(get_all_users()), 200


@usuarios_bp.get("/<int:user_id>")
@require_admin
def retrieve_user(user_id: int):
    """Returns a single user by ID."""
    user = get_user(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user), 200


@usuarios_bp.post("/")
@require_admin
def add_user():
    """Creates a new user. Only admin and root can do this."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        user = create_user(data)
        return jsonify(user), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@usuarios_bp.put("/<int:user_id>")
@require_admin
def modify_user(user_id: int):
    """Updates an existing user."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    user = update_user(user_id, data)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user), 200


@usuarios_bp.put("/<int:user_id>/desactivar")
@require_admin
def disable_user(user_id: int):
    """Deactivates a user. Cannot deactivate root."""
    try:
        user = deactivate_user(user_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify(user), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@usuarios_bp.put("/<int:user_id>/reactivar")
@require_admin
def enable_user(user_id: int):
    """Reactivates a previously deactivated user."""
    try:
        user = reactivate_user(user_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify(user), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@usuarios_bp.get("/vista")
@require_admin
def users_view():
    """Renders the users list page."""
    users = get_all_users()
    return render_template("usuarios/index.html", users=users)
