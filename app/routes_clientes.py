# app/routes_clientes.py
from collections import defaultdict

from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, current_app
from app import db_session
from app.models import Cliente, Destinatario, Lugar
from werkzeug.utils import secure_filename
import os
import uuid

clientes_bp = Blueprint("clientes_bp", __name__)

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp"}


# Agrega esta función para gestionar la carga de archivos
def guardar_logo(logo_file, cliente_id):
    if not logo_file or logo_file.filename == "":
        return None

    filename = secure_filename(logo_file.filename)
    # guardamos dentro de app/static/logos/
    abs_dir = current_app.config["UPLOAD_LOGOS"]  # <- OJO: esta key
    os.makedirs(abs_dir, exist_ok=True)

    new_name = f"cliente_{cliente_id}_{filename}"
    abs_path = os.path.join(abs_dir, new_name)
    logo_file.save(abs_path)

    # lo que guardas en BD debe ser RELATIVO a static/
    return f"logos/{new_name}"



@clientes_bp.route("/", endpoint="inicio")
def inicio():
    try:
        clientes_habilitados = (
            db_session.query(Cliente)
            .filter_by(activo=True)
            .order_by(Cliente.nombre)
            .all()
        )
        return render_template("index.html", clientes_habilitados=clientes_habilitados)
    except Exception as e:
        print("Error al cargar clientes en index:", e)
        return render_template("index.html", clientes_habilitados=[])


@clientes_bp.route("/clientes/<int:cliente_id>/destinatarios", endpoint="ver_destinatarios_cliente")
def ver_destinatarios_cliente(cliente_id):
    cliente = db_session.query(Cliente).get(cliente_id)
    if not cliente:
        abort(404)

    lugares_cliente = (
        db_session.query(Lugar)
        .filter_by(cliente_id=cliente_id)
        .order_by(Lugar.nombre)
        .all()
    )

    resultados = (
        db_session.query(Destinatario, Lugar)
        .outerjoin(Lugar, Destinatario.lugar_id == Lugar.id)
        .filter(Destinatario.cliente_id == cliente_id, Destinatario.activo.is_(True))
        .order_by(Lugar.nombre.nullsfirst(), Destinatario.tipo, Destinatario.nombre)
        .all()
    )

    grupos_destinatarios = defaultdict(list)
    for dest, lugar in resultados:
        nombre_lugar = lugar.nombre if lugar else "Consolidado / Sin lugar"
        grupos_destinatarios[nombre_lugar].append(dest)

    es_consolidado = cliente.modo_envio == "consolidado"

    return render_template(
        "destinatarios_cliente.html",
        cliente=cliente,
        grupos_destinatarios=grupos_destinatarios,
        es_consolidado=es_consolidado,
        lugares_cliente=lugares_cliente,
    )


@clientes_bp.route("/clientes/<int:cliente_id>/destinatarios/nuevo", methods=["GET", "POST"], endpoint="nuevo_destinatario")
def nuevo_destinatario(cliente_id):
    cliente = db_session.query(Cliente).get(cliente_id)
    if not cliente:
        abort(404)

    lugares = (
        db_session.query(Lugar)
        .filter_by(cliente_id=cliente_id, activo=True)
        .order_by(Lugar.nombre)
        .all()
    )

    if request.method == "POST":
        nombre = request.form.get("nombre") or None
        email = (request.form.get("email") or "").strip()
        tipo = (request.form.get("tipo") or "to").lower()
        lugar_id_raw = (request.form.get("lugar_id") or "").strip()

        lugar_id = None
        if lugar_id_raw and lugar_id_raw.lower() not in ("none", "null", "0"):
            try:
                lugar_id = int(lugar_id_raw)
            except ValueError:
                lugar_id = None

        if not email:
            flash("El correo es obligatorio.", "danger")
        else:
            try:
                dest = Destinatario(
                    email=email,
                    nombre=nombre,
                    tipo=tipo,
                    cliente_id=cliente.id,
                    lugar_id=lugar_id,
                    activo=True,
                )
                db_session.add(dest)
                db_session.commit()
                flash("Destinatario creado correctamente.", "success")
                return redirect(url_for("clientes_bp.ver_destinatarios_cliente", cliente_id=cliente.id))
            except Exception as e:
                db_session.rollback()
                print("Error al crear destinatario:", e)
                flash("No se pudo crear el destinatario.", "danger")

    return render_template(
        "form_destinatario.html",
        cliente=cliente,
        lugares=lugares,
        destinatario=None,
        titulo_form="Nuevo destinatario",
    )


