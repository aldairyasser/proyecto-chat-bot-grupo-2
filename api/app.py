import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
from api.traductor_txt_sql import generar_sql
from flask_cors import CORS
from MCP.mcp_core import MCP


# CARAGAMOS VARIABLES DE ENTORNO
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL no está definida")

# APLICACIÓN FLASK
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

mcp = MCP()   #----------- Aquí va el MCP


# HABILITAR CORS
CORS(app, supports_credentials=True)

# SEGURIDAD BÁSICA: VALIDAR SQL
# def validar_sql(sql: str):
#     sql = sql.strip().lower()

#     if not sql.startswith("select"):
#         raise ValueError("Solo se permiten consultas SELECT")

#     bloqueados = [
#         "delete", "update", "drop", "insert",
#         "alter", "truncate", "grant", "revoke"
#     ]

#     for palabra in bloqueados:
#         if palabra in sql:
#             raise ValueError("Consulta SQL no permitida")


# CLASIFICAR INTENCIÓN DE LA CONSULTA
def detectar_intencion(prompt: str):
    prompt = prompt.lower()
    prompt = prompt.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

    if any(k in prompt for k in ["grafico", "grafica", "barras", "tarta", "queso", "lineas"]):
        if "tarta" in prompt or "pie" in prompt:
            return "chart", "pie"
        if "linea" in prompt or "linea" in prompt:
            return "chart", "line"
        return "chart", "bar"
    return "data", None

# ENDPOINT BIENVENIDA
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "API de TXT a SQL funcionando correctamente"
    }), 200

# ENDPOINT DE SALUD
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "todo en orden grumetes"}), 200

# ENPOINT PRINCIPAL

@app.route("/query", methods=["POST"])
def run_query():
    data = request.get_json(silent=True)

    if not data or "prompt" not in data:
        return jsonify({"error": "Se requiere un JSON con el campo 'prompt'"}), 400

    prompt = data["prompt"].strip()
    if not prompt:
        return jsonify({"error": "El prompt está vacío"}), 400

    # 1️⃣ MCP: revisa el prompt antes de generar SQL
    prompt_check = mcp.run_prompt_check(prompt)
    if "error" in prompt_check:
        print("lalalala aquí error mío")
        return jsonify(prompt_check), 400

    query_type, chart_type = detectar_intencion(prompt)

    try:
        # 2️⃣ Generamos SQL solo si el prompt es relevante
        sql = generar_sql(prompt)

        # 3️⃣ MCP: revisa seguridad del SQL

# Si no se detecta intención de negocio, devolvemos error
        if sql is None:
            return jsonify({"error": "Prompt no relacionado con datos de negocio"}), 400


        # Ejecutar SQL
        result = db.session.execute(text(sql))
        rows = [dict(row._mapping) for row in result]

        if not rows:
            return jsonify({"error": "Consulta sin resultados"}), 404

        columns = list(rows[0].keys())
        data_rows = [list(row.values()) for row in rows]

        response = {
            "type": query_type,
            "chart_type": chart_type,
            "data": {
                "columns": columns,
                "rows": data_rows
            },
            "sql": sql,
            "metadata": {"prompt": prompt}
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

