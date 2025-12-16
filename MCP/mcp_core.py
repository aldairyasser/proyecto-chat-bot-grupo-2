import re

class MCP:
    def __init__(self):
        self.allowed_tables = {"merge_transaccion_cliente"}

        self.business_keywords = {"ventas","dinero","ingresos","beneficios","ganancias","facturacion",
        "importe","total","monto","recaudacion","caja","pasta","plata","valor","unidades","cantidad",
        "numero","volumen","cuantos","cuantas","precio","coste","valor_unitario","pvp",
        "Costesespecíficos","envio","transporte","portes","logistica","entregas","fabricacion",
        "produccion","elaboracion","pais","nacion","region","territorio","ciudad","capital",
        "municipio","ubicacion","localidad","producto","articulo","item","modelo","referencia",
        "categoria","tipo","clase","familia","seccion","gama","cliente","comprador","usuario",
        "consumidor","persona","clientes","genero","sexo","hombres","mujeres","edad","anos",
        "nacimiento","viejo","joven","transaccion","pedido","orden","ticket","factura","operacion",
        "venta","metodo","pago","forma","tarjeta","efectivo","fecha","compra","dia","cuando","momento",
        "revenue","income","earnings","profit","turnover","amount","total","money","value","billings",
        "units","quantity","volume","count","number","items","price","cost","unit","rate","worth",
        "shipping","delivery","transport","freight","logistics","manufacturing","production","making",
        "country","nation","region","territory","land","","city","town","location","municipality",
        "village","product","item","article","model","sku","good","","category","type","class","family",
        "kind","group","gender","sex","male","female","","age","years","old","payment","method","card",
        "cash","date","purchase","time","when","day","transaction","order","deal","invoice","ticket",
        "client","customer","user","buyer","shopper"
        }

        self.blocked_topics = {
            "clima", "tiempo", "weather", "historia", "chiste",
            "politica", "deporte", "musica", "pelicula", "perro",
            "playa", "botella", "teclas", "balon",
            "agua", "pantalla", "coche", "barco", "cargador",
            "reloj", "mar", "gato", "sexo", "violencia", "drogas",
            "armas", "medicina", "salud", "enfermedad"
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