@clientes_bp.route("/destinatarios/<int:destinatario_id>/editar", methods=["GET", "POST"], endpoint="editar_destinatario")
def editar_destinatario(destinatario_id):
    dest = db_session.query(Destinatario).get(destinatario_id)
    if not dest:
        abort(404)

    cliente = db_session.query(Cliente).get(dest.cliente_id)
    if not cliente:
        abort(404)

    lugares = (
        db_session.query(Lugar)
        .filter_by(cliente_id=cliente.id, activo=True)
        .order_by(Lugar.nombre)
        .all()
    )

    if request.method == "POST":
        nombre = request.form.get("nombre") or None
        email = (request.form.get("email") or "").strip()
        tipo = (request.form.get("tipo") or "to").lower()
        lugar_id_raw = (request.form.get("lugar_id") or "").strip()

        lugar_id = None
        if lugar_id_raw and lugar_id_raw.lower() not in ("none", "null", "0"):
            try:
                lugar_id = int(lugar_id_raw)
            except ValueError:
                lugar_id = None

        if not email:
            flash("El correo es obligatorio.", "danger")
        else:
            try:
                dest.nombre = nombre
                dest.email = email
                dest.tipo = tipo
                dest.lugar_id = lugar_id
                db_session.commit()
                flash("Destinatario actualizado correctamente.", "success")
                return redirect(url_for("clientes_bp.ver_destinatarios_cliente", cliente_id=cliente.id))
            except Exception as e:
                db_session.rollback()
                print("Error al editar destinatario:", e)
                flash("No se pudo actualizar el destinatario.", "danger")

    return render_template(
        "form_destinatario.html",
        cliente=cliente,
        lugares=lugares,
        destinatario=dest,
        titulo_form="Editar destinatario",
    )


@clientes_bp.route("/destinatarios/<int:destinatario_id>/eliminar", methods=["POST"], endpoint="eliminar_destinatario")
def eliminar_destinatario(destinatario_id):
    dest = db_session.query(Destinatario).get(destinatario_id)
    if not dest:
        abort(404)

    cliente_id = dest.cliente_id

    try:
        dest.activo = False
        db_session.commit()
        flash("Destinatario eliminado (inactivo).", "success")
    except Exception as e:
        db_session.rollback()
        print("Error al eliminar destinatario:", e)
        flash("No se pudo eliminar el destinatario.", "danger")

    return redirect(url_for("clientes_bp.ver_destinatarios_cliente", cliente_id=cliente_id))


@clientes_bp.route("/clientes/<int:cliente_id>/lugares/nuevo", methods=["POST"], endpoint="nuevo_lugar")
def nuevo_lugar(cliente_id):
    cliente = db_session.query(Cliente).get(cliente_id)
    if not cliente:
        abort(404)

    nombre = (request.form.get("nombre") or "").strip()
    codigo_interno = (request.form.get("codigo_interno") or "").strip() or None
    requiere_individual = bool(request.form.get("requiere_bitacora_individual"))

    if not nombre:
        flash("El nombre del lugar es obligatorio.", "danger")
        return redirect(url_for("clientes_bp.ver_destinatarios_cliente", cliente_id=cliente_id))

    try:
        lugar = Lugar(
            nombre=nombre,
            codigo_interno=codigo_interno,
            requiere_bitacora_individual=requiere_individual,
            cliente_id=cliente.id,
            activo=True,
        )
        db_session.add(lugar)
        db_session.commit()
        flash("Lugar creado correctamente.", "success")
    except Exception as e:
        db_session.rollback()
        print("Error al crear lugar:", e)
        flash("No se pudo crear el lugar.", "danger")

    return redirect(url_for("clientes_bp.ver_destinatarios_cliente", cliente_id=cliente_id))


@clientes_bp.route("/lugares/<int:lugar_id>/toggle-activo", methods=["POST"], endpoint="toggle_lugar_activo")
def toggle_lugar_activo(lugar_id):
    lugar = db_session.query(Lugar).get(lugar_id)
    if not lugar:
        abort(404)

    cliente_id = lugar.cliente_id

    try:
        lugar.activo = not lugar.activo
        db_session.commit()
        estado = "activado" if lugar.activo else "desactivado"
        flash(f"Lugar {estado} correctamente.", "success")
    except Exception as e:
        db_session.rollback()
        print("Error al cambiar estado del lugar:", e)
        flash("No se pudo cambiar el estado del lugar.", "danger")

    return redirect(url_for("clientes_bp.ver_destinatarios_cliente", cliente_id=cliente_id))

