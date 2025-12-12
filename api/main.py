from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://sql:ugXUydx6vkmpAj4x001dReqdzhYhAMjs@dpg-d4ttdjidbo4c73aifvpg-a.oregon-postgres.render.com/desafio_tripulaciones_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route("/query", methods=["GET"])
def run_query():
    sql = request.args.get("sql")
    if not sql:
        return jsonify({"error": "Falta el parámetro 'sql'"}), 400

    try:
        result = db.session.execute(text(sql))

        # SQLAlchemy 2.0: convertir Rows a dict con row._mapping
        rows = [dict(row._mapping) for row in result]

        return jsonify({"results": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
