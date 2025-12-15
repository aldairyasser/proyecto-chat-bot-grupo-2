import os
import socket
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
from .traductor_txt_sql import generar_sql
from flask_cors import CORS
from MCP.mcp_core import MCP
from MCP.mcp_tools import query_dataset, init_db
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
mcp = MCP(tools={"query_dataset": query_dataset})

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
    
    query_type, chart_type = detectar_intencion(prompt)
    
    try:
        # Generar SQL desde lenguaje natural
        sql = generar_sql(prompt)
        send_to_qradar("INFO", "SQL generated", {"sql": sql})
        
        # Envolver la salida para el MCP
        llm_output = {
            "tool": "query_dataset",
            "params": {
                "sql": sql
            }
        }

        # Ejecutar vía MCP (único punto de acceso a la BD)
        mcp_result = mcp.run(llm_output)
        if mcp_result.get("status") != "ok":
            send_to_qradar("ERROR", "MCP run failed", {"mcp_result": mcp_result})
            return jsonify(mcp_result), 400
        
        rows = mcp_result.get("results", [])
        if not rows:
            send_to_qradar("INFO", "Query returned no results", {"sql": sql})
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
