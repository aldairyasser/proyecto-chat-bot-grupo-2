import re

class MCP:
    def __init__(self):
        self.allowed_tables = {"merge_transaccion_cliente"}

        self.business_keywords = {
            "ventas","totales","mes","año","producto","categoria",
            "agrupado","país","pais","precio","trimestre","meses"
        }

        self.blocked_topics = {
            "clima", "tiempo", "weather", "historia", "chiste",
            "politica", "deporte", "musica", "pelicula", "perro",
            "playa", "botella", "ordenador", "teclas", "balon",
            "agua", "pantalla", "coche", "barco", "cargador",
            "reloj", "mar", "gato"
        }

    def _contains_word(self, text: str, word: str) -> bool:
        return re.search(rf"\b{re.escape(word)}\b", text) is not None

    def run_prompt_check(self, prompt: str) -> dict:
        prompt_norm = prompt.lower()

        has_business = any(
            self._contains_word(prompt_norm, k)
            for k in self.business_keywords
        )

        has_blocked = any(
            self._contains_word(prompt_norm, b)
            for b in self.blocked_topics
        )

        if has_blocked and not has_business:
            return {"error": "Prompt fuera del dominio de negocio"}

        if not has_business:
            return {"error": "Prompt no relacionado con métricas de negocio"}

        return {"ok": True}

    def run_sql_check(self, sql: str) -> dict:
        sql_norm = sql.lower()

        # Solo SELECT
        if not re.match(r"^\s*select\b", sql_norm):
            return {"error": "Solo se permiten consultas SELECT"}

        return {"ok": True}
