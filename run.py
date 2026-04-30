# run.py
import os
from src.__init__ import create_app
from db.init import init_db
from db.seed import run_seed


init_db()
run_seed()

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(debug=debug)