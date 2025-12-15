import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
from flask_cors import CORS

# Import MCP
from MCP.mcp_core import MCP
from MCP.mcp_tools import query_dataset, init_db
from llm.traductor_txt_sql import generar_sql, llm_to_mcp  # tu LLM

# CARGAMOS VARIABLES DE ENTORNO
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL no está definida")

# ======================
# Configuración Flask
# ======================
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
CORS(app, supports_credentials=True)

# ======================
# Inicializar MCP
# ======================
init_db(db)  # inyecta la base en las tools MCP
mcp = MCP(tools={"query_dataset": query_dataset})

# ======================
# Funciones auxiliares
# ======================
def validar_sql(sql: str):
    sql = sql.strip().lower()
    if not sql.startswith("select"):
        raise ValueError("Solo se permiten consultas SELECT")
    bloqueados = ["delete", "update", "drop", "insert", "alter", "truncate", "grant", "revoke"]
    for palabra in bloqueados:
        if palabra in sql:
            raise ValueError("Consulta SQL no permitida")

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

# ======================
# Endpoints
# ======================
@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "API de TXT a SQL con MCP funcionando correctamente"}), 200

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "todo en orden grumetes"}), 200

@app.route("/query", methods=["POST"])
def run_query():
    data = request.get_json(silent=True)
    if not data or "prompt" not in data:
        return jsonify({"error": "Se requiere un JSON con el campo 'prompt'"}), 400

    prompt = data["prompt"].strip()
    if not prompt:
        return jsonify({"error": "El prompt está vacío"}), 400

    query_type, chart_type = detectar_intencion(prompt)

    try:
        # Generar instrucción para MCP usando tu LLM
        llm_output = llm_to_mcp(prompt)

        # Ejecutar MCP
        result = mcp.run(llm_output)

        return jsonify({
            "prompt": prompt,
            "type": query_type,
            "chart_type": chart_type,
            "result": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ======================
# Main
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)


