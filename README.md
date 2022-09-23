# pjecz-citas-v2-admin

Sistema de Citas V2: Interfaz para administracion hecho en Flask.

## Entorno Virtual con Python 3.6 o superior

Crear el entorno virtual dentro de la copia local del repositorio, con

    python -m venv venv

O con virtualenv

    virtualenv -p python3 venv

Active el entorno virtual, en Linux con...

    source venv/bin/activate

O en windows con

    venv/Scripts/activate

Verifique que haya el mínimo de paquetes con

    pip list

Actualice el pip de ser necesario

    pip install --upgrade pip

Y luego instale los paquetes que requiere Plataforma Web

    pip install -r requirements.txt

Verifique con

    pip list

Instalar el Comando Cli

    pip install --editable .

## Configurar

Debe crear un archivo `instance/settings.py` que defina su conexion a la base de datos...

    """
    Configuracion para desarrollo
    """
    import os


    # Base de datos
    DB_USER = os.environ.get("DB_USER", "wronguser")
    DB_PASS = os.environ.get("DB_PASS", "badpassword")
    DB_NAME = os.environ.get("DB_NAME", "pjecz_citas_v2")
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")

    # MariaDB o MySQL
    # SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

    # PostgreSQL
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

    # SQLite
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///pjecz_citas_v2.sqlite3'

Guarde sus configuraciones, contrasenas y tokens en un archivo `.env`

    # Flask
    FLASK_APP=citas_admin.app
    FLASK_DEBUG=1
    SECRET_KEY=****************

    # Database
    DB_HOST=127.0.0.1
    DB_NAME=pjecz_citas_v2
    DB_PASS=****************
    DB_USER=adminpjeczcitasv2

    # Redis
    REDIS_URL=redis://127.0.0.1
    TASK_QUEUE=pjecz_citas_v2

    # Google Cloud Storage
    CLOUD_STORAGE_DEPOSITO=

    # Host
    HOST=

    # Salt sirve para cifrar el ID con HashID, debe ser igual en la API
    SALT=****************

    # Sendgrid
    SENDGRID_API_KEY=
    SENDGRID_FROM_EMAIL=

    # URLs de destino a las paginas de confirmacion
    NEW_ACCOUNT_CONFIRM_URL=http://127.0.0.1:3000/new_account_confirm
    RECOVER_ACCOUNT_CONFIRM_URL=http://127.0.0.1:3000/recover_account_confirm

    # URLs de las encuestas
    POLL_SYSTEM_URL=http://127.0.0.1:3000/poll_system
    POLL_SERVICE_URL=http://127.0.0.1:3000/poll_service

    # Si esta en PRODUCTION se evita reiniciar la base de datos
    DEPLOYMENT_ENVIRONMENT=develop

Cree el archivo `.bashrc` para que un perfil de Konsole le facilite la inicializacion

    if [ -f ~/.bashrc ]; then
        source ~/.bashrc
    fi

    source venv/bin/activate
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi

    figlet CitasV2 Admin
    echo

    echo "== Variables de entorno"
    echo "   CLOUD_STORAGE_DEPOSITO: ${CLOUD_STORAGE_DEPOSITO}"
    echo "   DEPLOYMENT_ENVIRONMENT: ${DEPLOYMENT_ENVIRONMENT}"
    echo "   DB_HOST: ${DB_HOST}"
    echo "   DB_NAME: ${DB_NAME}"
    echo "   DB_USER: ${DB_USER}"
    echo "   DB_PASS: ${DB_PASS}"
    echo "   FLASK_APP: ${FLASK_APP}"
    echo "   HOST: ${HOST}"
    echo "   NEW_ACCOUNT_CONFIRM_URL: ${NEW_ACCOUNT_CONFIRM_URL}"
    echo "   POLL_SYSTEM_URL: ${POLL_SYSTEM_URL}"
    echo "   POLL_SERVICE_URL: ${POLL_SERVICE_URL}"
    echo "   RECOVER_ACCOUNT_CONFIRM_URL: ${RECOVER_ACCOUNT_CONFIRM_URL}"
    echo "   REDIS_URL: ${REDIS_URL}"
    echo "   SALT: ${SALT}"
    echo "   SECRET_KEY: ${SECRET_KEY}"
    echo "   SENDGRID_API_KEY: ${SENDGRID_API_KEY}"
    echo "   SENDGRID_FROM_EMAIL: ${SENDGRID_FROM_EMAIL}"
    echo "   TASK_QUEUE: ${TASK_QUEUE}"
    echo

    export PGHOST=$DB_HOST
    export PGPORT=5432
    export PGDATABASE=$DB_NAME
    export PGUSER=$DB_USER
    export PGPASSWORD=$DB_PASS

    alias reiniciar="citas db reiniciar"
    alias arrancar="flask run --port 5010"
    alias fondear="rq worker ${TASK_QUEUE}"
    echo "-- Aliases"
    echo "   reiniciar: Reiniciar base de datos"
    echo "   arrancar:  Arrancar Flask"
    echo "   fondear:   Arrancar RQ worker"
    echo

## Tareas en el fondo a programar en el servidor en la nube

Cada noche eliminar los cit_clientes que NO tengan contrasena SHA256 ni citas

    citas cit_clientes eliminar-abandonados --test False
