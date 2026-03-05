-- ==========================================
--   NUEVA BD - CATÁLOGOS Y CONFIGURACIÓN
-- ==========================================

-- 1. Clientes
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    modo_envio VARCHAR(20) NOT NULL DEFAULT 'consolidado', -- 'consolidado' | 'por_lugar'
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 2. Lugares
CREATE TABLE lugares (
    id SERIAL PRIMARY KEY,
    cliente_id INT NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    nombre VARCHAR(150) NOT NULL,
    codigo_interno VARCHAR(100),
    requiere_bitacora_individual BOOLEAN DEFAULT FALSE,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 3. Destinatarios
CREATE TABLE destinatarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(200) NOT NULL,
    nombre VARCHAR(150),
    tipo VARCHAR(10) NOT NULL DEFAULT 'to', -- 'to' | 'cc' | 'bcc'
    cliente_id INT REFERENCES clientes(id) ON DELETE CASCADE,
    lugar_id INT REFERENCES lugares(id) ON DELETE CASCADE,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 4. Operadores
CREATE TABLE operadores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    email VARCHAR(150),
    rol VARCHAR(50),
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 5. Tipos de Evento (catálogo)
CREATE TABLE tipos_evento (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    categoria VARCHAR(100),
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 6. (OPCIONAL) Meta bitácoras
-- Si NO deseas guardar registro administrativo, puedes omitirla.
CREATE TABLE bitacoras_meta (
    id SERIAL PRIMARY KEY,
    cliente_id INT NOT NULL REFERENCES clientes(id),

    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    horario VARCHAR(100),

    num_eventos INT,
    ruta_pdf TEXT,
    enviada_a TEXT,

    creada_por INT REFERENCES operadores(id),
    fecha_envio TIMESTAMP DEFAULT NOW()
);
