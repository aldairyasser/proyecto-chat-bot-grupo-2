import streamlit as st
import requests
import urllib.parse

st.title("Consulta SQL con Flask API")

sql_query = st.text_area("Escribe tu consulta SQL", height=150)

if st.button("Ejecutar"):
    if not sql_query.strip():
        st.warning("Por favor escribe una consulta SQL.")
    else:
        try:
            #url = "http://localhost:5000/query"
            #params = {"sql": sql_query}
            #encoded_params = urllib.parse.urlencode(params)
            #full_url = f"{url}?{encoded_params}"
            response = requests.get(
                "http://127.0.0.1:5000/query",
                params={"sql": sql_query},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    st.dataframe(results)
                else:
                    st.info("No hay resultados.")
            else:
                st.error(f"Error: {response.json().get('error')}")
        except Exception as e:
            st.error(f"No se pudo conectar con la API: {e}")
