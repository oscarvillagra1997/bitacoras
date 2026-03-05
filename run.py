# run.py
from app import app, socketio
from werkzeug.middleware.dispatcher import DispatcherMiddleware

if __name__ == "__main__":
    # Para pruebas locales seguirá funcionando en el puerto 5000
    socketio.run(app, host="0.0.0.0", port=5000)