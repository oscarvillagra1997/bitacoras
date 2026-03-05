---------------------------------------------------------
-- INSERTS BASE PARA CLIENTES, LUGARES, OPERADORES,
-- TIPOS DE EVENTO Y DESTINATARIOS
---------------------------------------------------------

-----------------------------
-- 1) CLIENTES
-----------------------------
INSERT INTO clientes (nombre, modo_envio)
VALUES
('Nueva Atacama', 'por_lugar'),
('MultiX', 'consolidado');


-----------------------------
-- 2) LUGARES
-----------------------------
INSERT INTO lugares (cliente_id, nombre, codigo_interno, requiere_bitacora_individual)
VALUES
-- Nueva Atacama (bitácora por lugar)
(1, 'PTAS Copiapó', 'PTAS-01', TRUE),
(1, 'PTAS Tierra Amarilla', 'PTAS-02', TRUE),
(1, 'Estanque Rosario', 'EST-01', TRUE),

-- MultiX (consolidado)
(2, 'Centro Ganso', 'CTR-GAN', FALSE),
(2, 'Centro Yelén', 'CTR-YEL', FALSE);


-----------------------------
-- 3) OPERADORES
-----------------------------
INSERT INTO operadores (nombre, email, rol)
VALUES
('Oscar Villagra', 'oscar.villagra@ctr.cl', 'Administrador'),
('Carlos Muñoz', 'carlos.munoz@ctr.cl', 'Operador'),
('Jorge Ortiz', 'jorge.ortiz@ctr.cl', 'Operador'),
('Nicole Fernández', 'nicole.fernandez@ctr.cl', 'Supervisor'),
('Ana Soto', 'ana.soto@ctr.cl', 'Operador'),
('Luis Ramírez', 'luis.ramirez@ctr.cl', 'Operador'),
('Marcela Paredes', 'marcela.paredes@ctr.cl', 'Operador'),
('Pedro Aguilera', 'pedro.aguilera@ctr.cl', 'Operador');


-----------------------------
-- 4) TIPOS DE EVENTO
-----------------------------
INSERT INTO tipos_evento (nombre, descripcion, categoria)
VALUES
('Ingreso vehículo', 'Ingreso normal registrado por cámara', 'Vehicular'),
('Salida vehículo', 'Salida normal registrada por cámara', 'Vehicular'),
('Ingreso persona', 'Acceso de persona sin anomalías', 'Personal'),
('Salida persona', 'Salida de persona sin anomalías', 'Personal'),
('Actividad sospechosa', 'Persona o vehículo fuera de horario permitido', 'Alarma'),
('Sensor activado', 'Evento generado por sensor físico', 'Alarma'),
('Cámara sin conexión', 'Pérdida de señal de cámara', 'Técnico'),
('Movimiento detectado', 'Detección por analítica', 'Analítica'),
('Apoyo operativo', 'Interacción necesaria del operador', 'Gestión'),
('Observación general', 'Nota o comentario importante', 'General');


-----------------------------
-- 5) DESTINATARIOS NIVEL CLIENTE
-----------------------------
-- Nueva Atacama (Cliente 1)
INSERT INTO destinatarios (email, nombre, tipo, cliente_id)
VALUES
('control.cctv@nuevaatacama.cl', 'Control CCTV Nueva Atacama', 'to', 1),
('seguridad@nuevaatacama.cl', 'Seguridad Nueva Atacama', 'cc', 1);

-- MultiX (Cliente 2)
INSERT INTO destinatarios (email, nombre, tipo, cliente_id)
VALUES
('centro.operaciones@multix.cl', 'Centro de Operaciones MultiX', 'to', 2),
('seguridad@multix.cl', 'Departamento Seguridad', 'cc', 2);


-----------------------------
-- 6) DESTINATARIOS POR LUGAR
-----------------------------
-- PTAS Copiapó
INSERT INTO destinatarios (email, nombre, tipo, cliente_id, lugar_id)
VALUES
('jefe.copiapo@nuevaatacama.cl', 'Jefe PTAS Copiapó', 'to', 1, 1),
('operaciones.copiapo@nuevaatacama.cl', 'Operaciones Copiapó', 'cc', 1, 1);

-- PTAS Tierra Amarilla
INSERT INTO destinatarios (email, nombre, tipo, cliente_id, lugar_id)
VALUES
('jefe.ta@nuevaatacama.cl', 'Jefe Tierra Amarilla', 'to', 1, 2),
('operaciones.ta@nuevaatacama.cl', 'Operaciones Tierra Amarilla', 'cc', 1, 2);

-- Estanque Rosario
INSERT INTO destinatarios (email, nombre, tipo, cliente_id, lugar_id)
VALUES
('jefe.rosario@nuevaatacama.cl', 'Jefe Estanque Rosario', 'to', 1, 3),
('operaciones.rosario@nuevaatacama.cl', 'Operaciones Rosario', 'cc', 1, 3);
