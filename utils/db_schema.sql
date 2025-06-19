-- =============================================
-- TABLA DE USUARIOS (Autenticación)
-- =============================================
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(100),
    es_admin BOOLEAN DEFAULT FALSE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- TABLA DE CLIENTES (Con alias único oculto)
-- =============================================
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    alias VARCHAR(100) UNIQUE NOT NULL,
    creado_por INTEGER REFERENCES usuarios(id),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- TABLA DE CATEGORÍAS (Independiente)
-- =============================================
CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT
);

-- =============================================
-- TABLA DE ITEMS BASE (Vinculados a categorías)
-- =============================================
CREATE TABLE items_base (
    id SERIAL PRIMARY KEY,
    categoria_id INTEGER REFERENCES categorias(id) ON DELETE RESTRICT,
    nombre VARCHAR(100) NOT NULL,
    unidad VARCHAR(20) NOT NULL,
    precio_referencia NUMERIC(12, 2),
    UNIQUE (nombre, unidad)  -- Evita duplicados exactos
);

-- =============================================
-- TABLA DE PRESUPUESTOS (Cabecera)
-- =============================================
CREATE TABLE presupuestos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id) ON DELETE RESTRICT,
    lugar_trabajo VARCHAR(255) NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(12, 2) NOT NULL,
    ruta_pdf VARCHAR(255) NOT NULL,
    creado_por INTEGER REFERENCES usuarios(id),
    notas TEXT
);

-- =============================================
-- TABLA DE ITEMS_EN_PRESUPUESTO (Asociación)
-- =============================================
CREATE TABLE items_en_presupuesto (
    id SERIAL PRIMARY KEY,
    presupuesto_id INTEGER REFERENCES presupuestos(id) ON DELETE CASCADE,
    item_base_id INTEGER REFERENCES items_base(id) ON DELETE SET NULL,  -- Permite borrar ítem base manteniendo histórico
    categoria_id INTEGER REFERENCES categorias(id) ON DELETE RESTRICT,
    nombre_personalizado VARCHAR(100),  -- Para sobreescribir el nombre del ítem base
    unidad VARCHAR(20) NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(12, 2) NOT NULL,
    total NUMERIC(12, 2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,
    notas TEXT
);

-- =============================================
-- ÍNDICES PARA MEJORAR RENDIMIENTO
-- =============================================
CREATE INDEX idx_presupuestos_cliente ON presupuestos(cliente_id);
CREATE INDEX idx_items_en_presupuesto_presupuesto ON items_en_presupuesto(presupuesto_id);
CREATE INDEX idx_items_base_categoria ON items_base(categoria_id);


-- =============================================
-- TABLA DE LUGARES DE TRABAJO
-- =============================================
CREATE TABLE lugares_trabajo (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) UNIQUE NOT NULL,
    direccion TEXT,
    creado_por INTEGER REFERENCES usuarios(id),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);