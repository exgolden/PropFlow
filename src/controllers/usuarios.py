# src/controllers/usuarios.py
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


def get_user(id: int) -> dict | None:
    """
    Returns a single user by ID without contrasena_hash, or None if not found.
    """
    logger.debug(f"Fetching user id={id}")
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT id, nombre, correo, rol, activo, creado_en, ultimo_acceso
            FROM usuarios WHERE id = ?
            """,
            (id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email(correo: str) -> dict | None:
    """
    Returns a single user by email including contrasena_hash.
    Only used internally for authentication — never returned to the client.
    """
    logger.debug(f"Fetching user by email correo={correo}")
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
        logger.warning(f"Attempted to create duplicate user correo={data['correo']}")
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
    logger.info(f"User created id={user_id} correo={data['correo']} rol={data['rol']}")
    return get_user(user_id)


def update_user(id: int, data: dict) -> dict | None:
    """
    Updates an existing user. Password is rehashed if provided.
    Returns the updated user, or None if not found.
    """
    user = get_user(id)
    if not user:
        logger.warning(f"User not found id={id}")
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
    values = list(updates.values()) + [id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE usuarios SET {columns} WHERE id = ?",
            values
        )
    logger.info(f"User updated id={id} fields={[k for k in updates.keys() if k != 'contrasena_hash']}")
    return get_user(id)


def deactivate_user(id: int) -> dict | None:
    """
    Deactivates a user by setting activo to 0.
    Returns the updated user, or None if not found.
    """
    user = get_user(id)
    if not user:
        logger.warning(f"User not found for deactivation id={id}")
        return None
    if not user["activo"]:
        logger.warning(f"Attempted to deactivate already inactive user id={id}")
        raise ValueError("El usuario ya está desactivado")
    with get_db() as conn:
        conn.execute(
            "UPDATE usuarios SET activo = 0 WHERE id = ?",
            (id,)
        )
    logger.info(f"User deactivated id={id}")
    return get_user(id)


def reactivate_user(id: int) -> dict | None:
    """
    Reactivates a previously deactivated user.
    Returns the updated user, or None if not found.
    """
    user = get_user(id)
    if not user:
        logger.warning(f"User not found for reactivation id={id}")
        return None
    if user["activo"]:
        logger.warning(f"Attempted to reactivate already active user id={id}")
        raise ValueError("El usuario ya está activo")
    with get_db() as conn:
        conn.execute(
            "UPDATE usuarios SET activo = 1 WHERE id = ?",
            (id,)
        )
    logger.info(f"User reactivated id={id}")
    return get_user(id)


def authenticate_user(correo: str, contrasena: str) -> dict | None:
    """
    Verifies email and password. Updates ultimo_acceso on success.
    Returns the user without contrasena_hash, or None if invalid credentials.
    """
    user = get_user_by_email(correo)
    if not user:
        logger.warning(f"Login failed — user not found correo={correo}")
        return None
    if not user["activo"]:
        logger.warning(f"Login failed — inactive user correo={correo}")
        return None
    password_matches = bcrypt.checkpw(
        contrasena.encode("utf-8"),
        user["contrasena_hash"].encode("utf-8")
    )
    if not password_matches:
        logger.warning(f"Login failed — wrong password correo={correo}")
        return None
    with get_db() as conn:
        conn.execute(
            "UPDATE usuarios SET ultimo_acceso = datetime('now') WHERE id = ?",
            (user["id"],)
        )
    logger.info(f"Login successful id={user['id']} correo={correo}")
    return get_user(user["id"])