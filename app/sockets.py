# app/sockets.py
from flask import request
from flask_socketio import join_room, emit

from app import socketio

# Estructura en memoria:
# estado_salas = {
#   "bitacora_cliente_2": {
#       "conectados": 2,
#       "form": {...},
#       "eventos": {
#           "rowId-1": {...},
#           "rowId-2": {...}
#       }
#   },
#   ...
# }
estado_salas = {}


def _nombre_sala_actual():
    """
    Usa el cliente_id enviado en la query del socket:
    io({ query: { cliente_id: '2' } })
    Si no viene, usa una sala global.
    """
    cliente_id = request.args.get("cliente_id")
    if cliente_id:
        return f"bitacora_cliente_{cliente_id}"
    return "bitacoras_global"


def _get_estado_sala(nombre_sala):
    if nombre_sala not in estado_salas:
        estado_salas[nombre_sala] = {
            "conectados": 0,
            "form": {},
            "eventos": {}
        }
    return estado_salas[nombre_sala]


# ========================
# CONEXIÓN / DESCONEXIÓN
# ========================
@socketio.on("connect")
def handle_connect():
    sala = _nombre_sala_actual()
    estado = _get_estado_sala(sala)

    estado["conectados"] += 1
    join_room(sala)

    print(f"🔌 Nuevo cliente conectado a {sala}. Total: {estado['conectados']}")

    # Avisar contador a todos en la sala
    emit("user_count", {"conectados": estado["conectados"]}, room=sala)

    # Enviar snapshot inicial SOLO al nuevo cliente
    snapshot = {
        "form": estado["form"],
        "eventos": list(estado["eventos"].values()),
    }
    emit("snapshot_inicial", snapshot)


@socketio.on("disconnect")
def handle_disconnect():
    sala = _nombre_sala_actual()
    estado = _get_estado_sala(sala)

    if estado["conectados"] > 0:
        estado["conectados"] -= 1

    print(f"🔌 Cliente desconectado de {sala}. Total: {estado['conectados']}")
    emit("user_count", {"conectados": estado["conectados"]}, room=sala)


# ========================
# EVENTOS DE BITÁCORA
# ========================

@socketio.on("evento_nuevo")
def handle_evento_nuevo(data):
    """
    data: { id, cliente_id, row_data? }
    """
    sala = _nombre_sala_actual()
    estado = _get_estado_sala(sala)

    row_id = data.get("id")
    row_data = data.get("row") or {}
    if not row_id:
        return

    row_data.setdefault("id", row_id)
    estado["eventos"][row_id] = row_data

    # Rebotar a todos MENOS al que lo envía
    emit("evento_nuevo", row_data, room=sala, include_self=False)


@socketio.on("evento_update")
def handle_evento_update(data):
    """
    data: { id, field, value }
    """
    sala = _nombre_sala_actual()
    estado = _get_estado_sala(sala)

    row_id = data.get("id")
    field = data.get("field")
    value = data.get("value")

    if not row_id or not field:
        return

    if row_id not in estado["eventos"]:
        estado["eventos"][row_id] = {"id": row_id}

    estado["eventos"][row_id][field] = value

    emit("evento_update", data, room=sala, include_self=False)


@socketio.on("evento_eliminar")
def handle_evento_eliminar(data):
    """
    data: { id }
    """
    sala = _nombre_sala_actual()
    estado = _get_estado_sala(sala)

    row_id = data.get("id")
    if not row_id:
        return

    estado["eventos"].pop(row_id, None)
    emit("evento_eliminar", {"id": row_id}, room=sala, include_self=False)


@socketio.on("form_update")
def handle_form_update(data):
    """
    data: {
      operadores: [ids],
      horario: str,
      fecha_inicio: str,
      fecha_fin: str
    }
    """
    sala = _nombre_sala_actual()
    estado = _get_estado_sala(sala)

    estado["form"] = data or {}

    emit("form_update", data, room=sala, include_self=False)
