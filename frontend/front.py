import streamlit as st
import requests
import json

st.set_page_config(page_title="Test API TXT → SQL", layout="wide")

st.title("🧪 Test API TXT → SQL (JSON)")

prompt = st.text_area(
    "Escribe el prompt en lenguaje natural",
    height=120,
    placeholder="Ej: Ventas totales por país en 2024"
)

if st.button("Enviar a la API"):
    if not prompt.strip():
        st.warning("Por favor escribe un prompt.")
    else:
        try:
            # Cambia la URL a tu API local o remota
            # url = "http://localhost:5000/query"
            url = "https://proyecto-chat-bot-grupo-2.onrender.com/query"

            payload = {"prompt": prompt}

            response = requests.post(url, json=payload, timeout=10)
            st.subheader("🔎 Estado HTTP")
            st.code(response.status_code)

            try:
                data = response.json()
            except json.JSONDecodeError:
                st.error("La respuesta no es JSON válido")
                st.text(response.text)
                st.stop()

            st.subheader("📦 JSON de respuesta (raw)")
            st.json(data)

            # === Procesamos el resultado real ===
            result = data.get("result")
            if not result:
                st.error("❌ La respuesta no contiene 'result'")
            else:
                if result.get("status") == "ok":
                    rows = result.get("results", [])
                    if rows:
                        st.success(f"✅ {len(rows)} resultados encontrados")
                        st.dataframe(rows)  # muestra tabla
                    else:
                        st.warning("⚠️ No se encontraron resultados")
                else:
                    st.error(f"❌ Error en la consulta: {result.get('error')}")

            # === Opcional: mostrar SQL generado para debug ===
            if "sql_debug" in result:
                st.subheader("📝 SQL generado")
                st.code(result["sql_debug"])

        except requests.exceptions.RequestException as e:
            st.error(f"No se pudo conectar con la API: {e}")
        except Exception as e:
            st.error(f"Error inesperado: {e}")
