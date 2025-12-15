import re
import spacy
from langdetect import detect

# Modelos
nlp_es = spacy.load("es_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")

# Tabla "lógica" (la que usarás en SQL)
TABLE_NAME = "transacciones"
CLIENTS_TABLE ="clientes"

COLS = {
    "id_cliente","nombre","apellidos","email","pais","ciudad","edad","genero",
    "id_transaccion","fecha_compra","producto","categoria_producto",
    "precio_unitario","cantidad","importe_total","metodo_pago",
    "coste_envio","coste_fabricacion"
}

# Sinónimos / palabras clave -> columnas (ES/EN)
SYN_TO_COL = {
    "es": {
        # métricas
        "ventas": "importe_total",
        "ingresos": "importe_total",
        "facturacion": "importe_total",
        "importe": "importe_total",
        "total": "importe_total",
        "unidades": "cantidad",
        "cantidad": "cantidad",
        "precio": "precio_unitario",
        "envio": "coste_envio",
        "fabricacion": "coste_fabricacion",
        # dimensiones
        "pais": "pais",
        "ciudad": "ciudad",
        "producto": "producto",
        "categoria": "categoria_producto",
        "genero": "genero",
        "edad": "edad",
        "metodo": "metodo_pago",
        "pago": "metodo_pago",
        "fecha": "fecha_compra",
        "compra": "fecha_compra",
        "transaccion": "id_transaccion",
        "cliente": "id_cliente",
    },
    "en": {
        # si el usuario pregunta en inglés, seguimos generando SQL con columnas ES
        # (porque tu dataset está en ES). Solo traducimos la intención.
        "sales": "importe_total",
        "revenue": "importe_total",
        "amount": "importe_total",
        "total": "importe_total",
        "units": "cantidad",
        "quantity": "cantidad",
        "price": "precio_unitario",
        "shipping": "coste_envio",
        "manufacturing": "coste_fabricacion",
        "country": "pais",
        "city": "ciudad",
        "product": "producto",
        "category": "categoria_producto",
        "gender": "genero",
        "age": "edad",
        "payment": "metodo_pago",
        "date": "fecha_compra",
        "purchase": "fecha_compra",
        "transaction": "id_transaccion",
        "client": "id_cliente",
        "customer": "id_cliente",
    }
}

AGG_WORDS = {
    "es": {
        "avg": {"promedio", "media", "promediar"},
        "sum": {"suma", "total", "sumar"},
        "count": {"cuantos", "cuántos", "numero", "número", "conteo", "contar"},
    },
    "en": {
        "avg": {"average", "avg", "mean"},
        "sum": {"sum", "total"},
        "count": {"count", "how", "many", "number"},
    }
}

TIME_GROUP_WORDS = {
    "es": {
        "quarter": {"trimestre", "trimestral"},
        "month": {"mes", "mensual"},
        "year": {"año", "anual"},
    },
    "en": {
        "quarter": {"quarter", "qtr"},
        "month": {"month", "monthly"},
        "year": {"year", "yearly", "annual"},
    }
}

def detectar_idioma(texto: str):
    lang = detect(texto)
    if lang == "es":
        return nlp_es(texto), "es"
    elif lang == "en":
        return nlp_en(texto), "en"
    else:
        raise ValueError(f"Idioma no soportado: {lang}")

def _find_years(texto: str):
    # años 1900-2099
    return sorted(set(re.findall(r"\b(19\d{2}|20\d{2})\b", texto)))

def _normalize_tokens(doc):
    # lemmas en minúscula, sin puntuación/espacios
    return [t.lemma_.lower() for t in doc if not t.is_punct and not t.is_space]

def detectar_agregacion(tokens, idioma):
    # default: None (si no pide nada, se puede devolver *)
    for agg, words in AGG_WORDS[idioma].items():
        if any(w in tokens for w in words):
            return agg
    return None

def detectar_metricas(tokens, idioma):
    # Busca la primera métrica "razonable"
    # Si menciona ventas/importe -> importe_total; unidades -> cantidad; etc.
    for tok in tokens:
        if tok in SYN_TO_COL[idioma]:
            col = SYN_TO_COL[idioma][tok]
            if col in {"importe_total", "cantidad", "precio_unitario", "coste_envio", "coste_fabricacion"}:
                return col
    # fallback: si habla de promedio sin métrica explícita, asumimos ventas
    return None

def detectar_groupbys(tokens, idioma):
    group_cols = []
    # Tiempo
    if any(w in tokens for w in TIME_GROUP_WORDS[idioma]["quarter"]):
        group_cols.append("QUARTER(fecha_compra)")
        group_cols.append("YEAR(fecha_compra)")
    elif any(w in tokens for w in TIME_GROUP_WORDS[idioma]["month"]):
        group_cols.append("MONTH(fecha_compra)")
        group_cols.append("YEAR(fecha_compra)")
    elif any(w in tokens for w in TIME_GROUP_WORDS[idioma]["year"]):
        group_cols.append("YEAR(fecha_compra)")
    # Dimensiones típicas si el usuario las menciona
    dims_priority = ["pais", "ciudad", "categoria_producto", "producto", "genero", "metodo_pago"]
    mentioned = set()
    for tok in tokens:
        if tok in SYN_TO_COL[idioma]:
            mentioned.add(SYN_TO_COL[idioma][tok])
    for d in dims_priority:
        if d in mentioned and d in COLS:
            group_cols.append(d)
    # Elimina duplicados manteniendo orden
    seen = set()
    out = []
    for g in group_cols:
        if g not in seen:
            out.append(g)
            seen.add(g)
    return out

