import yaml
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
from pathlib import Path
from flask import Flask, g

app = Flask(__name__)
app.secret_key = "this@is@my@secret"


class ManagedMySQLConnection:
    def __init__(self, app_instance):
        self.app = app_instance

    def _connect(self):
        if "_mysql_connection" not in g:
            g._mysql_connection = MySQLdb.connect(
                host=self.app.config["MYSQL_HOST"],
                user=self.app.config["MYSQL_USER"],
                passwd=self.app.config["MYSQL_PASSWORD"],
                db=self.app.config["MYSQL_DB"],
                charset="utf8mb4",
            )
        return g._mysql_connection

    def cursor(self):
        return self._connect().cursor()

    def commit(self):
        return self._connect().commit()

    def rollback(self):
        return self._connect().rollback()


class ManagedMySQL:
    def __init__(self, app_instance):
        self.connection = ManagedMySQLConnection(app_instance)


def _load_db_config():
    project_root = Path(__file__).resolve().parent.parent
    candidate_paths = [
        project_root / "database.yaml",
        project_root / "database copy.yaml",
    ]

    for config_path in candidate_paths:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            if config:
                return config

    searched = ", ".join(str(p) for p in candidate_paths)
    raise FileNotFoundError(
        f"Database config file not found. Checked: {searched}"
    )


db = _load_db_config()
app.config["MYSQL_HOST"] = db["mysql_host"]
app.config["MYSQL_USER"] = db["mysql_user"]
app.config["MYSQL_PASSWORD"] = db["mysql_password"]
app.config["MYSQL_DB"] = db["mysql_db"]
my_sql = ManagedMySQL(app)


@app.teardown_appcontext
def close_db_connection(exception):
    connection = g.pop("_mysql_connection", None)
    if connection is not None:
        connection.close()


# ... existing code ...
from market.translations import get_text
from flask import session, request

@app.context_processor
def inject_translate():
    def t(key):
        lang = session.get('lang', 'en')
        return get_text(key, lang)
    return dict(t=t)

from market import routes

