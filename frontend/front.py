import streamlit as st
import requests
import json

st.set_page_config(page_title="Test API TXT → SQL", layout="wide")

st.title("🧪 Test API TXT → SQL (JSON)")

prompt = st.text_area(
    "Escribe el prompt en lenguaje natural",
    height=120,
    placeholder="Ej: grafico de barras de empleados por departamento"
)

if st.button("Enviar a la API"):
    if not prompt.strip():
        st.warning("Por favor escribe un prompt.")
    else:
        try:
            url = "http://localhost:5000/query"
            #url = "https://proyecto-chat-bot-grupo-2-final.onrender.com/query"

            payload = {
                "prompt": prompt
            }

            response = requests.post(
                url,
                json=payload,
                timeout=10
            )

            st.subheader("🔎 Estado HTTP")
            st.code(response.status_code)

            st.subheader("📦 JSON de respuesta")

            try:
                data = response.json()
                st.json(data)

                # ===== Comprobaciones básicas =====
                st.subheader("✅ Validaciones")

                if "type" not in data:
                    st.error("❌ Falta campo 'type'")
                else:
                    st.success(f"Tipo detectado: {data['type']}")

                #if data.get("type") == "value":
                #    st.success(f"Valor devuelto: {data.get('value')}")

                if data.get("type") in ["data", "chart"]:
                    cols = data.get("data", {}).get("columns")
                    rows = data.get("data", {}).get("rows")

                    if cols and rows:
                        st.success("Tabla base correcta")
                        st.dataframe(
                            [dict(zip(cols, r)) for r in rows]
                        )
                    else:
                        st.error("❌ data.columns o data.rows incorrectos")

            except json.JSONDecodeError:
                st.error("La respuesta no es JSON válido")
                st.text(response.text)

        except Exception as e:
            st.error(f"No se pudo conectar con la API: {e}")
