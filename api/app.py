import os
import socket
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
from api.traductor_txt_sql import generar_sql
from flask_cors import CORS
from MCP.mcp_core import MCP, init_db
import socket
import json

# CARGAMOS VARIABLES DE ENTORNO
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(":x: DATABASE_URL no está definida")
QRADAR_HOST = os.getenv("QRADAR_HOST", "127.0.0.1")  # IP del HOST con VirtualBox
QRADAR_PORT = int(os.getenv("QRADAR_PORT", 1514))       # Host Port que apunta al 514 UDP de QRadar


# FUNCION SYSLOG PARA QRADAR
syslog_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
def send_to_qradar(level, message, extra=None):
    timestamp = datetime.utcnow().isoformat()
    hostname = "chatbot-backend"
    appname = "flask-api"
    payload = {
        "level": level,
        "message": message,
        "extra": extra or {},
        "timestamp": timestamp
    }
    syslog_message = f"<134>{timestamp} {hostname} {appname}: {json.dumps(payload)}"
    syslog_socket.sendto(
        syslog_message.encode(),
        (QRADAR_HOST, QRADAR_PORT)
    )

# APLICACIÓN FLASK
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# INICIALIZAR MCP
init_db(db)  # inyecta la base en las tools MCP
mcp = MCP()

# HABILITAR CORS
CORS(app, supports_credentials=True)

# DETECTAR INTENCION DEL PROMPT
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
        "message": "Estamos funcionando marineros de agua dulce"
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
        send_to_qradar("WARN", "Prompt missing in request", {"request_data": data})
        return jsonify({"error": "Se requiere un JSON con el campo 'prompt'"}), 400
    
    prompt = data["prompt"].strip()
    if not prompt:
        send_to_qradar("WARN", "Prompt vacío en request")
        return jsonify({"error": "El prompt está vacío"}), 400

    send_to_qradar("INFO", "Query received", {"prompt": prompt})

    # =========================
    # MCP – VALIDACIÓN PROMPT
    # =========================
    prompt_check = mcp.run_prompt_check(prompt)
    if prompt_check.get("error"):
        send_to_qradar(
            "WARN",
            "MCP prompt check failed",
            {"prompt": prompt, "reason": prompt_check["error"]}
        )
        return jsonify(prompt_check), 400

    query_type, chart_type = detectar_intencion(prompt)

    try:
        # Generar SQL desde lenguaje natural
        sql = generar_sql(prompt)
        send_to_qradar("INFO", "SQL generated", {"sql": sql})

        # =========================
        # MCP – VALIDACIÓN SQL
        # =========================
        sql_check = mcp.run_sql_check(sql)
        if sql_check.get("error"):
            send_to_qradar(
                "ERROR",
                "MCP SQL check failed",
                {"sql": sql, "reason": sql_check["error"]}
            )
            return jsonify(sql_check), 400

        # =========================
        # EJECUCIÓN DIRECTA BBDD
        # =========================
        result = db.session.execute(text(sql))
        rows = result.mappings().all()

        if not rows:
            send_to_qradar("INFO", "Query returned no results", {"sql": sql})
            return jsonify({"error": "Consulta sin resultados"}), 404

        columns = list(rows[0].keys())
        data_rows = [list(row.values()) for row in rows]

        # =========================
        # RESPUESTA
        # =========================
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

        send_to_qradar("INFO", "Query executed successfully", {"rows": len(rows)})
        return jsonify(response), 200

    except Exception as e:
        send_to_qradar("ERROR", "Query execution failed", {"error": str(e)})
        return jsonify({"error": str(e)}), 400

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
