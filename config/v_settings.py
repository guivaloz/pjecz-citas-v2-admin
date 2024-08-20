"""
Configuración para producción
"""

import os

# Google Cloud SQL
DB_USER = os.environ.get("DB_USER", "nouser")
DB_PASS = os.environ.get("DB_PASS", "wrongpassword")
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "pjecz_citas_v2")
DB_SOCKET_DIR = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
CLOUD_SQL_CONNECTION_NAME = os.environ.get("CLOUD_SQL_CONNECTION_NAME", "none")

# Google Cloud SQL a Minerva con PostgreSQL
SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Always in False
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret key
SECRET_KEY = os.environ.get("SECRET_KEY", "Esta es una muy mala cadena aleatoria")

# Redis
REDIS_URL = os.environ.get("REDIS_URL", "redis://")
TASK_QUEUE = os.environ.get("TASK_QUEUE", "pjecz_citas_v2")

# Google Cloud Storage
CLOUD_STORAGE_DEPOSITO = os.environ.get("CLOUD_STORAGE_DEPOSITO", "pjecz-informatica")

# Host para los vínculos en los mensajes
HOST = os.environ.get("HOST", "")

# Salt para convertir/reconverir el id en hash
SALT = os.environ.get("SALT", "Esta es una muy mala cadena aleatoria")

# Limite de citas pendientes por cliente
LIMITE_CITAS_PENDIENTES = int(os.environ.get("LIMITE_CITAS_PENDIENTES", "0"))

# URL base para verificar
PAGO_VERIFY_URL = os.environ.get("PAGO_VERIFY_URL", "")
PPA_SOLICITUD_VERIFY_URL = os.environ.get("PPA_SOLICITUD_VERIFY_URL", "")
TDT_SOLICITUD_VERIFY_URL = os.environ.get("TDT_SOLICITUD_VERIFY_URL", "")
