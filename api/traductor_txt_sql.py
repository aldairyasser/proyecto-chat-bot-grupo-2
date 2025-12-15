import re
import spacy
from langdetect import detect
import pandas as pd

nlp_es = spacy.load("es_core_news_sm") # Español
nlp_en = spacy.load("en_core_web_sm") # English

# TODAVÍA QUEDA POR HACER EL JOIN
TABLE_NAME = "merge_transaccion_cliente"

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
        "beneficios": "importe_total",
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
        "pedido": "id_transaccion",
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
        # dimensiones
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
        "order": "id_transaccion",
        "client": "id_cliente",
        "customer": "id_cliente",
    }
}

# ## Meses
MONTHS = {
    "es": {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    },
    "en": {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
    }
}

# ## Metricas
AGG_WORDS = {
    "es": {
        "avg": {"promedio", "media", "promediar"},
        "sum": {"suma", "total", "sumar", "sumatorio"},
        "count": {"cuantos", "cuantas", "numero", "numeros", "conteo", "contar"},
        "max": {"maximo", "maxima", "mayor", "pico", "tope"},
        "min": {"minimo", "minima", "menor", "bajo"},
        "median": {"mediana", "percentil", "percentil 50"},
        "mode": {"moda", "mas frecuente", "frecuente"},
        "std": {"desviacion", "desviacion estandar", "variacion"},
    },
    "en": {
        "avg": {"average", "avg", "mean"},
        "sum": {"sum", "total"},
        "count": {"count", "how", "many", "number"},
        "max": {"max", "maximum", "highest", "top"},
        "min": {"min", "minimum", "lowest"},
        "median": {"median", "percentile"},
        "mode": {"mode", "most frequent"},
        "std": {"std", "stddev", "standard deviation"}
    }
}

# %% [markdown]
# ## Agrupaciones temporales

# %%
TIME_GROUP_WORDS = {
    "es": {
        "quarter": {"trimestre", "trimestral", "trimestralmente", "cuatrimestre"},
        "month": {"mes", "mensual"},
        "year": {"año", "anual"},
    },
    "en": {
        "quarter": {"quarter", "qtr"},
        "month": {"month", "monthly"},
        "year": {"year", "yearly", "annual"},
    }
}

# %% [markdown]
# ## Funcion que detecta el idioma

# %%
def detectar_idioma(texto: str):
    lang = detect(texto)
    if lang == "es":
        return nlp_es(texto), "es"
    elif lang == "en":
        return nlp_en(texto), "en"
    else:
        raise ValueError(f"Idioma no soportado: {lang}")

# %% [markdown]
# ## Filtro de fecha

# %% [markdown]
# ### Filtro año

# %%
def _find_years(texto: str):
    return sorted(set(re.findall(r"\b(2023|2024)\b", texto)))

# %% [markdown]
# ### SQL año

# %%
def _year_range_condition_pg(years):
    # years es lista de strings [“2023”] o [“2023",“2024"]
    start_y = min(years)
    end_y = max(years)
    return (
        f"fecha_compra BETWEEN '{start_y}-01-01' AND '{end_y}-12-31'"
    )

# %% [markdown]
# ### Rango meses

# %%
def _find_month_ranges(texto: str, idioma: str):
    texto = texto.lower()
    pattern = (
        r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|"
        r"january|february|march|april|may|june|july|august|september|october|november|december)"
        r"\s+(a|hasta|to)\s+"
        r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|"
        r"january|february|march|april|may|june|july|august|september|october|november|december)"
        r"(?:\s+(\d{4}))?"
    )
    return re.findall(pattern, texto)

# %% [markdown]
# ### SQL rango meses

# %%
def _month_range_condition_pg(start_month, end_month, year):
    start_date = f"{year}-{start_month:02d}-01"
    # último día del mes final
    end_date = (
        f"date_trunc('month', DATE '{year}-{end_month:02d}-01') "
        f"+ INTERVAL '1 month - 1 day'"
    )
    return f"fecha_compra BETWEEN '{start_date}' AND {end_date}"

# %% [markdown]
# ### Filtro un mes en concreto de un año en concreto

# %%
def _find_single_month(texto: str, idioma: str):
    texto = texto.lower()
    for m, num in MONTHS[idioma].items():
        m_match = re.search(rf"\b{m}\b\s*(\d{{4}})?", texto)
        if m_match:
            year = m_match.group(1)
            return num, year
    return None

# %% [markdown]
# #### SQL un mes en concreto de un año en concreto

# %%
def _single_month_condition_pg(month, year):
    start = f"{year}-{month:02d}-01"
    end = (
        f"date_trunc('month', DATE '{year}-{month:02d}-01') "
        f"+ INTERVAL '1 month - 1 day'"
    )
    return f"fecha_compra BETWEEN '{start}' AND {end}"

# %% [markdown]
# ## Quitar tíldes

# %%
import unicodedata