def detectar_filtros(doc, tokens, idioma):
    where = []
    # Año(s)
    years = _find_years(doc.text)
    if years:
        # Si hay varios, usamos IN
        if len(years) == 1:
            where.append(f"YEAR(fecha_compra) = {years[0]}")
        else:
            years_list = ",".join(years)
            where.append(f"fecha_compra BETWEEN '{years}-01-01' AND '{years}-12-31'")

    # País / ciudad vía entidades LOC/GPE
    for ent in doc.ents:
        if ent.label_ in {"LOC", "GPE"}:
            # Heurística: si menciona "ciudad" cerca, filtra por ciudad; si no, por país.
            txt = ent.text.replace("‘", "‘’")
            # Ventana simple alrededor de la entidad
            span_start = max(ent.start - 2, 0)
            span_end = min(ent.end + 2, len(doc))
            window = " ".join([t.lemma_.lower() for t in doc[span_start:span_end]])
            if ("ciudad" in window) or ("city" in window):
                where.append(f"ciudad = ‘{txt}‘")
            else:
                where.append(f"pais = ‘{txt}‘")
    # Producto / categoría por patrón "producto X" / "categoría Y"
    text_lower = doc.text.lower()
    # ES: "producto iphone", "categoría electronica"
    m_prod = re.search(r"(producto)\s+([a-z0-9_\-áéíóúñ ]{2,})", text_lower)
    if m_prod:
        val = m_prod.group(2).strip()
        # corta si aparecen conectores comunes
        val = re.split(r"\b(en|por|de|del|la|el|and|by|of)\b", val)[0].strip()
        where.append(f"producto LIKE ‘%{val.replace('\'','\'\'')}%")
    m_cat = re.search(r"(categor[ií]a)\s+([a-z0-9_\-áéíóúñ ]{2,})", text_lower)
    if m_cat:
        val = m_cat.group(2).strip()
        val = re.split(r"\b(en|por|de|del|la|el|and|by|of)\b", val)[0].strip()
        where.append(f"categoria_producto LIKE ‘%{val.replace('\'','\'\'')}%’")
    # Género simple (M/F, masculino/femenino, male/female)
    if re.search(r"\b(masculino|hombre|male|m)\b", text_lower):
        where.append("genero IN (‘M’,‘Masculino’,‘male’,‘Male’)")
    if re.search(r"\b(femenino|mujer|female|f)\b", text_lower):
        where.append("genero IN (‘F’,‘Femenino’,‘female’,‘Female’)")
    # Edad: "mayores de 30", "menores de 25"
    m_gt = re.search(r"(mayores de|más de|over|older than)\s+(\d{1,3})", text_lower)
    if m_gt:
        where.append(f"edad > {int(m_gt.group(2))}")
    m_lt = re.search(r"(menores de|menos de|under|younger than)\s+(\d{1,3})", text_lower)
    if m_lt:
        where.append(f"edad < {int(m_lt.group(2))}")
    # Dedup
    where_out = []
    seen = set()
    for w in where:
        if w not in seen:
            where_out.append(w)
            seen.add(w)
    return where_out

def generar_sql(texto: str):
    doc, idioma = detectar_idioma(texto)
    tokens = _normalize_tokens(doc)
    agg = detectar_agregacion(tokens, idioma)
    metric = detectar_metricas(tokens, idioma)
    # Defaults "razonables"
    if agg in {"avg", "sum"} and metric is None:
        metric = "importe_total"
    if agg is None and metric is not None:
        # si menciona métrica pero no agg, asumimos SUM para ventas/unidades
        if metric in {"importe_total", "cantidad"}:
            agg = "sum"
    group_by = detectar_groupbys(tokens, idioma)
    where = detectar_filtros(doc, tokens, idioma)
    # SELECT
    select_parts = []
    if group_by:
        select_parts.extend(group_by)
    if agg == "avg":
        select_parts.append(f"AVG({metric}) AS promedio_{metric}")
    elif agg == "sum":
        select_parts.append(f"SUM({metric}) AS total_{metric}")
    elif agg == "count":
        # Si pide conteo, contamos transacciones por defecto
        select_parts.append("COUNT(id_transaccion) AS conteo_transacciones")
    else:
        # Sin intención: devuelve columnas principales (evita SELECT *)
        select_parts.append("id_transaccion")
        select_parts.append("fecha_compra")
        select_parts.append("importe_total")
        select_parts.append("cantidad")
    sql = "SELECT " + ", ".join(select_parts) + f" FROM {TABLE_NAME}"
    if where:
        sql += " WHERE " + " AND ".join(where)
    if group_by:
        sql += " GROUP BY " + ", ".join(group_by)
    sql += ";"
    return sql

def llm_to_mcp(texto: str) -> dict:
    sql = generar_sql(texto)

    return {
        "tool": "query_dataset",
        "params": {
            "sql": sql
        }
    }
