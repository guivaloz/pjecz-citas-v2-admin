"""
Google Cloud App Engine toma main.py
"""
from citas_admin import app

app = app.create_app()


if __name__ == "__main__":
    app.run()
