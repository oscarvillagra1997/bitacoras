from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Cliente, Lugar, Destinatario, Operador, TipoEvento

# Configuración de la base de datos
DATABASE_URL = "postgresql://bitacoras:Labo0123@localhost:5432/bitacorasDB2"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Crear tablas si no existen
Base.metadata.create_all(engine)


def poblar_bd():
    try:
        print("Inicializando la base de datos...")

        # -------------------------------
        # CLIENTES
        # -------------------------------
        if session.query(Cliente).count() == 0:
            print("Insertando clientes...")
            clientes = [
                Cliente(nombre="Nueva Atacama", modo_envio="por_lugar"),
                Cliente(nombre="MultiX", modo_envio="consolidado"),
                Cliente(nombre="Parque Industrial Lautaro", modo_envio="consolidado")
            ]
            session.add_all(clientes)

        session.commit()

        # Necesitamos IDs recién creados
        nueva_atacama = session.query(Cliente).filter_by(nombre="Nueva Atacama").first()
        multix = session.query(Cliente).filter_by(nombre="MultiX").first()
        parque_industrial = session.query(Cliente).filter_by(nombre="Parque Industrial Lautaro").first()

        # -------------------------------
        # LUGARES
        # -------------------------------
        if session.query(Lugar).count() == 0:
            print("Insertando lugares...")

            lugares = [
                # Nueva Atacama (bitácora por lugar)
                Lugar(cliente_id=nueva_atacama.id, nombre="PTAS Copiapó", codigo_interno="PTAS-01", requiere_bitacora_individual=True),
                Lugar(cliente_id=nueva_atacama.id, nombre="PTAS Tierra Amarilla", codigo_interno="PTAS-02", requiere_bitacora_individual=True),
                Lugar(cliente_id=nueva_atacama.id, nombre="Estanque Rosario", codigo_interno="EST-01", requiere_bitacora_individual=True),

                # MultiX (consolidado)
                Lugar(cliente_id=multix.id, nombre="Centro Ganso", codigo_interno="CTR-GAN"),
                Lugar(cliente_id=multix.id, nombre="Centro Yelén", codigo_interno="CTR-YEL")
            ]
            session.add_all(lugares)

        session.commit()

        # -------------------------------
        # OPERADORES
        # -------------------------------
        if session.query(Operador).count() == 0:
            print("Insertando operadores...")

            operadores = [
                Operador(nombre="Oscar Villagra", email="oscar.villagra@ctr.cl", rol="Administrador"),
                Operador(nombre="Carlos Muñoz", email="carlos.munoz@ctr.cl", rol="Operador"),
                Operador(nombre="Jorge Ortiz", email="jorge.ortiz@ctr.cl", rol="Operador"),
                Operador(nombre="Nicole Fernández", email="nicole.fernandez@ctr.cl", rol="Supervisor"),
                Operador(nombre="Ana Soto", email="ana.soto@ctr.cl", rol="Operador"),
                Operador(nombre="Luis Ramírez", email="luis.ramirez@ctr.cl", rol="Operador"),
                Operador(nombre="Marcela Paredes", email="marcela.paredes@ctr.cl", rol="Operador"),
                Operador(nombre="Pedro Aguilera", email="pedro.aguilera@ctr.cl", rol="Operador"),
            ]
            session.add_all(operadores)

        # -------------------------------
        # TIPOS DE EVENTO
        # -------------------------------
        if session.query(TipoEvento).count() == 0:
            print("Insertando tipos de evento...")

            tipos = [
                TipoEvento(nombre="Ingreso vehículo", categoria="Vehicular"),
                TipoEvento(nombre="Salida vehículo", categoria="Vehicular"),
                TipoEvento(nombre="Ingreso persona", categoria="Personal"),
                TipoEvento(nombre="Salida persona", categoria="Personal"),
                TipoEvento(nombre="Actividad sospechosa", categoria="Alarma"),
                TipoEvento(nombre="Sensor activado", categoria="Alarma"),
                TipoEvento(nombre="Cámara sin conexión", categoria="Técnico"),
                TipoEvento(nombre="Movimiento detectado", categoria="Analítica"),
                TipoEvento(nombre="Apoyo operativo", categoria="Gestión"),
                TipoEvento(nombre="Observación general", categoria="General"),
            ]
            session.add_all(tipos)

        session.commit()

        # -------------------------------
        # DESTINATARIOS
        # -------------------------------
        if session.query(Destinatario).count() == 0:
            print("Insertando destinatarios...")

            # Obtener lugares ya insertados
            ptas_copiapo = session.query(Lugar).filter_by(nombre="PTAS Copiapó").first()
            ptas_ta = session.query(Lugar).filter_by(nombre="PTAS Tierra Amarilla").first()
            estanque_rosario = session.query(Lugar).filter_by(nombre="Estanque Rosario").first()
            ganso = session.query(Lugar).filter_by(nombre="Centro Ganso").first()
            yelen = session.query(Lugar).filter_by(nombre="Centro Yelén").first()

            destinatarios = [

                # Nivel cliente - Nueva Atacama
                Destinatario(email="control.cctv@nuevaatacama.cl", nombre="Control CCTV Nueva Atacama", tipo="to", cliente_id=nueva_atacama.id),
                Destinatario(email="seguridad@nuevaatacama.cl", nombre="Seguridad Nueva Atacama", tipo="cc", cliente_id=nueva_atacama.id),

                # Nivel cliente - MultiX
                Destinatario(email="centro.operaciones@multix.cl", nombre="Centro de Operaciones MultiX", tipo="to", cliente_id=multix.id),
                Destinatario(email="seguridad@multix.cl", nombre="Departamento Seguridad", tipo="cc", cliente_id=multix.id),

                # Por lugar - Nueva Atacama
                Destinatario(email="jefe.copiapo@nuevaatacama.cl", nombre="Jefe PTAS Copiapó", tipo="to", cliente_id=nueva_atacama.id, lugar_id=ptas_copiapo.id),
                Destinatario(email="operaciones.copiapo@nuevaatacama.cl", nombre="Operaciones Copiapó", tipo="cc", cliente_id=nueva_atacama.id, lugar_id=ptas_copiapo.id),

                Destinatario(email="jefe.ta@nuevaatacama.cl", nombre="Jefe Tierra Amarilla", tipo="to", cliente_id=nueva_atacama.id, lugar_id=ptas_ta.id),
                Destinatario(email="operaciones.ta@nuevaatacama.cl", nombre="Operaciones Tierra Amarilla", tipo="cc", cliente_id=nueva_atacama.id, lugar_id=ptas_ta.id),

                Destinatario(email="jefe.rosario@nuevaatacama.cl", nombre="Jefe Estanque Rosario", tipo="to", cliente_id=nueva_atacama.id, lugar_id=estanque_rosario.id),
                Destinatario(email="operaciones.rosario@nuevaatacama.cl", nombre="Operaciones Rosario", tipo="cc", cliente_id=nueva_atacama.id, lugar_id=estanque_rosario.id),
            ]

            session.add_all(destinatarios)

        session.commit()
        print("Base de datos inicializada correctamente.")

    except Exception as e:
        session.rollback()
        print(f"Error al inicializar la base de datos: {e}")

    finally:
        session.close()



# Ejecutar la inicialización solo si se ejecuta directamente
if __name__ == "__main__":
    poblar_bd()
