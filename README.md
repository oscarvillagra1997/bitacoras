# Crear entorno virtual (Windows)
python -m venv mi_entorno

# Activar entorno virtual (Windows)
.\mi_entorno\Scripts\Activate.ps1

# Si aparece error de permisos (ExecutionPolicy), usa:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Windows CMD clasico
.\.venv\Scripts\activate.bat


# Nombres para proyectos

Para proyectos formales, se suelen usar:

.venv (estándar moderno)

venv

.env

nombre_del_proyecto-venv