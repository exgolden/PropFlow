CREATE TABLE IF NOT EXISTS notificaciones_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    inquilino_id INTEGER REFERENCES inquilinos(id),
    factura_id   INTEGER REFERENCES facturas(id),
    contrato_id  INTEGER REFERENCES contratos(id),
    tipo         TEXT NOT NULL,
    canal        TEXT NOT NULL CHECK(canal IN ('correo', 'sms', 'whatsapp')),
    destinatario TEXT NOT NULL,
    estado       TEXT NOT NULL CHECK(estado IN ('enviado', 'entregado', 'fallido', 'rebotado')),
    error_msg    TEXT,
    enviado_en   TEXT NOT NULL DEFAULT (datetime('now'))
);