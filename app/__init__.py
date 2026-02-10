# app/__init__.py
import os
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from flask_socketio import SocketIO

from app.config import DATABASE_URL, SECRET_KEY
from app.models import Base, Cliente

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["MODO_PRUEBAS"] = True

# ✅ carpeta física: app/static/logos
UPLOAD_LOGOS = os.path.join(app.root_path, "static", "logos")
os.makedirs(UPLOAD_LOGOS, exist_ok=True)
app.config["UPLOAD_LOGOS"] = UPLOAD_LOGOS  # 👈 ESTA ES LA KEY

socketio = SocketIO(app, cors_allowed_origins="*")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20
)
Base.metadata.bind = engine
SessionLocal = sessionmaker(bind=engine)
db_session = scoped_session(SessionLocal)

@app.context_processor
def inject_clientes_nav():
    try:
        clientes_consolidados = (
            db_session.query(Cliente)
            .filter_by(activo=True, modo_envio="consolidado")
            .order_by(Cliente.nombre)
            .all()
        )
        clientes_por_lugar = (
            db_session.query(Cliente)
            .filter_by(activo=True, modo_envio="por_lugar")
            .order_by(Cliente.nombre)
            .all()
        )
    except Exception as e:
        print("Error cargando clientes para navbar:", e)
        clientes_consolidados, clientes_por_lugar = [], []

    return dict(
        clientes_consolidados=clientes_consolidados,
        clientes_por_lugar=clientes_por_lugar,
        modo_pruebas=app.config.get("MODO_PRUEBAS", True),
    )

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

from app.routes_bitacoras import bitacoras_bp  # noqa
from app.routes_clientes import clientes_bp    # noqa
app.register_blueprint(bitacoras_bp)
app.register_blueprint(clientes_bp)

from app import sockets  # noqa
