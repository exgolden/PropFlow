CREATE TABLE IF NOT EXISTS usuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    correo          TEXT NOT NULL UNIQUE,
    contrasena_hash TEXT NOT NULL,
    rol             TEXT NOT NULL CHECK(rol IN ('root', 'admin', 'staff')),
    activo          INTEGER NOT NULL DEFAULT 1,
    creado_en       TEXT NOT NULL DEFAULT (datetime('now')),
    ultimo_acceso   TEXT
);