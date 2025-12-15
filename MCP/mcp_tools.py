from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
# db se inyecta desde la API
db = None
def init_db(database):
    global db
    db = database
FORBIDDEN = {"drop", "delete", "update", "insert"}
def query_dataset(sql: str):
    if any(word in sql.lower() for word in FORBIDDEN):
        return {"error": "Consulta no permitida"}
    if db is None:
        return {"status": "error", "message": "DB no inicializada"}
    try:
        result = db.session.execute(text(sql))
        rows = [dict(row._mapping) for row in result]
        return {"status": "ok", "results": rows}
    except Exception as e:
        return {"status": "error", "message": str(e)}