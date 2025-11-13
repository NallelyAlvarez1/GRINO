--
-- PostgreSQL database
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;
SET default_tablespace = '';
SET default_table_access_method = heap;


-- =============================================
-- TABLA DE USUARIOS
-- =============================================
CREATE TABLE public.usuarios (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(255) NOT NULL,
    nombre_completo character varying(100),
    es_admin boolean DEFAULT false,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    nombre character varying(50),
    apellidos character varying(50),
    correo_electronico character varying(100),
    telefono character varying(20)
);


ALTER TABLE public.usuarios OWNER TO postgres;
CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO postgres;
ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;

-- =============================================
-- TABLA DE CLIENTES
-- =============================================

CREATE TABLE public.clientes (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    alias character varying(100) NOT NULL,
    creado_por integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE public.clientes OWNER TO postgres;
CREATE SEQUENCE public.clientes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.clientes_id_seq OWNER TO postgres;
ALTER SEQUENCE public.clientes_id_seq OWNED BY public.clientes.id;


-- =============================================
-- TABLA DE CATEGORÍAS 
-- =============================================
CREATE TABLE public.categorias (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    creado_por integer
);


ALTER TABLE public.categorias OWNER TO postgres;

CREATE SEQUENCE public.categorias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.categorias_id_seq OWNER TO postgres;
ALTER SEQUENCE public.categorias_id_seq OWNED BY public.categorias.id;

-- =============================================
-- TABLA DE ITEMS BASE 
-- =============================================
CREATE TABLE public.items_base (
    id integer NOT NULL,
    categoria_id integer,
    nombre character varying(100) NOT NULL,
    unidad character varying(20) NOT NULL,
    precio_referencia numeric(12,2)
);


ALTER TABLE public.items_base OWNER TO postgres;
CREATE SEQUENCE public.items_base_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.items_base_id_seq OWNER TO postgres;
ALTER SEQUENCE public.items_base_id_seq OWNED BY public.items_base.id;

-- =============================================
-- TABLA DE ITEMS_EN_PRESUPUESTOS 
-- =============================================
CREATE TABLE public.items_en_presupuesto (
    id integer NOT NULL,
    presupuesto_id integer,
    categoria_id integer,
    nombre_personalizado character varying(100) NOT NULL,
    unidad character varying(20) NOT NULL,
    cantidad integer NOT NULL,
    precio_unitario numeric(12,2) NOT NULL,
    total numeric(12,2) GENERATED ALWAYS AS (((cantidad)::numeric * precio_unitario)) STORED,
    notas text
);


ALTER TABLE public.items_en_presupuesto OWNER TO postgres;
CREATE SEQUENCE public.items_en_presupuesto_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.items_en_presupuesto_id_seq OWNER TO postgres;
ALTER SEQUENCE public.items_en_presupuesto_id_seq OWNED BY public.items_en_presupuesto.id;


-- =============================================
-- TABLA DE ITEMS_EN_PRESUPUESTO (Asociación)
-- =============================================
CREATE TABLE public.presupuestos (
    id integer NOT NULL,
    cliente_id integer,
    lugar_trabajo_id integer,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    descripcion text,
    total numeric(12,2) NOT NULL,
    creado_por integer,
    notas text
);


ALTER TABLE public.presupuestos OWNER TO postgres;
CREATE SEQUENCE public.presupuestos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.presupuestos_id_seq OWNER TO postgres;
ALTER SEQUENCE public.presupuestos_id_seq OWNED BY public.presupuestos.id;

-- =============================================
-- TABLA DE LUGARES DE TRABAJO
-- =============================================

CREATE TABLE public.lugares_trabajo (
    id integer NOT NULL,
    nombre character varying(255) NOT NULL,
    direccion text,
    creado_por integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.lugares_trabajo OWNER TO postgres;
CREATE SEQUENCE public.lugares_trabajo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.lugares_trabajo_id_seq OWNER TO postgres;
ALTER SEQUENCE public.lugares_trabajo_id_seq OWNED BY public.lugares_trabajo.id;


-- =============================================
-- ADICIONALES e INSERT
-- =============================================
-- 🔒 Activa RLS en todas tus tablas
ALTER TABLE public.clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lugares_trabajo ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.presupuestos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.items_en_presupuesto ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categorias ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.items_base ENABLE ROW LEVEL SECURITY;

-- 👀 Crea una política que permita acceso completo (solo para tu sistema interno)
CREATE POLICY "permitir_todo_usuarios" ON public.usuarios FOR ALL USING (true);
CREATE POLICY "permitir_todo_clientes" ON public.clientes FOR ALL USING (true);
CREATE POLICY "permitir_todo_presupuestos" ON public.presupuestos FOR ALL USING (true);
CREATE POLICY "permitir_todo_lugares_trabajo" ON public.lugares_trabajo FOR ALL USING (true);
CREATE POLICY "permitir_todo_items_en_presupuesto" ON public.items_en_presupuesto FOR ALL USING (true);
CREATE POLICY "permitir_todo_categorias" ON public.categorias FOR ALL USING (true);
CREATE POLICY "permitir_todo_items" ON public.items_base FOR ALL USING (true);


CREATE INDEX idx_presupuestos_cliente ON presupuestos(cliente_id);
CREATE INDEX idx_items_en_presupuesto_presupuesto ON items_en_presupuesto(presupuesto_id);
CREATE INDEX idx_items_base_categoria ON public.items_base USING btree (categoria_id);

ALTER TABLE ONLY public.categorias ALTER COLUMN id SET DEFAULT nextval('public.categorias_id_seq'::regclass);
ALTER TABLE ONLY public.clientes ALTER COLUMN id SET DEFAULT nextval('public.clientes_id_seq'::regclass);
ALTER TABLE ONLY public.items_base ALTER COLUMN id SET DEFAULT nextval('public.items_base_id_seq'::regclass);
ALTER TABLE ONLY public.items_en_presupuesto ALTER COLUMN id SET DEFAULT nextval('public.items_en_presupuesto_id_seq'::regclass);
ALTER TABLE ONLY public.lugares_trabajo ALTER COLUMN id SET DEFAULT nextval('public.lugares_trabajo_id_seq'::regclass);
ALTER TABLE ONLY public.presupuestos ALTER COLUMN id SET DEFAULT nextval('public.presupuestos_id_seq'::regclass);
ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- TOC entry 4971 (class 0 OID 32880)
-- Dependencies: 222
-- Data for Name: categorias; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.categorias (id, nombre, descripcion, creado_por) FROM stdin;
1	Terraza	\N	\N
2	Piscina	\N	\N
3	Cambio de valvulas	\N	\N
4	Piscina 2	\N	\N
5	Base de madera	\N	\N
6	Patio delantero	\N	1
7	Plantas	\N	1
8	Cesped	\N	1
9	Puerta Jardín	\N	1
\.


--
-- TOC entry 4969 (class 0 OID 32865)
-- Dependencies: 220
-- Data for Name: clientes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.clientes (id, nombre, alias, creado_por, fecha_registro) FROM stdin;
2	Por confirmar	por-confirmar-da16	1	2025-06-11 17:09:39.049314
3	Juan	juan-36bd	1	2025-06-11 17:09:50.605317
5	Pedro	pedro-a8a8	1	2025-06-13 20:51:50.942318
4	Juan Pablo	juan-3778	1	2025-06-11 17:10:06.403069
1	Mario mario-a3bb	1	2025-06-11 17:04:29.471158
6	Rosario	rosario-b6a2	1	2025-06-21 17:50:36.186797
7	Matias 	matias-3-faf6	1	2025-07-03 15:57:07.446457
8	Roberto roberto-8-6ee6	1	2025-07-03 16:00:06.590654
9	Lucia lucia-9-0529	1	2025-07-03 16:01:55.68262
10	Rodrigo rodrigo-0-33a0	1	2025-07-03 16:04:15.634074
11	Claudia	claudia-2f51	1	2025-07-03 16:57:27.647903
12	felipe	felipe-96fd	1	2025-07-04 16:29:53.082886
13	Julian	julian-fb93	1	2025-09-30 13:12:16.157088
14	Alejandro	alejandro-18fd	1	2025-09-30 15:25:48.626158
15	Diego	diego-21a6	1	2025-10-22 20:48:08.284875
16	Tamara	tamara-0ed6	1	2025-10-29 21:44:32.789924
\.



COPY public.lugares_trabajo (id, nombre, direccion, creado_por, fecha_registro) FROM stdin;
1	Los Acasios	\N	1	2025-06-12 00:39:29.29303
2	Lagares Casa #64	\N	1	2025-10-22 20:48:36.831066
3	Condominio La Ñipa Casa 12	\N	1	2025-10-29 21:45:00.92368
4	Los Agapantos #45	\N	1	2025-06-20 19:13:28.891076
5	Condominio Terralta Guay Guay Casa 73	\N	1	2025-10-29 22:13:14.293109
\.

INSERT INTO public.presupuestos (id, cliente_id, lugar_trabajo_id, fecha_creacion, descripcion, total, creado_por, notas) VALUES
(67,4,1,'2025-10-09 21:47:13.262317','Instalación de riego en terraza',23000.00,1,NULL),
(70,4,1,'2025-10-15 15:03:23.992073','[EDITADO] Instalación de riego en terraza',230000.00,1,NULL),
(71,1,1,'2025-10-15 15:30:47.692626','[EDITADO]',2059660.00,1,NULL),
(73,15,2,'2025-10-22 21:25:07.221685','',1191350.00,1,NULL),
(74,14,1,'2025-10-23 17:25:55.460932','Rellenado de piscina',33400.00,1,NULL),
(75,3,1,'2025-10-29 21:40:44.576273','Reaparacion piscina',5670.00,1,NULL),
(76,16,3,'2025-10-29 22:07:22.201288','',233500.00,1,NULL),
(77,16,3,'2025-10-29 22:08:50.687542','Compra e Instalación de plantas',233500.00,1,NULL),
(78,2,5,'2025-10-29 22:20:55.962954','Reemplazo de cesped',1007500.00,1,NULL);

INSERT INTO public.items_en_presupuesto (id, presupuesto_id, categoria_id, nombre_personalizado, unidad, cantidad, precio_unitario, notas) VALUES
(101,67,2,'riegos','m²',10,2300.00,NULL),
(104,70,2,'riegos','m²',100,2300.00,NULL),
(105,71,2,'Mano de Obra','Unidad',1,56000.00,'Mano de obra'),
(106,71,2,'Valvulas','Unidad',17,6790.00,NULL),
(107,71,2,'agua','m³',170,679.00,NULL),
(108,71,1,'Mano de Obra','Unidad',1,87900.00,'Mano de obra'),
(109,71,1,'Pasto','Metro lineal',170,6790.00,NULL),
(110,71,1,'Tablas','Unidad',58,8900.00,NULL),
(120,73,5,'Mano de Obra','Unidad',1,450000.00,'Mano de obra'),
(121,73,5,'Rollizo 4''','Unidad',20,8200.00,NULL),
(122,73,5,'Pino Deck 1x4','Unidad',50,5489.00,NULL),
(123,73,5,'Pino bruto 2x4','Unidad',20,6500.00,NULL),
(124,73,5,'Tornillo turbo','Unidad',1,32000.00,NULL),
(125,73,5,'Tornillo madera 2''','Unidad',5,2500.00,NULL),
(126,73,5,'Rollizo 1x2','Unidad',40,2400.00,NULL),
(127,73,5,'Tornillo madera 3''','Unidad',2,9900.00,NULL),
(128,73,5,'Cemento','Saco',3,4200.00,NULL),
(129,74,2,'Agua','Unidad',10,3340.00,NULL),
(130,75,5,'jio','m²',10,567.00,NULL),
(131,76,7,'Mano de Obra','Unidad',1,25000.00,'Mano de obra'),
(132,76,7,'hortencia invierno','Unidad',4,4500.00,NULL),
(133,76,7,'lestospermum','Unidad',1,12500.00,NULL),
(134,76,7,'tobira enano','Unidad',5,4500.00,NULL),
(135,76,7,'erica','Unidad',3,4500.00,NULL),
(136,76,7,'dietes','Unidad',3,3500.00,NULL),
(137,76,7,'stenocarpus','Unidad',2,6500.00,NULL),
(138,76,7,'crespon','Unidad',1,45000.00,NULL),
(139,76,7,'buganbillia','Unidad',1,25000.00,NULL),
(140,76,7,'ficus repens','Unidad',10,3000.00,NULL),
(141,76,7,'diosma','Unidad',1,5500.00,NULL),
(142,76,7,'teucrium','Unidad',2,6500.00,NULL),
(143,77,7,'Mano de Obra','Unidad',1,25000.00,'Mano de obra'),
(144,77,7,'hortencia invierno','Unidad',4,4500.00,NULL),
(145,77,7,'lestospermum','Unidad',1,12500.00,NULL),
(146,77,7,'tobira enano','Unidad',5,4500.00,NULL),
(147,77,7,'erica','Unidad',3,4500.00,NULL),
(148,77,7,'dietes','Unidad',3,3500.00,NULL),
(149,77,7,'stenocarpus','Unidad',2,6500.00,NULL),
(150,77,7,'crespon','Unidad',1,45000.00,NULL),
(151,77,7,'buganbillia','Unidad',1,25000.00,NULL),
(152,77,7,'ficus repens','Unidad',10,3000.00,NULL),
(153,77,7,'diosma','Unidad',1,5500.00,NULL),
(154,77,7,'teucrium','Unidad',2,6500.00,NULL),
(155,78,7,'Mano de Obra','Unidad',1,25000.00,'Mano de obra'),
(156,78,8,'Cesped','m²',130,2500.00,NULL),
(157,78,8,'Remoción de cesped','m²',130,2500.00,NULL),
(158,78,8,'Nivelación de terreno','m²',130,2500.00,NULL),
(159,78,8,'Tierra vegetal','m³',2,2500.00,NULL),
(160,78,8,'Retiro de escombros','m²',1,2500.00,NULL);



COPY public.usuarios (id, username, password_hash, nombre_completo, es_admin, fecha_registro, nombre, apellidos, correo_electronico, telefono) FROM stdin;
1	admin	$2b$12$DsKd9oRV42SyA.CpxdALN.QhFR4Zwyupb.QQh3bpiouCCinihCVZi	\N	t	2025-06-11 15:40:55.175503	\N	\N	\N	\N
\.


SELECT pg_catalog.setval('public.categorias_id_seq', 9, true);
SELECT pg_catalog.setval('public.clientes_id_seq', 16, true);
SELECT pg_catalog.setval('public.items_base_id_seq', 1, false);
SELECT pg_catalog.setval('public.items_en_presupuesto_id_seq', 160, true);
SELECT pg_catalog.setval('public.lugares_trabajo_id_seq', 45, true);
SELECT pg_catalog.setval('public.presupuestos_id_seq', 78, true);
SELECT pg_catalog.setval('public.usuarios_id_seq', 1, true);

----

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_nombre_key UNIQUE (nombre);
ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.clientes
    ADD CONSTRAINT clientes_alias_key UNIQUE (alias);
ALTER TABLE ONLY public.clientes
    ADD CONSTRAINT clientes_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.items_base
    ADD CONSTRAINT items_base_nombre_unidad_key UNIQUE (nombre, unidad);
ALTER TABLE ONLY public.items_base
    ADD CONSTRAINT items_base_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.items_en_presupuesto
    ADD CONSTRAINT items_en_presupuesto_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.lugares_trabajo
    ADD CONSTRAINT lugares_trabajo_nombre_key UNIQUE (nombre);
ALTER TABLE ONLY public.lugares_trabajo
    ADD CONSTRAINT lugares_trabajo_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.presupuestos
    ADD CONSTRAINT presupuestos_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_correo_electronico_key UNIQUE (correo_electronico);
ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_username_key UNIQUE (username);
ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_creado_por_fkey FOREIGN KEY (creado_por) REFERENCES public.usuarios(id);
ALTER TABLE ONLY public.clientes
    ADD CONSTRAINT clientes_creado_por_fkey FOREIGN KEY (creado_por) REFERENCES public.usuarios(id);
ALTER TABLE ONLY public.items_base
    ADD CONSTRAINT items_base_categoria_id_fkey FOREIGN KEY (categoria_id) REFERENCES public.categorias(id) ON DELETE RESTRICT;
ALTER TABLE ONLY public.items_en_presupuesto
    ADD CONSTRAINT items_en_presupuesto_categoria_id_fkey FOREIGN KEY (categoria_id) REFERENCES public.categorias(id) ON DELETE RESTRICT;
ALTER TABLE ONLY public.items_en_presupuesto
    ADD CONSTRAINT items_en_presupuesto_presupuesto_id_fkey FOREIGN KEY (presupuesto_id) REFERENCES public.presupuestos(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.lugares_trabajo
    ADD CONSTRAINT lugares_trabajo_creado_por_fkey FOREIGN KEY (creado_por) REFERENCES public.usuarios(id);
ALTER TABLE ONLY public.presupuestos
    ADD CONSTRAINT presupuestos_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.clientes(id) ON DELETE RESTRICT;
ALTER TABLE ONLY public.presupuestos
    ADD CONSTRAINT presupuestos_creado_por_fkey FOREIGN KEY (creado_por) REFERENCES public.usuarios(id);
ALTER TABLE ONLY public.presupuestos
    ADD CONSTRAINT presupuestos_lugar_trabajo_id_fkey FOREIGN KEY (lugar_trabajo_id) REFERENCES public.lugares_trabajo(id) ON DELETE RESTRICT;



