from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

from llm.traductor_txt_sql import llm_to_mcp
from MCP.mcp_core import MCP
from MCP.mcp_tools import query_dataset, init_db

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    "postgresql://sql:ugXUydx6vkmpAj4x001dReqdzhYhAMjs"
    "@dpg-d4ttdjidbo4c73aifvpg-a.oregon-postgres.render.com"
    "/desafio_tripulaciones_db"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 👉 inyectamos la BD en las tools MCP
init_db(db)

# 👉 inicializamos MCP
mcp = MCP(
    tools={
        "query_dataset": query_dataset
    }
)

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json()
    prompt = data.get("prompt")

    if not prompt or not isinstance(prompt, str):
        return jsonify({"error": "Prompt inválido"}), 400

    try:
        llm_output = llm_to_mcp(prompt)
    except Exception as e:
        return jsonify({"error": str(e)}), 500   # Evita que si no detecta bien el idioma, lance un error en vez de romperse.
    result = mcp.run(llm_output)

    return jsonify({
        "prompt": prompt,
        "result": result
    })

if __name__ == "__main__":
    app.run(debug=True)