def strip_accents(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

# %% [markdown]
# ## Prepocesado minus y mayus

# %%
def _normalize_tokens(doc):
    # lemmas en minúscula, sin puntuación/espacios
        return [
        strip_accents(t.lemma_.lower())
        for t in doc
        if not t.is_punct and not t.is_space
    ]

# %% [markdown]
# ## Filtro ranking

# %%
def detectar_ranking(tokens, idioma):
    top_words = {
        "es": {"top", "mejores", "mayores", "ranking"},
        "en": {"top", "best", "highest", "ranking"},
    }

    if any(t in tokens for t in top_words[idioma]):
        return True
    return False

# %% [markdown]
# ## Detectar N top

# %%
def detectar_limit(texto: str):
    m = re.search(r"\btop\s+(\d+)", texto.lower())
    if m:
        return int(m.group(1))
    return 5  # default razonable

# %% [markdown]
# ## Filtro agrupaciones

# %%
def detectar_agregacion(tokens, idioma):
    # default: None (si no pide nada, se puede devolver *)
    for agg, words in AGG_WORDS[idioma].items():
        if any(w in tokens for w in words):
            return agg
    return None

# %% [markdown]
# ## Detección de where

# %%
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

# %% [markdown]
# ## Detección de group

# %%
def detectar_groupbys(tokens, idioma):
    group_cols = []
    # Tiempo
    if any(w in tokens for w in TIME_GROUP_WORDS[idioma]["quarter"]):
        group_cols.append("date_trunc('quarter', fecha_compra)")
    elif any(w in tokens for w in TIME_GROUP_WORDS[idioma]["month"]):
        group_cols.append("date_trunc('month', fecha_compra)")
    elif any(w in tokens for w in TIME_GROUP_WORDS[idioma]["year"]):
        group_cols.append("date_trunc('year', fecha_compra)")

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

# %% [markdown]
# ## Detección de filtro

# %%
def detectar_filtros(doc, tokens, idioma):
    where = []
    text = doc.text.lower()

    # Rango de meses
    month_ranges = _find_month_ranges(text, idioma)
    if month_ranges:
        for m_start, _, m_end, year in month_ranges:
            y = year or _find_years(text)[0]
            where.append(
                _month_range_condition_pg(
                    MONTHS[idioma][m_start],
                    MONTHS[idioma][m_end],
                    y
                )
            )
        return where
    
    # Mes en concreto
    single_month = _find_single_month(text, idioma)
    if single_month:
        month, year = single_month
        if year:
            where.append(_single_month_condition_pg(month, year))
            return where

    # Año(s)
    years = _find_years(doc.text)
    if years:
        where.append(_year_range_condition_pg(years))
    
    # País / ciudad vía entidades LOC/GPE
    for ent in doc.ents:
        if ent.label_ in {"LOC", "GPE"}:
            # Heurística: si menciona "ciudad" cerca, filtra por ciudad; si no, por país.
            txt = ent.text.replace("'", "''")
            # Ventana simple alrededor de la entidad
            span_start = max(ent.start - 2, 0)
            span_end = min(ent.end + 2, len(doc))
            window = " ".join([t.lemma_.lower() for t in doc[span_start:span_end]])
            if ("ciudad" in window) or ("city" in window):
                where.append(f"ciudad = '{txt}'")
            else:
                where.append(f"pais = '{txt}'")
    # Producto / categoría por patrón "producto X" / "categoría Y"
    text_lower = doc.text.lower()
    # ES: "producto iphone", "categoría electronica"
    m_prod = re.search(r"(producto)\s+([a-z0-9_\-áéíóúñ ]{2,})", text_lower)
    if m_prod:
        val = m_prod.group(2).strip()
        # corta si aparecen conectores comunes
        val = re.split(r"\b(en|por|de|del|la|el|and|by|of)\b", val)[0].strip()
        where.append("producto LIKE '%" + val.replace("'", "''") + "%'")
    m_cat = re.search(r"(categor[ií]a)\s+([a-z0-9_\-áéíóúñ ]{2,})", text_lower)
    if m_cat:
        val = m_cat.group(2).strip()
        val = re.split(r"\b(en|por|de|del|la|el|and|by|of)\b", val)[0].strip()
        "producto LIKE '%" + val.replace("'", "''") + "%'"
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

# %% [markdown]
# ## Generador de SQL

# %% [markdown]
# COUNT(DISTINCT id_transaccion)
# 
# o subquery agregada antes del join

# %% [markdown]
# MODIFICAR COUNT, QUE NO SOLAMENTE SEA CON TRANSACCIONES

# %%
def generar_sql(texto: str):
    doc, idioma = detectar_idioma(texto)
    tokens = _normalize_tokens(doc)
    agg = detectar_agregacion(tokens, idioma)
    metric = detectar_metricas(tokens, idioma)

    # Defaults "razonables"
    if agg in {"avg", "sum", "max", "min"} and metric is None:
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
        alias_metric = f"promedio_{metric}"
        select_parts.append(f"AVG({metric}) AS {alias_metric}")

    elif agg == "sum":
        alias_metric = f"total_{metric}"
        select_parts.append(f"SUM({metric}) AS {alias_metric}")

    elif agg == "max":
        alias_metric = f"max_{metric}"
        select_parts.append(f"MAX({metric}) AS {alias_metric}")

    elif agg == "min":
        alias_metric = f"min_{metric}"
        select_parts.append(f"MIN({metric}) AS min_{alias_metric}")
    
    elif agg == "median":
        alias_metric = f"mediana_{metric}"
        select_parts.append(f"PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {metric}) AS {alias_metric}")
    
    elif agg == "mode":
        alias_metric = f"moda_{metric}"
        select_parts.append(f"MODE() WITHIN GROUP (ORDER BY {metric}) AS {alias_metric}")
    
    elif agg == "std":
        alias_metric = f"std_{metric}"
        select_parts.append(f"STDDEV_POP({metric}) AS {alias_metric}")

    elif agg == "count":
        alias_metric = "conteo_transacciones"
        select_parts.append(
        f"COUNT(DISTINCT id_transaccion) AS {alias_metric}")

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

    if detectar_ranking(tokens, idioma) and alias_metric:
        sql += f" ORDER BY {alias_metric} DESC"
        sql += f" LIMIT {detectar_limit(texto)}"
    sql += ";"
    return sql

def llm_to_mcp(prompt: str):
    sql = generar_sql(prompt)
    return {
        "tool": "query_dataset",
        "params": {
            "sql": sql
        }
    }





