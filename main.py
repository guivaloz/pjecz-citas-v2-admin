"""
Google Cloud App Engine
"""
import os


# Decidir entre arrancar el sistema para el cliente o para administracion
if os.environ.get("FLASK_APP", "citas_admin.app") == "citas_admin.app":
    from citas_admin import app
else:
    from citas_cliente import app
app = app.create_app()


if __name__ == "__main__":
    app.run()
