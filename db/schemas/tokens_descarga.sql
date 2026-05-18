CREATE TABLE IF NOT EXISTS tokens_descarga (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    token        TEXT NOT NULL UNIQUE,
    documento_id INTEGER NOT NULL REFERENCES documentos(id),
    creado_en    TEXT NOT NULL DEFAULT (datetime('now')),
    expira_en    TEXT NOT NULL,
    usado_en     TEXT
);
