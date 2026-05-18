CREATE TABLE IF NOT EXISTS inquilinos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa         TEXT NOT NULL,
    nombre_contacto TEXT NOT NULL,
    correo          TEXT NOT NULL,
    telefono        TEXT,
    rfc             TEXT,
    creado_en       TEXT NOT NULL DEFAULT (datetime('now')),
    eliminado_en    TEXT
);
