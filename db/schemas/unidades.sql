CREATE TABLE IF NOT EXISTS unidades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    numero      TEXT NOT NULL UNIQUE,
    area_m2     REAL,
    tipo        TEXT CHECK(tipo IN ('oficina', 'local', 'bodega', 'consultorio')),
    renta_base  REAL NOT NULL,
    estado      TEXT NOT NULL DEFAULT 'disponible'
                    CHECK(estado IN ('disponible', 'ocupada', 'mantenimiento')),
    creado_en   TEXT NOT NULL DEFAULT (datetime('now')),
    eliminado_en TEXT
);