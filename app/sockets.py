# app/sockets.py
from flask import request
from flask_socketio import join_room, emit
from app import socketio

# estado_salas = {
#   "bitacora_cliente_2": {"conectados": 2, "form": {}, "eventos": {}}
# }
estado_salas = {}


def _nombre_sala_actual():
    cliente_id = request.args.get("cliente_id")
    if cliente_id:
        return f"bitacora_cliente_{cliente_id}"
    return "bitacoras_global"


def _get_estado_sala(nombre_sala):
    if nombre_sala not in estado_salas:
        estado_salas[nombre_sala] = {"conectados": 0, "form": {}, "eventos": {}}
    return estado_salas[nombre_sala]


@socketio.on("connect")
def handle_connect():
    sala = _nombre_sala_actual()
    estado = _get_estado_sala(sala)

    estado["conectados"] += 1
    join_room(sala)

    emit("user_count", {"conectados": estado["conectados"]}, room=sala)

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

    emit("user_count", {"conectados": estado["conectados"]}, room=sala)


@socketio.on("evento_nuevo")
def handle_evento_nuevo(data):
    sala = _nombre_sala_actual()
    estado = _get_estado_sala(sala)

    row_id = data.get("id")
    row_data = data.get("row") or {}
    if not row_id:
        return

    row_data.setdefault("id", row_id)
    estado["eventos"][row_id] = row_data

    emit("evento_nuevo", row_data, room=sala, include_self=False)


@socketio.on("evento_update")
def handle_evento_update(data):
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
    sala = _nombre_sala_actual()
    estado = _get_estado_sala(sala)

    row_id = data.get("id")
    if not row_id:
        return

    estado["eventos"].pop(row_id, None)
    emit("evento_eliminar", {"id": row_id}, room=sala, include_self=False)


@socketio.on("form_update")
def handle_form_update(data):
    sala = _nombre_sala_actual()
    estado = _get_estado_sala(sala)

    estado["form"] = data or {}
    emit("form_update", data, room=sala, include_self=False)


# ==========================
# ✅ VACIAR BITÁCORA (NUEVO)
# ==========================
@socketio.on("bitacora_vaciar")
def handle_bitacora_vaciar(data=None):
    sala = _nombre_sala_actual()
    estado = _get_estado_sala(sala)

    estado["form"] = {}
    estado["eventos"] = {}

    emit("bitacora_vaciada", {"ok": True, "motivo": (data or {}).get("motivo", "manual")}, room=sala)


# (Opcional) útil si al POST OK quieres vaciar a todos automáticamente
@socketio.on("bitacora_enviada_ok")
def handle_bitacora_enviada_ok(data=None):
    sala = _nombre_sala_actual()
    estado = _get_estado_sala(sala)

    estado["form"] = {}
    estado["eventos"] = {}

    emit("bitacora_vaciada", {"ok": True, "motivo": "enviada_ok"}, room=sala)