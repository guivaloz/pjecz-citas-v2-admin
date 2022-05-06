if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

source venv/bin/activate
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi
export FLASK_APP=citas_admin.app
export SECRET_KEY=vx5Gy5R8UsMZiKn6
export HOST=http://127.0.0.1:5010

figlet CitasV2 admin
echo

echo "-- Flask"
echo "   FLASK_APP:   ${FLASK_APP}"
echo "   FLASK_DEBUG: ${FLASK_DEBUG}"
echo "   SECRET_KEY:  ${SECRET_KEY}"
echo
echo "-- Database"
echo "   DB_HOST: ${DB_HOST}"
echo "   DB_NAME: ${DB_NAME}"
echo "   DB_PASS: ${DB_PASS}"
echo "   DB_USER: ${DB_USER}"
echo
echo "-- Redis"
echo "   REDIS_URL:  ${REDIS_URL}"
echo "   TASK_QUEUE: ${TASK_QUEUE}"
echo
echo "-- Google Cloud Storage"
echo "   CLOUD_STORAGE_DEPOSITO: ${CLOUD_STORAGE_DEPOSITO}"
echo
echo "-- Host"
echo "   HOST: ${HOST}"
echo
echo "-- Salt"
echo "   SALT: ${SALT}"
echo
echo "-- Deployment environment"
echo "   DEPLOYMENT_ENVIRONMENT: ${DEPLOYMENT_ENVIRONMENT}"
echo

export PGDATABASE=${DB_NAME}
export PGPASSWORD=${DB_PASS}
export PGUSER=${DB_USER}
echo "-- PostgreSQL"
echo "   PGDATABASE: ${PGDATABASE}"
echo "   PGPASSWORD: ${PGPASSWORD}"
echo "   PGUSER:     ${PGUSER}"
echo

alias reiniciar="citas db reiniciar"
alias arrancar="flask run --port 5010"
echo "-- Aliases"
echo "   reiniciar: citas db reiniciar"
echo "   arrancar:  flask run --port 5010"
echo
