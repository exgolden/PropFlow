CREATE TABLE IF NOT EXISTS documentos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    unidad_id    INTEGER REFERENCES unidades(id),
    contrato_id  INTEGER REFERENCES contratos(id),
    inquilino_id INTEGER REFERENCES inquilinos(id),
    subido_por   INTEGER NOT NULL REFERENCES usuarios(id),
    nombre       TEXT NOT NULL,
    tipo         TEXT NOT NULL CHECK(tipo IN ('contrato', 'identificacion', 'permiso', 'seguro', 'otro')),
    url_archivo  TEXT NOT NULL,
    vence_en     TEXT,
    subido_en    TEXT NOT NULL DEFAULT (datetime('now')),
    eliminado_en TEXT
);