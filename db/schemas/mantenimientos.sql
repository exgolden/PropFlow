CREATE TABLE IF NOT EXISTS mantenimientos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    unidad_id        INTEGER NOT NULL REFERENCES unidades(id),
    titulo           TEXT NOT NULL,
    descripcion      TEXT,
    prioridad        TEXT NOT NULL DEFAULT 'media'
                        CHECK(prioridad IN ('baja', 'media', 'alta', 'urgente')),
    costo            REAL,
    estado           TEXT NOT NULL DEFAULT 'abierto'
                        CHECK(estado IN ('abierto', 'en_proceso', 'resuelto')),
    fecha_programada TEXT,
    fecha_resolucion TEXT,
    creado_en        TEXT NOT NULL DEFAULT (datetime('now')),
    eliminado_en     TEXT
);