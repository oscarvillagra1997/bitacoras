from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app import db_session
from app.models import Operador

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        user = (
            db_session.query(Operador)
            .filter(Operador.email == email, Operador.activo.is_(True))
            .first()
        )

        if not user or not user.check_password(password):
            flash("Credenciales inválidas.", "danger")
            return render_template("login.html")

        login_user(user)  # ✅ crea sesión
        return redirect(url_for("clientes_bp.inicio"))

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth_bp.login"))
