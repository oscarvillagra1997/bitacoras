import os

# Configuración de Flask
SECRET_KEY = "super_secret_key"

# Configuración de la base de datos
DATABASE_URL = "postgresql://bitacoras:Labo0123@localhost:5432/bitacorasDB2"

#UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app/static/img/clientes')

# Carpeta raíz para las bitácoras
BITACORAS_FOLDER = "bitacoras"
if not os.path.exists(BITACORAS_FOLDER):
    os.makedirs(BITACORAS_FOLDER)