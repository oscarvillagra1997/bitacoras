from weasyprint import HTML
import os
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage

from flask import current_app
from app.models import Destinatario, Cliente
from markupsafe import escape


# ========================
#  HELPERS MODO PRUEBAS
# ========================

CORREO_PRUEBAS = "oscar.villagra@ctr.cl"


def is_modo_pruebas():
    """
    Lee el modo pruebas desde la configuración global de Flask.
    Si no está seteado, por defecto True (para que no salga nada a clientes sin querer).
    """
    return current_app.config.get("MODO_PRUEBAS", True)


# ============================================================
#  PDF POR LUGAR (o consolidado)
# ============================================================
def generar_pdf_por_lugar(bitacora, eventos_por_lugar, carpeta_base, nombre_cliente="", cliente_obj=None):
    pdf_paths = {}

    operadores = [usuario.nombre for usuario in bitacora.usuarios]
    if operadores:
        operadores_str = "<ul>" + "".join(f"<li>{escape(op)}</li>" for op in operadores) + "</ul>"
    else:
        operadores_str = "No especificados"

    fecha_inicio = bitacora.fecha_inicio.strftime("%d-%m-%Y")
    fecha_fin    = bitacora.fecha_fin.strftime("%d-%m-%Y")

    cliente_display = nombre_cliente or (cliente_obj.nombre if cliente_obj else "Cliente")
    cliente_slug    = (cliente_display or "Cliente").replace(" ", "_")

    # =========================================================
    # ✅ LOGO: usar root_path + base_url (NO file:///)
    # =========================================================
    def resolver_logo_src():
        # Fallback CTR (debe existir en app/static/img/logo_ctr.png)
        fallback_rel = "static/img/logo_ctr.png"

        # Si no hay cliente o no hay logo guardado
        if not cliente_obj or not getattr(cliente_obj, "logo", None):
            return fallback_rel

        logo_raw = (cliente_obj.logo or "").strip().replace("\\", "/")

        # Esperado en BD: "logos/cliente_5_algo.png"
        # Si viene "static/logos/..." también lo soportamos
        if logo_raw.startswith("static/"):
            rel = logo_raw                      # "static/logos/..."
        else:
            rel = "static/" + logo_raw.lstrip("/")  # "static/logos/..."

        abs_candidate = os.path.join(current_app.root_path, rel)
        if os.path.exists(abs_candidate):
            return rel

        # Si el archivo no existe, usa fallback
        return fallback_rel

    logo_src = resolver_logo_src()
    print("LOGO BD:", getattr(cliente_obj, "logo", None))
    print("LOGO RESUELTO:", logo_src)
    print("EXISTS?:", os.path.exists(os.path.join(current_app.root_path, logo_src)))
    print("ROOT:", current_app.root_path)
    # =========================================================

    def get_campo(evento, campo):
        if hasattr(evento, campo):
            return getattr(evento, campo) or ""

        if isinstance(evento, dict):
            claves_posibles = {
                "lugar": ["lugar", "Lugar"],
                "camara": ["camara", "Cámara", "camera"],
                "hora": ["hora", "Hora", "Hora Evento"],
                "tipo": ["tipo", "tipo_evento", "Tipo de Evento"],
                "observaciones": ["observaciones", "Observaciones"],
            }.get(campo, [])

            for k in claves_posibles:
                if k in evento and evento[k]:
                    return evento[k]

            # ✅ CLAVE: si es dict y quieres "tipo", leer evento_estandar
                if campo == "tipo":
                    ev = evento.get("evento_estandar")
                    if ev and getattr(ev, "nombre", None):
                        return ev.nombre

            return ""

    for lugar_key, eventos in eventos_por_lugar.items():
        if hasattr(lugar_key, "nombre"):
            lugar_obj = lugar_key
            lugar = lugar_obj.nombre
        else:
            lugar_obj = None
            lugar = str(lugar_key)

        es_consolidado = (lugar_obj is None and lugar == "Consolidado")

        lugar_folder_name = lugar.replace(" ", "_")
        nombre_pdf = f"Bitacora_{cliente_slug}_{lugar_folder_name}_{fecha_inicio}_y_{fecha_fin}.pdf"

        lugar_folder = os.path.join(carpeta_base, lugar_folder_name)
        os.makedirs(lugar_folder, exist_ok=True)
        ruta_pdf = os.path.join(lugar_folder, nombre_pdf)

        try:
            if es_consolidado:
                eventos_ordenados = sorted(eventos, key=lambda e: (get_campo(e, "lugar"), get_campo(e, "hora")))
            else:
                eventos_ordenados = list(eventos)

            filas_html = []
            for i, evento in enumerate(eventos_ordenados):
                lugar_evt = escape(get_campo(evento, "lugar"))
                camara    = escape(get_campo(evento, "camara"))
                hora      = escape(get_campo(evento, "hora"))
                tipo      = escape(get_campo(evento, "tipo") or "Sin tipo")
                obs       = escape(get_campo(evento, "observaciones"))

                color_fila = "#ffffff" if i % 2 == 0 else "#e9ecef"

                if es_consolidado:
                    fila = (
                        f'<tr style="background-color: {color_fila};">'
                        f'<td style="padding: 10px; border: 1px solid #ddd; text-align: left;">{lugar_evt}</td>'
                        f'<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{camara}</td>'
                        f'<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{hora}</td>'
                        f'<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{tipo}</td>'
                        f'<td style="padding: 10px; border: 1px solid #ddd; text-align: left;">{obs}</td>'
                        f'</tr>'
                    )
                else:
                    fila = (
                        f'<tr style="background-color: {color_fila};">'
                        f'<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{camara}</td>'
                        f'<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{hora}</td>'
                        f'<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{tipo}</td>'
                        f'<td style="padding: 10px; border: 1px solid #ddd; text-align: left;">{obs}</td>'
                        f'</tr>'
                    )
                filas_html.append(fila)

            if es_consolidado:
                thead_html = """
                <thead>
                    <tr style="background-color: #343a40; color: white; text-align: left;">
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">📍 Lugar</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">📷 Cámara</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">🕒 Hora</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">📌 Tipo de Evento</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">✍️ Observaciones</th>
                    </tr>
                </thead>
                """
            else:
                thead_html = """
                <thead>
                    <tr style="background-color: #343a40; color: white; text-align: left;">
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">📷 Cámara</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">🕒 Hora</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">📌 Tipo de Evento</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">✍️ Observaciones</th>
                    </tr>
                </thead>
                """

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    @page {{
                        size: A4;
                        margin: 20mm 15mm 30mm 15mm;
                        @bottom-left {{ content: "Página " counter(page) " de " counter(pages); font-size: 10px; color: #333; }}
                        @bottom-center {{ content: "{escape(cliente_display)} - {escape(lugar)}"; font-size: 10px; font-weight: bold; text-align: center; color: #333; }}
                        @bottom-right {{ content: "Seguridad Electrónica - CTR"; font-size: 10px; color: #333; }}
                    }}
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    h1, h2, h3 {{ color: #333; text-align: center; }}
                    .header {{ margin-bottom: 12px; margin-top: 10px; text-align: center; }}
                    .logo {{max-width: 320px; max-height: 140px; height: auto; object-fit: contain;}}
                    .card {{ margin-bottom: 20px; border: 1px solid #ccc; border-radius: 5px; background-color: white; overflow: hidden; }}
                    .card-title {{ font-size: 16px; font-weight: bold; background-color: #007BFF; color: white; padding: 10px; text-align: center; }}
                    .card-body {{ padding: 15px;}}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #ccc;}}
                    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
                    th {{ background-color: #666; color: white; }}
                    thead {{ display: table-header-group; }}
                    .page-break {{ page-break-before: always; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <img src="{logo_src}" alt="Logo" class="logo">
                    <h1>BITÁCORA {escape(cliente_display).upper()}</h1>
                    <h2>ÁREA CCTV Y SEGURIDAD ELECTRÓNICA</h2>
                </div>

                <div class="card">
                    <div class="card-title">Información Bitácora</div>
                    <div class="card-body">
                    <h2 style="text-align:center; font-size:22px; font-weight:bold; color:#0056b3; margin-bottom:10px;">Reporte de Eventos</h2>
                    <p style="text-align:center; font-size:18px; font-weight:bold; color:#333; margin-top:5px;">Cruce de líneas e intrusiones de perímetro.</p>
                    <hr style="border: 1px solid #ccc; margin: 15px 0;">
                    <h3 style="text-align:center; font-size:20px; font-weight:bold; color:#007BFF;">Ubicación</h3>
                    <p style="text-align:center; font-size:18px; font-weight:bold; color:#333; margin-top:5px;">{escape(lugar)}</p>
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">Datos de Monitoreo</div>
                    <div class="card-body" style="display:flex; justify-content:space-between; padding:15px; background-color:#f8f9fa; border-radius:8px;">
                    <div style="width:48%;">
                        <p style="font-size:16px; font-weight:bold; color:#333; margin-bottom:8px;">👷‍♂️ Operador/es de turno:</p>
                        <div style="background-color:#fff; padding:10px; border-radius:5px; box-shadow:0px 1px 4px rgba(0,0,0,0.1);">
                        {operadores_str}
                        </div>
                    </div>

                    <div style="width:48%;">
                        <p style="font-size:16px; font-weight:bold; color:#333; margin-bottom:8px;">⏰ Horario de monitoreo:</p>
                        <p style="font-size:14px; color:#555;">{escape(bitacora.horario)}</p>

                        <p style="font-size:16px; font-weight:bold; color:#333; margin-top:10px;">📅 Fecha de inicio:</p>
                        <p style="font-size:14px; color:#555;">{escape(fecha_inicio)}</p>

                        <p style="font-size:16px; font-weight:bold; color:#333; margin-top:10px;">📅 Fecha de fin:</p>
                        <p style="font-size:14px; color:#555;">{escape(fecha_fin)}</p>
                    </div>
                    </div>
                </div>

                <div class="page-break"></div>

                <div class="card">
                    <div class="card-title" style="background-color:#0056b3; color:white; text-align:center; padding:12px; font-size:18px;">📋 Eventos Registrados</div>
                    <div class="card-body" style="padding:15px; background-color:#f8f9fa; border-radius:8px;">
                    <table style="width:100%; border-collapse:collapse; margin-top:10px; font-size:14px;">
                        {thead_html}
                        <tbody>
                        {''.join(filas_html)}
                        </tbody>
                    </table>
                    </div>
                </div>

                </body>
                </html>
                """
            
            # ✅ CLAVE: base_url
            HTML(string=html_content, base_url=current_app.root_path).write_pdf(ruta_pdf)

            print(f"✅ PDF generado en {ruta_pdf}")
            pdf_paths[lugar_obj or lugar] = ruta_pdf

        except Exception as e:
            print(f"❌ Error al generar el PDF para '{lugar}': {e}")

    return pdf_paths


# ============================================================
#  DESTINATARIOS DESDE BD
# ============================================================
def obtener_destinatarios_db(session, cliente_id, lugar_id=None):
    """
    Obtiene destinatarios desde la tabla 'destinatarios' diferenciando to / cc / bcc.

    Devuelve un dict:
    {
        "to":  [emails...],
        "cc":  [emails...],
        "bcc": [emails...]
    }
    """
    destinatarios = {"to": [], "cc": [], "bcc": []}

    # Nivel cliente
    q_general = session.query(Destinatario).filter_by(
        cliente_id=cliente_id,
        lugar_id=None,
        activo=True
    )

    if lugar_id is not None:
        q_lugar = session.query(Destinatario).filter_by(
            cliente_id=cliente_id,
            lugar_id=lugar_id,
            activo=True
        )
        rows = list(q_general) + list(q_lugar)
    else:
        rows = list(q_general)

    for d in rows:
        tipo = (d.tipo or "to").lower()
        if tipo not in destinatarios:
            tipo = "to"
        destinatarios[tipo].append(d.email)

    return destinatarios


# ============================================================
#  ENVÍO DE CORREO (por lugar o consolidado)
# ============================================================
def enviar_correo_bitacora_html(session, nueva_bitacora, lugar_obj, pdf_path):
    """
    Envía el correo de bitácora.
    - Si lugar_obj es None → envío consolidado (solo destinatarios de cliente)
    - Si lugar_obj es Lugar → envío por lugar (cliente + lugar)
    """
    try:
        pdf_path = os.path.abspath(pdf_path)
        logo_path = r'C:\Users\oscar.villagra\Documents\VSCode\SeguridadElectronica\bitacorasAPP\firma_correo.png'

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"⚠️ ERROR: El archivo PDF no existe en la ruta: {pdf_path}")

        if not os.path.exists(logo_path):
            raise FileNotFoundError(f"⚠️ ERROR: La firma no existe en la ruta: {logo_path}")

        # ================== CONFIG SMTP OUTLOOK ==================
        SMTP_SERVER = "smtp.office365.com"
        SMTP_PORT = 587  # TLS
        SMTP_USER = "bitacoras@ctr.cl"
        SMTP_PASS = "Carlota123!"

        if not SMTP_USER or not SMTP_PASS:
            raise ValueError("⚠️ ERROR: OUTLOOK_USER u OUTLOOK_PASS no configurados o vacíos.")

        # Datos de bitácora / lugar / cliente
        fecha_inicio = nueva_bitacora.fecha_inicio.strftime("%d-%m-%Y")
        fecha_fin = nueva_bitacora.fecha_fin.strftime("%d-%m-%Y")
        nombre_lugar = getattr(lugar_obj, "nombre", "Consolidado")
        cliente_id = nueva_bitacora.cliente_id
        lugar_id = getattr(lugar_obj, "id", None)

        cliente = session.query(Cliente).get(cliente_id)
        nombre_cliente = cliente.nombre if cliente else "Cliente"

        # ================== DESTINATARIOS DESDE BD ==================
        dest = obtener_destinatarios_db(session, cliente_id, lugar_id)
        to_list = [d.strip() for d in dest["to"] if d.strip()]
        cc_list = [d.strip() for d in dest["cc"] if d.strip()]
        bcc_list = [d.strip() for d in dest["bcc"] if d.strip()]

        # ================== MODO PRUEBAS ==================
        if is_modo_pruebas():
            print("⚠️ MODO PRUEBAS ACTIVADO: Todos los correos serán enviados SOLO a:", CORREO_PRUEBAS)
            to_list = [CORREO_PRUEBAS]
            cc_list = []
            bcc_list = []

        if not to_list:
            print(f"⚠️ No hay destinatarios TO para '{nombre_lugar}'. No se envía correo.")
            return

        if not is_modo_pruebas():
            cc_list_extra = ["oscar.villagra@ctr.cl"]
            cc_list = list(dict.fromkeys(cc_list + cc_list_extra))

        all_recipients = to_list + cc_list + bcc_list

        # ================== ASUNTO Y CUERPO ==================
        if "CAIDA" in nombre_lugar.upper():
            asunto = f"{nombre_cliente} // REPORTE DE {nombre_lugar} // jornada {fecha_inicio} y {fecha_fin}"
            parrafo_intro = (
                f"Junto con saludar, se hace entrega del REPORTE DE CAÍDA correspondiente al día "
                f"{fecha_inicio} hasta el {fecha_fin}. El horario de monitoreo para esta jornada fue: "
                f"{nueva_bitacora.horario}."
            )
        else:
            asunto = f"{nombre_cliente} // Bitácora {nombre_lugar} // jornada {fecha_inicio} y {fecha_fin}"
            parrafo_intro = (
                f"Junto con saludar, se hace entrega de la BITÁCORA correspondiente al día "
                f"{fecha_inicio} hasta el {fecha_fin}. El horario de monitoreo para esta jornada fue: "
                f"{nueva_bitacora.horario}."
            )

        msg_root = MIMEMultipart('related')
        msg_root['Subject'] = asunto
        msg_root['From'] = SMTP_USER
        msg_root['To'] = ", ".join(to_list)
        if cc_list:
            msg_root['Cc'] = ", ".join(cc_list)

        msg_alternative = MIMEMultipart('alternative')
        msg_root.attach(msg_alternative)

        text_body = (
            f"Estimados,\n\n"
            f"Se adjunta la bitácora correspondiente al lugar {nombre_lugar}, "
            f"para el periodo {fecha_inicio} hasta {fecha_fin}. "
            f"Horario de monitoreo: {nueva_bitacora.horario}.\n\n"
            "Saludos cordiales."
        )
        msg_alternative.attach(MIMEText(text_body, 'plain', 'utf-8'))

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.5; color: #333;">
            <p>Estimados</p>
            <p>{parrafo_intro}</p>
            <p>Quedamos atentos a cualquier duda o consulta que puedan presentar.</p>
            <p>Saludos cordiales.</p>
            <p>
                <img src="cid:logo_email" style="width: 200px; height: auto;" alt="{nombre_cliente}">
            </p>
            <p class="editor-paragraph">
                <b><span style="color: rgb(0, 0, 0); font-size: 20px;">
                    Plataforma CCTV y Seguridad Electrónica.
                </span></b><br>
                <span style="font-size: 13px;">Caupolicán N°26, Temuco - Chile</span><br>
                <span style="font-size: 13px;">Whatsapp: +56 9 4028 0981</span><br>
                <span style="font-size: 13px;">Teléfono Fijo: 45 292 1637</span><br>
                <span style="font-size: 13px;">Teléfono Fijo: 45 292 1636</span>
            </p>
        </body>
        </html>
        """
        msg_alternative.attach(MIMEText(html_body, 'html', 'utf-8'))

        # Firma
        with open(logo_path, 'rb') as f_logo:
            img = MIMEImage(f_logo.read())
            img.add_header('Content-ID', '<logo_email>')
            img.add_header('Content-Disposition', 'inline', filename=os.path.basename(logo_path))
            msg_root.attach(img)

        # PDF
        with open(pdf_path, 'rb') as f_pdf:
            pdf_data = f_pdf.read()

        pdf_filename = os.path.basename(pdf_path)
        pdf_part = MIMEApplication(pdf_data, _subtype='pdf')
        pdf_part.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
        msg_root.attach(pdf_part)

        # Envío
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, all_recipients, msg_root.as_string())

        print(f"✅ Correo enviado correctamente a: {', '.join(all_recipients)}")

    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")
        print(f"PDF: {pdf_path}")
        print(f"Lugar: {getattr(lugar_obj, 'nombre', lugar_obj)}")
