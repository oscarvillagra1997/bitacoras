# app/__init__.py
import os
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager


from app.config import DATABASE_URL, SECRET_KEY
from app.models import Base, Cliente, Operador

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["MODO_PRUEBAS"] = True

login_manager = LoginManager()
login_manager.login_view = "auth_bp.login"  # endpoint del login
login_manager.init_app(app)

# Importante si estás detrás de Nginx (headers forwarded)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

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

@login_manager.user_loader
def load_user(user_id):
    try:
        return db_session.get(Operador, int(user_id))
    except Exception:
        return None

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
app.register_blueprint(clientes_bp)
app.register_blueprint(bitacoras_bp)

from app import sockets  # noqa
