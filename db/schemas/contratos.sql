CREATE TABLE IF NOT EXISTS contratos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    unidad_id     INTEGER NOT NULL REFERENCES unidades(id),
    inquilino_id  INTEGER NOT NULL REFERENCES inquilinos(id),
    fecha_inicio  TEXT NOT NULL,
    fecha_fin     TEXT NOT NULL,
    renta_mensual REAL NOT NULL,
    deposito      REAL NOT NULL DEFAULT 0,
    dia_cobro     INTEGER NOT NULL DEFAULT 1 CHECK(dia_cobro BETWEEN 1 AND 28),
    estado        TEXT NOT NULL DEFAULT 'activo'
                    CHECK(estado IN ('activo', 'vencido', 'terminado')),
    creado_en     TEXT NOT NULL DEFAULT (datetime('now')),
    eliminado_en  TEXT
);