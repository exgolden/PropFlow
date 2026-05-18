"""
Controller para la gestión de usuarios y autenticación.
Maneja creación, consulta, actualización, activación/desactivación
y autenticación de usuarios. Nunca expone contrasena_hash al cliente.
"""
import bcrypt
from db.init import get_db
from src.logger import get_logger

logger = get_logger()


def get_all_users() -> list[dict]:
    """
    Returns all users. Never returns contrasena_hash.
    """
    logger.debug("Fetching all users")
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT id, nombre, correo, rol, activo, creado_en, ultimo_acceso
            FROM usuarios
            ORDER BY id
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def get_user(user_id: int) -> dict | None:
    """
    Returns a single user by ID without contrasena_hash, or None if not found.
    """
    logger.debug("Fetching user user_id=%s", user_id)
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT id, nombre, correo, rol, activo, creado_en, ultimo_acceso
            FROM usuarios WHERE id = ?
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email(correo: str) -> dict | None:
    """
    Returns a single user by email including contrasena_hash.
    Only used internally for authentication — never returned to the client.
    """
    logger.debug("Fetching user by email correo=%s", correo)
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM usuarios WHERE correo = ?",
            (correo,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_user(data: dict) -> dict:
    """
    Creates a new user. Only admin and root can do this — enforced at the route level.
    Raises ValueError if required fields are missing or email already exists.
    """
    required_fields = ["nombre", "correo", "contrasena", "rol"]
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"El campo '{field}' es requerido")
    if get_user_by_email(data["correo"]):
        logger.warning("Attempted to create duplicate user correo=%s", data["correo"])
        raise ValueError("Ya existe un usuario con ese correo")
    contrasena_hash = bcrypt.hashpw(
        data["contrasena"].encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO usuarios (nombre, correo, contrasena_hash, rol)
            VALUES (?, ?, ?, ?)
            """,
            (
                data["nombre"],
                data["correo"],
                contrasena_hash,
                data["rol"],
            )
        )
        user_id = cursor.lastrowid
    logger.info("User created user_id=%s correo=%s rol=%s", user_id, data["correo"], data["rol"])
    return get_user(user_id)


def update_user(user_id: int, data: dict) -> dict | None:
    """
    Updates an existing user. Password is rehashed if provided.
    Returns the updated user, or None if not found.
    """
    user = get_user(user_id)
    if not user:
        logger.warning("User not found user_id=%s", user_id)
        return None
    allowed_fields = ["nombre", "correo"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if data.get("contrasena"):
        updates["contrasena_hash"] = bcrypt.hashpw(
            data["contrasena"].encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")
    if not updates:
        return user
    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [user_id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE usuarios SET {columns} WHERE id = ?", # nosec B608
            values
        )
    logger.info("User updated user_id=%s fields=%s", user_id, [k for k in updates.keys() if k != "contrasena_hash"])
    return get_user(user_id)


def deactivate_user(user_id: int) -> dict | None:
    """
    Deactivates a user by setting activo to 0.
    Returns the updated user, or None if not found.
    """
    user = get_user(user_id)
    if not user:
        logger.warning("User not found for deactivation user_id=%s", user_id)
        return None
    if user["rol"] == "root":
        logger.warning("Attempted to deactivate root user user_id=%s", user_id)
        raise ValueError("El usuario root no puede ser desactivado")
    if not user["activo"]:
        logger.warning("Attempted to deactivate already inactive user user_id=%s", user_id)
        raise ValueError("El usuario ya está desactivado")
    with get_db() as conn:
        conn.execute(
            "UPDATE usuarios SET activo = 0 WHERE id = ?",
            (user_id,)
        )
    logger.info("User deactivated user_id=%s", user_id)
    return get_user(user_id)


def reactivate_user(user_id: int) -> dict | None:
    """
    Reactivates a previously deactivated user.
    Returns the updated user, or None if not found.
    """
    user = get_user(user_id)
    if not user:
        logger.warning("User not found for reactivation user_id=%s", user_id)
        return None
    if user["activo"]:
        logger.warning("Attempted to reactivate already active user user_id=%s", user_id)
        raise ValueError("El usuario ya está activo")
    with get_db() as conn:
        conn.execute(
            "UPDATE usuarios SET activo = 1 WHERE id = ?",
            (user_id,)
        )
    logger.info("User reactivated user_id=%s", user_id)
    return get_user(user_id)


def authenticate_user(correo: str, contrasena: str) -> dict | None:
    """
    Verifies email and password. Updates ultimo_acceso on success.
    Returns the user without contrasena_hash, or None if invalid credentials.
    """
    user = get_user_by_email(correo)
    if not user:
        logger.warning("Login failed — user not found correo=%s", correo)
        return None
    if not user["activo"]:
        logger.warning("Login failed — inactive user correo=%s", correo)
        return None
    password_matches = bcrypt.checkpw(
        contrasena.encode("utf-8"),
        user["contrasena_hash"].encode("utf-8")
    )
    if not password_matches:
        logger.warning("Login failed — wrong password correo=%s", correo)
        return None
    with get_db() as conn:
        conn.execute(
            "UPDATE usuarios SET ultimo_acceso = datetime('now') WHERE id = ?",
            (user["id"],)
        )
    logger.info("Login successful user_id=%s correo=%s", user["id"], correo)
    return get_user(user["id"])