@clientes_bp.route("/lugares/<int:lugar_id>/toggle-individual", methods=["POST"], endpoint="toggle_lugar_individual")
def toggle_lugar_individual(lugar_id):
    lugar = db_session.query(Lugar).get(lugar_id)
    if not lugar:
        abort(404)

    cliente_id = lugar.cliente_id

    try:
        lugar.requiere_bitacora_individual = not lugar.requiere_bitacora_individual
        db_session.commit()

        estado = "activada" if lugar.requiere_bitacora_individual else "desactivada"
        flash(f"Bitácora individual {estado} para '{lugar.nombre}'.", "success")

    except Exception as e:
        db_session.rollback()
        print("Error al cambiar bitácora individual del lugar:", e)
        flash("No se pudo cambiar la bitácora individual del lugar.", "danger")

    return redirect(url_for("clientes_bp.ver_destinatarios_cliente", cliente_id=cliente_id))


@clientes_bp.route("/clientes/nuevo", methods=["GET", "POST"], endpoint="nuevo_cliente")
def nuevo_cliente():
    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        modo_envio = request.form.get("modo_envio") or "consolidado"
        activo = bool(request.form.get("activo"))

        logo_file = request.files.get("logo")  # name="logo" en el input
        print("LOGO FILE:", logo_file)
        print("LOGO FILENAME:", getattr(logo_file, "filename", None))

        if not nombre:
            flash("El nombre del cliente es obligatorio.", "danger")
            return render_template("form_cliente.html")

        try:
            # 1) crear cliente primero (para tener ID)
            cliente = Cliente(nombre=nombre, modo_envio=modo_envio, activo=activo, logo=None)
            db_session.add(cliente)
            db_session.commit()  # 👈 aquí ya existe cliente.id

            # 2) guardar logo y actualizar campo logo
            logo_rel = guardar_logo(logo_file, cliente.id)
            if logo_rel:
                cliente.logo = logo_rel
                db_session.commit()

            flash("Cliente creado correctamente.", "success")
            return redirect(url_for("clientes_bp.ver_destinatarios_cliente", cliente_id=cliente.id))

        except Exception as e:
            db_session.rollback()
            print("Error al crear cliente:", e)
            flash("No se pudo crear el cliente.", "danger")

    return render_template("form_cliente.html")


@clientes_bp.route("/modo-pruebas/toggle", methods=["POST"], endpoint="toggle_modo_pruebas")
def toggle_modo_pruebas():
    estado_actual = current_app.config.get("MODO_PRUEBAS", True)
    nuevo_estado = not estado_actual
    current_app.config["MODO_PRUEBAS"] = nuevo_estado

    mensaje = (
        "Modo PRUEBAS ACTIVADO (correos solo a Oscar)."
        if nuevo_estado
        else "Modo PRUEBAS DESACTIVADO (correos a clientes reales)."
    )
    flash(mensaje, "info")

    # Si hay referrer, vuelve ahí. Si no, al inicio del blueprint.
    return redirect(request.referrer or url_for("clientes_bp.inicio"))

@clientes_bp.route("/clientes/<int:cliente_id>/editar", methods=["GET", "POST"], endpoint="editar_cliente")
def editar_cliente(cliente_id):
    cliente = db_session.query(Cliente).get(cliente_id)
    if not cliente:
        abort(404)

    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        modo_envio = request.form.get("modo_envio") or "consolidado"
        activo = bool(request.form.get("activo"))

        logo_file = request.files.get("logo")

        if not nombre:
            flash("El nombre del cliente es obligatorio.", "danger")
            return render_template("form_cliente.html", cliente=cliente, modo="editar")

        try:
            cliente.nombre = nombre
            cliente.modo_envio = modo_envio
            cliente.activo = activo

            # Logo opcional (si suben uno nuevo, reemplaza el campo en BD)
            logo_rel = guardar_logo(logo_file, cliente.id)
            if logo_rel:
                cliente.logo = logo_rel

            db_session.commit()
            flash("Cliente actualizado correctamente.", "success")
            return redirect(url_for("clientes_bp.ver_destinatarios_cliente", cliente_id=cliente.id))

        except Exception as e:
            db_session.rollback()
            print("Error al editar cliente:", e)
            flash("No se pudo actualizar el cliente.", "danger")

    return render_template("form_cliente.html", cliente=cliente, modo="editar")

