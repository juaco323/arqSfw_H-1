-- Referencia pedagógica del diseño intencionalmente pobre.
-- En runtime las tablas se crean vía SQLAlchemy (models.py); este archivo
-- documenta el enfoque "tablón" sin FKs reforzadas en BD.

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL
);

-- Una sola tabla mezcla usuario (redundante), paquete, estado y evento.
CREATE TABLE IF NOT EXISTS tracking_data (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    username_redundant VARCHAR(100),
    user_email_copy VARCHAR(255),
    tracking_code VARCHAR(64) NOT NULL,
    package_title VARCHAR(200),
    status VARCHAR(50) NOT NULL,
    location VARCHAR(200),
    city VARCHAR(100),
    event_note TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_tracking_data_tracking_code ON tracking_data (tracking_code);
