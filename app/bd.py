from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Time, Text, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Base de datos y conexión
DATABASE_URL = "postgresql://bitacoras:Labo0123@168.196.184.202:5432/bitacorasDB"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Tabla intermedia para la relación muchos a muchos entre bitacoras y usuarios
bitacoras_usuarios = Table(
    'bitacoras_usuarios', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('bitacora_id', Integer, ForeignKey('bitacoras.id', ondelete='CASCADE')),
    Column('usuario_id', Integer, ForeignKey('usuarios.id', ondelete='CASCADE'))
)

# Tabla Usuarios
class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    rol = Column(String(50), default='operador')  # operador o administrador
    created_at = Column(Text, default='NOW()')

# Tabla Lugares
class Lugar(Base):
    __tablename__ = 'lugares'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False, unique=True)

# Tabla Eventos Estandar
class EventoEstandar(Base):
    __tablename__ = 'eventos_estandar'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False, unique=True)

# Tabla Bitacoras
class Bitacora(Base):
    __tablename__ = 'bitacoras'
    id = Column(Integer, primary_key=True)
    fecha = Column(Date, nullable=False)
    horario = Column(String(20), nullable=False)
    created_at = Column(Text, default='NOW()')

    # Relación con usuarios a través de bitacoras_usuarios
    usuarios = relationship("Usuario", secondary=bitacoras_usuarios, backref="bitacoras")

# Tabla Eventos
class Evento(Base):
    __tablename__ = 'eventos'
    id = Column(Integer, primary_key=True)
    bitacora_id = Column(Integer, ForeignKey('bitacoras.id', ondelete='CASCADE'), nullable=False)
    lugar_id = Column(Integer, ForeignKey('lugares.id'), nullable=False)
    camara = Column(String(255), nullable=False)
    hora = Column(Time, nullable=False)
    evento_cid = Column(Integer, ForeignKey('eventos_estandar.id'), nullable=False)
    observaciones = Column(Text)

    # Relación con otras tablas
    bitacora = relationship("Bitacora", backref="eventos")
    lugar = relationship("Lugar", backref="eventos")
    evento_estandar = relationship("EventoEstandar", backref="eventos")

# Crear todas las tablas
if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Base de datos y tablas creadas exitosamente.")