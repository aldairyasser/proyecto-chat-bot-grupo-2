import re

class MCP:
    def __init__(self):
        self.allowed_tables = {"merge_transaccion_cliente"}

        # Keywords de negocio
        self.business_keywords = {
            "ventas","totales","mes","año","producto","categoria","agrupado","país","pais",
            "precio","trimestre","meses"
        }

        # Bloqueadas (irrelevantes para negocio)
        self.blocked_topics = {
            "clima", "tiempo", "weather", "historia", "chiste",
            "politica", "deporte", "musica", "pelicula", "perro", "playa",
            "botella","ordenador","teclas","balon","agua","pantalla",
            "coche","barco","cargador","reloj","mar","gato"
        }

    def run_prompt_check(self, prompt: str) -> dict:
        """
        Solo revisa el prompt sin SQL.
        """
        prompt_norm = prompt.lower()

        # Debe contener al menos una keyword de negocio
        if not any(k in prompt_norm for k in self.business_keywords):
            return {"error": "Prompt no relacionado con datos de negocio"}

        # Bloqueo por dominio semántico
        elif any(b in prompt_norm for b in self.blocked_topics):
            return {"error": "Prompt fuera del dominio de negocio (BI transacciones)"}
        
        else:
            return {"ok": True}

    def run_sql_check(self, sql: str) -> dict:
        """
        Revisa la seguridad del SQL
        """
        sql_norm = sql.lower()

        if not sql_norm.startswith("select"):
            return {"error": "Solo se permiten consultas SELECT"}

        elif not any(f"from {t}" in sql_norm for t in self.allowed_tables):
            return {"error": "Tabla no permitida"}

        elif " join " in sql_norm:
            return {"error": "JOINs no permitidos"}

        elif re.search(r"\b(select.+select)\b", sql_norm):
            return {"error": "Subqueries no permitidas"}
        
        else:
            return {"ok": True}
