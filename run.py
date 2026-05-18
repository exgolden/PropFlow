# run.py
"""
Punto de entrada de la aplicación PropFlow.
Inicializa la base de datos, carga variables de entorno y arranca el servidor Flask.
"""
import os
from dotenv import load_dotenv
from src.__init__ import create_app
from db.init import init_db

load_dotenv()
init_db()
app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(debug=debug)
