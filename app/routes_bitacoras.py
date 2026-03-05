# app/routes_bitacoras.py
from datetime import datetime
from collections import defaultdict

from flask import Blueprint, request, render_template, redirect, url_for, flash
from app import db_session
from app.models import Operador, Lugar, TipoEvento, Cliente
from app.config import BITACORAS_FOLDER
from app.utils import generar_pdf_por_lugar, enviar_correo_bitacora_html

# 👇 ESTE ES EL BLUEPRINT QUE ESTÁ BUSCANDO __init__.py
bitacoras_bp = Blueprint("bitacoras_bp", __name__)


@bitacoras_bp.route("/crear-bitacora", methods=["GET", "POST"], endpoint="crear_bitacora")
def crear_bitacora():
    if request.method == "POST":
        try:
            # ================================
            # 1) Datos generales del formulario
            # ================================
            operadores_ids = request.form.getlist("operadores[]")
            horario = request.form["horario"]
            fecha_inicio = datetime.strptime(request.form["fecha_inicio"], "%Y-%m-%d").date()
            fecha_fin = datetime.strptime(request.form["fecha_fin"], "%Y-%m-%d").date()
            cliente_id = request.form.get("cliente_id", type=int)

            cliente = db_session.query(Cliente).get(cliente_id)
            nombre_cliente = cliente.nombre if cliente else "Cliente"
            modo_envio = cliente.modo_envio if cliente else "consolidado"

            # Operadores desde BD
            operadores = []
            if operadores_ids:
                operadores = (
                    db_session.query(Operador)
                    .filter(Operador.id.in_([int(o) for o in operadores_ids]))
                    .all()
                )

            # ================================
            # 2) Eventos – se agrupan por objeto Lugar
            # ================================
            lugares_ids = request.form.getlist("lugares[]")
            camaras = request.form.getlist("camaras[]")
            horas_evento = request.form.getlist("horas_evento[]")
            tipos_evento_ids = request.form.getlist("tipos_evento[]")
            observaciones = request.form.getlist("observaciones[]")

            eventos_por_lugar = defaultdict(list)

            for i in range(len(lugares_ids)):
                if not lugares_ids[i]:
                    continue

                lugar_obj = db_session.query(Lugar).get(int(lugares_ids[i]))
                if not lugar_obj:
                    flash(f"Lugar inválido en fila {i+1}.", "danger")
                    return redirect(url_for("bitacoras_bp.crear_bitacora"))

                tipo_evento_obj = None
                if tipos_evento_ids[i]:
                    tipo_evento_obj = db_session.query(TipoEvento).get(int(tipos_evento_ids[i]))

                evento_data = {
                    "lugar": lugar_obj.nombre,
                    "camara": camaras[i],
                    "hora": horas_evento[i],
                    "tipo": (tipo_evento_obj.nombre if tipo_evento_obj else ""),  # 👈 AGREGAR
                    "observaciones": observaciones[i],
                }

                eventos_por_lugar[lugar_obj].append(evento_data)

            # ================================
            # 3) Bitácora efímera
            # ================================
            class BitacoraSimple:
                def __init__(self, horario, fecha_inicio, fecha_fin, usuarios, cliente_id):
                    self.horario = horario
                    self.fecha_inicio = fecha_inicio
                    self.fecha_fin = fecha_fin
                    self.usuarios = usuarios
                    self.cliente_id = cliente_id

            nueva_bitacora = BitacoraSimple(
                horario=horario,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                usuarios=operadores,
                cliente_id=cliente_id,
            )

            # ================================
            # 4) Generar PDFs según modo_envio
            # ================================
            if modo_envio == "por_lugar":
                # Un PDF por lugar (ej: Nueva Atacama)
                pdf_paths = generar_pdf_por_lugar(
                    bitacora=nueva_bitacora,
                    eventos_por_lugar=eventos_por_lugar,
                    carpeta_base=BITACORAS_FOLDER,
                    nombre_cliente=nombre_cliente,
                    cliente_obj=cliente,   # 👈 AGREGAR
                )

                for lugar_obj, ruta_pdf in pdf_paths.items():
                    enviar_correo_bitacora_html(
                        session=db_session,
                        nueva_bitacora=nueva_bitacora,
                        lugar_obj=lugar_obj,
                        pdf_path=ruta_pdf,
                    )

            else:
                # CONSOLIDADO (ej: MultiX)
                eventos_consolidados = []
                for lista in eventos_por_lugar.values():
                    eventos_consolidados.extend(lista)

                eventos_dict = {"Consolidado": eventos_consolidados}

                pdf_paths = generar_pdf_por_lugar(
                    bitacora=nueva_bitacora,
                    eventos_por_lugar=eventos_dict,
                    carpeta_base=BITACORAS_FOLDER,
                    nombre_cliente=nombre_cliente,
                    cliente_obj=cliente,   # 👈 AGREGAR
                )

                # Solo una entrada
                _, ruta_pdf = next(iter(pdf_paths.items()))

                enviar_correo_bitacora_html(
                    session=db_session,
                    nueva_bitacora=nueva_bitacora,
                    lugar_obj=None,  # consolidado
                    pdf_path=ruta_pdf,
                )

            flash("Bitácora creada y correos procesados correctamente.", "success")
            return redirect(url_for("bitacoras_bp.crear_bitacora"))

        except Exception as e:
            print("❌ Error al crear la bitácora:", e)
            db_session.rollback()
            flash("Hubo un error al crear o enviar la bitácora.", "danger")
            return redirect(url_for("bitacoras_bp.crear_bitacora"))

    # ================================
    # GET: cargar catálogos para el formulario
    # ================================
    cliente_id_preseleccionado = request.args.get("cliente_id", type=int)

    clientes = db_session.query(Cliente).filter_by(activo=True).all()
    operadores = db_session.query(Operador).filter_by(activo=True).all()
    eventos = db_session.query(TipoEvento).filter_by(activo=True).all()

    cliente_actual = None
    if cliente_id_preseleccionado:
        cliente_actual = db_session.get(Cliente, cliente_id_preseleccionado)

    return render_template(
        "crear_bitacora.html",
        clientes=clientes,
        operadores=operadores,
        eventos=eventos,
        cliente_id_preseleccionado=cliente_id_preseleccionado,
        cliente_actual=cliente_actual,
    )


@bitacoras_bp.route("/api/lugares/<int:cliente_id>", endpoint="api_lugares")
def api_lugares(cliente_id):
    try:
        lugares = (
            db_session.query(Lugar)
            .filter_by(cliente_id=cliente_id, activo=True)
            .order_by(Lugar.nombre)
            .all()
        )

        return {"lugares": [{"id": l.id, "nombre": l.nombre} for l in lugares]}
    except Exception as e:
        print("Error en API /api/lugares:", e)
        return {"lugares": []}, 500

