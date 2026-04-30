CREATE TABLE IF NOT EXISTS facturas (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    contrato_id       INTEGER NOT NULL REFERENCES contratos(id),
    fecha_emision     TEXT NOT NULL,
    fecha_vencimiento TEXT NOT NULL,
    periodo_inicio    TEXT NOT NULL,
    periodo_fin       TEXT NOT NULL,
    monto             REAL NOT NULL,
    pagado_en         TEXT,
    metodo_pago       TEXT CHECK(metodo_pago IN ('credito', 'efectivo', 'transferencia')),
    referencia_pago   TEXT,
    creado_en         TEXT NOT NULL DEFAULT (datetime('now')),
    eliminado_en      TEXT
);