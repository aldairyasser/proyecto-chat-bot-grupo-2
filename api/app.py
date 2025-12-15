import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
from .traductor_txt_sql import generar_sql
from flask_cors import CORS
from MCP.mcp_core import MCP
from MCP.mcp_tools import query_dataset, init_db


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

# INICIALIZAR MCP
init_db(db)  # inyecta la base en las tools MCP
mcp = MCP(tools={"query_dataset": query_dataset})

# HABILITAR CORS
CORS(app, supports_credentials=True)

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
        return jsonify({
            "error": "Se requiere un JSON con el campo 'prompt'"
        }), 400

    prompt = data["prompt"].strip()
    if not prompt:
        return jsonify({"error": "El prompt está vacío"}), 400

    query_type, chart_type = detectar_intencion(prompt)

    try:
        # Generar SQL desde lenguaje natural
        sql = generar_sql(prompt)

        # Envolver la salida para el MCP
        llm_output = {
            "tool": "query_dataset",
            "params": {
                "sql": sql
            }
        }

        # Ejecutar vía MCP (único punto de acceso a la BD)
        mcp_result = mcp.query_dataset(llm_output)

        if mcp_result.get("status") != "ok":
            return jsonify(mcp_result), 400

        rows = mcp_result.get("results", [])
        if not rows:
            return jsonify({"error": "Consulta sin resultados"}), 404

        columns = list(rows[0].keys())
        data_rows = [list(row.values()) for row in rows]

        # Respuesta unificada
        response = {
            "type": query_type,
            "chart_type": chart_type,
            "data": {
                "columns": columns,
                "rows": data_rows
            },
            "sql": sql,
            "metadata": {
                "prompt": prompt
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 400

# ======================
# Main
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

