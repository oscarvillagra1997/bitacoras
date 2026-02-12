from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Date,
    Text
)
from sqlalchemy.orm import relationship, declarative_base
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


# ===========================================
# 1. CLIENTES
# ===========================================
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), nullable=False)
    modo_envio = Column(String(20), nullable=False, default="consolidado")  # 'consolidado' | 'por_lugar'
    activo = Column(Boolean, nullable=False, default=True)
    logo = Column(String(255), nullable=True)  # Nueva columna para el logo

    # Relaciones
    lugares = relationship("Lugar", back_populates="cliente", cascade="all, delete-orphan")
    destinatarios = relationship("Destinatario", back_populates="cliente")

    def __repr__(self):
        return f"<Cliente {self.id} {self.nombre}>"


# ===========================================
# 2. LUGARES
# ===========================================
class Lugar(Base):
    __tablename__ = "lugares"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String(150), nullable=False)
    codigo_interno = Column(String(100))
    requiere_bitacora_individual = Column(Boolean, default=False)
    activo = Column(Boolean, nullable=False, default=True)

    # Relaciones
    cliente = relationship("Cliente", back_populates="lugares")
    destinatarios = relationship("Destinatario", back_populates="lugar")

    def __repr__(self):
        return f"<Lugar {self.id} {self.nombre}>"


# ===========================================
# 3. DESTINATARIOS
# ===========================================
class Destinatario(Base):
    __tablename__ = "destinatarios"

    id = Column(Integer, primary_key=True)
    email = Column(String(200), nullable=False)
    nombre = Column(String(150))
    tipo = Column(String(10), nullable=False, default="to")  # 'to' | 'cc' | 'bcc'
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"))
    lugar_id = Column(Integer, ForeignKey("lugares.id", ondelete="CASCADE"))
    activo = Column(Boolean, nullable=False, default=True)

    # Relaciones
    cliente = relationship("Cliente", back_populates="destinatarios")
    lugar = relationship("Lugar", back_populates="destinatarios")

    def __repr__(self):
        return f"<Destinatario {self.id} {self.email}>"


# ===========================================
# 4. OPERADORES
# ===========================================
class Operador(Base, UserMixin):
    __tablename__ = "operadores"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(150), unique=True)  # recomendable unique
    rol = Column(String(50))
    activo = Column(Boolean, nullable=False, default=True)

    password_hash = Column(String(255), nullable=True)  # 👈 NUEVO

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Operador {self.id} {self.nombre}>"


# ===========================================
# 5. TIPOS DE EVENTO (CATÁLOGO)
# ===========================================
class TipoEvento(Base):
    __tablename__ = "tipos_evento"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text)
    categoria = Column(String(100))
    activo = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<TipoEvento {self.id} {self.nombre}>"


# ===========================================
# 6. (OPCIONAL) META BITÁCORAS
# ===========================================
class BitacoraMeta(Base):
    __tablename__ = "bitacoras_meta"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)

    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    horario = Column(String(100))

    num_eventos = Column(Integer)
    ruta_pdf = Column(Text)
    enviada_a = Column(Text)

    creada_por = Column(Integer, ForeignKey("operadores.id"))
    fecha_envio = Column(Date)

    def __repr__(self):
        return f"<BitacoraMeta {self.id} cliente={self.cliente_id}>"
