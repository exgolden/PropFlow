from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from src.controllers.usuarios import (
    get_all_users,
    get_user,
    create_user,
    update_user,
    deactivate_user,
    reactivate_user,
    authenticate_user
)

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")

@usuarios_bp.get("/login")
def login_page():
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))
    return render_template("login.html")

def require_auth(f):
    """
    Decorator that blocks unauthenticated requests.
    """
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """
    Decorator that blocks non-admin and non-root requests.
    """
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "No autenticado"}), 401
        if session.get("user_rol") not in ("admin", "root"):
            return jsonify({"error": "No autorizado"}), 403
        return f(*args, **kwargs)
    return decorated


@usuarios_bp.post("/login")
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    user = authenticate_user(data.get("correo"), data.get("contrasena"))
    if not user:
        return jsonify({"error": "Credenciales inválidas"}), 401
    session["user_id"] = user["id"]
    session["user_rol"] = user["rol"]
    return jsonify(user), 200

@usuarios_bp.get("/logout")
@require_auth
def logout_page():
    session.clear()
    return redirect(url_for("usuarios.login_page"))


@usuarios_bp.get("/me")
@require_auth
def me():
    user = get_user(session["user_id"])
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user), 200


@usuarios_bp.get("/")
@require_admin
def list_users():
    return jsonify(get_all_users()), 200


@usuarios_bp.get("/<int:id>")
@require_admin
def retrieve_user(id: int):
    user = get_user(id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user), 200


@usuarios_bp.post("/")
@require_admin
def add_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    try:
        user = create_user(data)
        return jsonify(user), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@usuarios_bp.put("/<int:id>")
@require_admin
def modify_user(id: int):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
    user = update_user(id, data)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user), 200


@usuarios_bp.put("/<int:id>/desactivar")
@require_admin
def disable_user(id: int):
    try:
        user = deactivate_user(id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify(user), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@usuarios_bp.put("/<int:id>/reactivar")
@require_admin
def enable_user(id: int):
    try:
        user = reactivate_user(id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify(user), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

def require_auth_page(f):
    """
    Decorator for template routes — redirects to login instead of returning JSON 401.
    """
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("usuarios.login_page"))
        return f(*args, **kwargs)
    return decorated


@usuarios_bp.get("/vista")
@require_admin
def users_view():
    """Returns all users rendered as HTML."""
    users = get_all_users()
    return render_template("usuarios/index.html", users=users)