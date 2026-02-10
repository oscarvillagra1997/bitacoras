import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# --- Configuración de Flask ---
# Si no encuentra SECRET_KEY en el .env, usará el valor por defecto
SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-provisional-12345")

# --- Configuración de la base de datos ---
# Aquí se cargará tu cadena de conexión (MySQL, SQLite, etc.)
DATABASE_URL = os.getenv("DATABASE_URL")

# --- Configuración de Archivos y Carpetas ---
# Definimos la carpeta de bitácoras (puedes cambiarla en el .env)
BITACORAS_FOLDER = os.getenv("BITACORAS_FOLDER", "bitacoras")

# Crear la carpeta automáticamente si no existe al iniciar la app
if not os.path.exists(BITACORAS_FOLDER):
    os.makedirs(BITACORAS_FOLDER)
    print(f"Directorio creado: {BITACORAS_FOLDER}")

# Opcional: Configuración para subida de imágenes (CCTV/Evidencias)
# UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app/static/img/clientes')