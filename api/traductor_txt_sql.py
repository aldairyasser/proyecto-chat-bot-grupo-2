import re
import spacy
from langdetect import detect
import pandas as pd

nlp_es = spacy.load("es_core_news_sm") # Español
nlp_en = spacy.load("en_core_web_sm") # English

#clientes = pd.read_csv("../data/clientes_ecommerce.csv")
#transacciones = pd.read_csv("../data/transacciones_ecommerce.csv")

#df = pd.merge(transacciones, clientes, on="id_cliente", how="outer")
TABLE_NAME = "merge_transaccion_cliente"
# IMPORTANTE: en tu df mergeado las columnas son las del CSV, aquí asumo que usas las españolas.

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
        "pai": "pais",
        "país": "pais",
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

## Meses
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


## Mapeo de paises

PAIS_MAP = {
    "mexico": "México",
    "argentina": "Argentina",
    "espana": "España",
    "en reino unido": "Reino Unido",
    "francia": "Francia",
    "portugal": "Portugal",
    "alemania": "Alemania",
    "italia": "Italia",

    # Inglés
    "mexico": "México",
    "argentina": "Argentina",
    "spain": "España",
    "united kingdom": "Reino Unido",
    "uk": "Reino Unido",
    "england": "Reino Unido",
    "france": "Francia",
    "portugal": "Portugal",
    "germany": "Alemania",
    "italy": "Italia"

}

## Mapeo de categoria
CATEGORIA_MAP = {
    "accesorios": "Accesorios",
    "accesorio": "Accesorios",

    "reloj": "Relojes inteligentes",
    "relojes": "Relojes inteligentes",
    "reloj inteligente": "Relojes inteligentes",
    "smartwatch": "Relojes inteligentes",

    "movil": "Móviles",
    "moviles": "Móviles",
    "telefono": "Móviles",
    "telefonos": "Móviles",
    "smartphone": "Móviles",

    "portatil": "Portátiles",
    "portatiles": "Portátiles",
    "laptop": "Portátiles",
    "ordenador": "Portátiles",
    "computadora": "Portátiles",
}

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

## Agrupaciones temporales
TIME_GROUP_WORDS = {
    "es": {
        "quarter": {"trimestre", "trimestral", "trimestralmente"},
        "month": {"mes", "mensual"},
        "year": {"año", "ano", "anual"},
    },
    "en": {
        "quarter": {"quarter", "qtr"},
        "month": {"month", "monthly"},
        "year": {"year", "yearly", "annual"},
    }
}

## Mapeo para rankings
RANKING_WORDS = {
    "es": {
        "cantidad": {
            "mas vendido",
            "más vendido",
            "mas vendidos",
            "más vendidos",
            "top vendidos",
            "productos mas vendidos",
            "mayor volumen",
            "mayor volumen de ventas",
        },
        "importe_total": {
            "mayores ventas",
            "mas ingresos",
            "más ingresos",
            "mayor facturacion",
            "ingresos mas altos",
        },
    },
    "en": {
        "cantidad": {
            "best selling",
            "most sold",
            "top selling",
            "highest volume",
            "highest sales volume",
        },
        "importe_total": {
            "highest revenue",
            "top revenue",
            "most revenue",
            "top sales",
        },
    },
}

## Funcion que detecta el idioma
def detectar_idioma(texto: str):
    lang = detect(texto)
    if lang == "es":
        return nlp_es(texto), "es"
    elif lang == "en":
        return nlp_en(texto), "en"
    else:
        raise ValueError(f"Idioma no soportado: {lang}")

## Prepocesamiento del texto
### Quitar tíldes
import unicodedata

def strip_accents(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

### Prepocesado minus y mayus
def _normalize_tokens(doc):
    # lemmas en minúscula, sin puntuación/espacios
        return [
        strip_accents(t.lemma_.lower())
        for t in doc
        if not t.is_punct and not t.is_space
    ]

## Filtro de fecha
### Filtro año
def _find_years(texto: str):
    return sorted(set(re.findall(r"\b(2023|2024)\b", texto)))

### SQL año
def _year_range_condition_pg(years):
    # years es lista de strings [“2023”] o [“2023",“2024"]
    start_y = min(years)
    end_y = max(years)
    return (
        f"fecha_compra BETWEEN '{start_y}-01-01' AND '{end_y}-12-31'"
    )

### Rango meses
def _find_month_ranges(texto: str, idioma: str):
    texto = texto.lower()
    pattern = (
        r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|"
        r"january|february|march|april|may|june|july|august|september|october|november|december)"
        r"\s+(a|y|hasta|to|and)\s+"
        r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|"
        r"january|february|march|april|may|june|july|august|september|october|november|december)"
        r"(?:\s+(\d{4}))?"
    )
    matches = re.findall(pattern, texto)
    # Devuelve mes_inicio, mes_fin, año (como int o None)
    result = []
    for m_start, _, m_end, year in matches:
        y = int(year) if year else None
        result.append((m_start, m_end, y))
    return result

### SQL rango meses
from calendar import monthrange

def _month_range_condition_pg(start_month, end_month, year):
    start_date = f"{year}-{start_month:02d}-01"
    # último día del mes final
    last_day = monthrange(int(year), end_month)[1]
    end_date = f"{year}-{end_month:02d}-{last_day}"
    return f"fecha_compra BETWEEN '{start_date}' AND '{end_date}'"

### Filtro un mes en concreto de un año en concreto
def _find_single_month(texto: str, idioma: str):
    texto = texto.lower()
    for m, num in MONTHS[idioma].items():
        m_match = re.search(rf"\b{m}\b(?:\s+(?:de|del|of))?\s*(\d{{4}})?", texto)
        if m_match:
            year = m_match.group(1)
            return num, year
    return None

### SQL un mes en concreto de un año en concreto
def _single_month_condition_pg(month, year):
    start_date = f"{year}-{month:02d}-01"
    end_day = monthrange(int(year), month)[1]
    end_date = f"{year}-{month:02d}-{end_day}"
    return f"fecha_compra BETWEEN '{start_date}' AND '{end_date}'"

### Fechas relativas
from calendar import monthrange
import re
def _last_day_of_month(year, month):
    return monthrange(year, month)[1]

def _relative_time_condition(doc, idioma: str, available_years=[2023, 2024]):
    texto = strip_accents(doc.text.lower())

    years_in_text = _find_years(texto)
    year = int(years_in_text[0]) if years_in_text else None

    # TRIMESTRE
    m_quarter = re.search(r"(ultim(?:o|a|os|as)?|primer(?:o|a|os|as)?|last|first)\s+(trimestre|quarter)",texto)
    if m_quarter:
        tipo_raw = m_quarter.group(1)
        tipo = "last" if "ultim" in tipo_raw or tipo_raw == "last" else "first"
        if not year:
            year = max(available_years) if tipo == "last" else min(available_years)
        start_month, end_month = (1, 3) if tipo == "first" else (10, 12)
        start_date = f"{year}-{start_month:02d}-01"
        end_day = _last_day_of_month(year, end_month)
        end_date = f"{year}-{end_month:02d}-{end_day}"
        return f"fecha_compra BETWEEN '{start_date}' AND '{end_date}'"

    # Meses relativos
    m_months = re.search(r"(ultim(?:o|a|os|as)?|primer(?:o|a|os|as)?|last|first)\s+(meses?|months?)", texto)
    if m_months:
        tipo_raw = m_months.group(1)
        n_months = int(m_months.group(2)) if m_months.group(2) else 1
        n_months = min(max(n_months, 1), 12)
        tipo = "last" if "ultim" in tipo_raw or tipo_raw == "last" else "first"
        if not year:
            year = max(available_years) if tipo == "last" else min(available_years)
        if tipo == "first":
            start_month, end_month = 1, n_months
        else:
            start_month, end_month = 12 - n_months + 1, 12
        start_date = f"{year}-{start_month:02d}-01"
        end_day = _last_day_of_month(year, end_month)
        end_date = f"{year}-{end_month:02d}-{end_day}"
        return f"fecha_compra BETWEEN '{start_date}' AND '{end_date}'"

    # Año completo
    m_year = re.search(r"(ultim(?:o|a|os|as)?|primer(?:o|a|os|as)?|last|first)\s+(ano|año|year)", texto)
    if m_year:
        tipo_raw = m_year.group(1)
        tipo = "last" if "ultim" in tipo_raw or tipo_raw == "last" else "first"
        if not year:
            year = max(available_years) if tipo == "last" else min(available_years)
        return f"fecha_compra BETWEEN '{year}-01-01' AND '{year}-12-31'"

    return None

## Ranking
### Filtro ranking
def detectar_ranking(tokens, idioma):
    top_words = {
        "es": {"top", "mejores", "mayores", "ranking"},
        "en": {"top", "best", "highest", "ranking"},
    }

    if any(t in tokens for t in top_words[idioma]):
        return True
    return False

### Ranking
def detectar_ranking_semantico(texto: str, idioma: str):
    t = strip_accents(texto.lower())

    for metric, phrases in RANKING_WORDS[idioma].items():
        for p in phrases:
            if p in t:
                return "sum", metric

    return None

### Detectar N top
def detectar_limit(texto: str):
    m = re.search(r"\btop\s+(\d+)", texto.lower())
    if m:
        return int(m.group(1))
    return 5  # default razonable

## Dimesión del ranking
def detectar_dimension_ranking(tokens, idioma):
    tokens_norm = [strip_accents(t.lower()) for t in tokens]
    syn_norm = {strip_accents(k.lower()): v for k, v in SYN_TO_COL[idioma].items()}

    for tok in tokens_norm:
        if tok in syn_norm:
            col = syn_norm[tok]
            if col in {"pais", "producto", "id_cliente", "ciudad", "categoria_producto"}:
                return col
    return None

## Filtro agrupaciones
def detectar_agregacion(tokens, idioma):
    # default: None (si no pide nada, se puede devolver *)
    for agg, words in AGG_WORDS[idioma].items():
        if any(w in tokens for w in words):
            return agg
    return None

## Detección de where
def detectar_metricas(tokens, idioma):
    # Busca la primera métrica "razonable"
    # Si menciona ventas/importe -> importe_total; unidades -> cantidad; etc.
    for tok in tokens:
        if tok in SYN_TO_COL[idioma]:
            col = SYN_TO_COL[idioma][tok]
            if col in {"importe_total", "cantidad", "precio_unitario", "coste_envio", "coste_fabricacion"}:
                return col
    # fallback: si menciona ventas/total en cualquier parte del texto, asumimos importe_total
    texto = " ".join(tokens)
    if re.search(r"\b(venta|ventas|revenue|ingresos|total|totales)\b", texto.lower()):
        return "importe_total"
    return None

## Detección de group
def detectar_groupbys(tokens, idioma, filtros=None):
    group_cols = []
    skip_time_group = False
    auto_time_group = None
    
    if filtros:
        for f in filtros:
            m = re.search(r"BETWEEN '(\d{4})-(\d{2})-(\d{2})' AND '(\d{4})-(\d{2})-(\d{2})'", f)
            if m:
                start_year, start_month, start_day, end_year, end_month, end_day = map(int, m.groups())
                if (end_year == start_year) and ((end_month - start_month + 1) < 12):
                    skip_time_group = True
                    # decidir granularity según meses
                    months_span = end_month - start_month + 1
                    if months_span == 1:
                        auto_time_group = "month"
                    elif months_span == 3:
                        auto_time_group = "quarter"
                    else:
                        auto_time_group = "year"
                    break

    # Tiempo
    time_map = {
        "quarter": ("date_trunc('quarter', fecha_compra)", "trimestre"),
        "month": ("date_trunc('month', fecha_compra)", "mes"),
        "year": ("date_trunc('year', fecha_compra)", "anio"),
    }

    tokens_norm = [strip_accents(t.lower()) for t in tokens]

    # Agrupaciones temporales
    if skip_time_group and auto_time_group:
        expr, _ = time_map[auto_time_group]
        group_cols.append(expr)
    else:
        for granularity, (expr, alias) in time_map.items():
            if any(t in [strip_accents(w) for w in TIME_GROUP_WORDS[idioma][granularity]] for t in tokens_norm):
                group_cols.append(expr)
                break

    # Normalizar SYN_TO_COL
    syn_norm = {strip_accents(k.lower()): v for k, v in SYN_TO_COL[idioma].items()}

    # Detectar dimensiones mencionadas usando trigger ("por"/"by")
    trigger_words = {"es": {"por", "el"}, "en": "by"}
    trigger = trigger_words[idioma]

    for i, tok in enumerate(tokens_norm):
        if tok == trigger and i + 1 < len(tokens_norm):
            next_tok = tokens_norm[i + 1]
            if next_tok in syn_norm:
                col = syn_norm[next_tok]
                if col in COLS and col not in group_cols:
                    group_cols.append(col)

    return group_cols

## Detección de filtro
def detectar_filtros(doc, tokens, idioma):
    has_relative = False
    has_month_range = False
    has_single_month = False
    
    where = []
    text = strip_accents(doc.text.lower())  # todo en minúscula y sin tildes

    # Fechas relativas (prioridad absoluta)
    relative = _relative_time_condition(doc, idioma)
    if relative:
        where.append(relative)
        has_relative = True

    # Rango de meses
    month_ranges = _find_month_ranges(text, idioma)
    if month_ranges:
        for m_start, m_end, year in month_ranges:
            if not year:
                years_in_text = _find_years(text)
                year = int(years_in_text[0]) if years_in_text else 2024
            start_num = MONTHS[idioma][strip_accents(m_start.lower())]
            end_num = MONTHS[idioma][strip_accents(m_end.lower())]
            where.append(_month_range_condition_pg(start_num, end_num, year))
        has_month_range = True
    
    # Mes en concreto
    single_month = _find_single_month(text, idioma)
    if single_month and not has_month_range:
        month, year = single_month
        if not year:
            years_in_text = _find_years(text)
            year = int(years_in_text[0]) if years_in_text else 2024
        where.append(_single_month_condition_pg(month, year))
        has_single_month = True

    # Año(s) solo si no hay fecha relativa
    if not has_relative and not has_month_range and not has_single_month:
        years = _find_years(text)
        if years:
            where.append(_year_range_condition_pg(years))

    # País / ciudad
    for ent in doc.ents:
        ent_text_norm = strip_accents(ent.text.lower())
        if ent.label_ in {"LOC", "GPE"}:
            span_start = max(ent.start - 2, 0)
            span_end = min(ent.end + 2, len(doc))
            window = " ".join([strip_accents(t.lemma_.lower()) for t in doc[span_start:span_end]])
            if ("ciudad" in window) or ("city" in window):
                where.append(f"ciudad = '{ent_text_norm}'")
            else:
                pais_real = PAIS_MAP.get(ent_text_norm, ent.text)
                where.append(f"pais = '{pais_real}'")

    # Producto / categoría
    m_prod = re.search(r"(producto)\s+([a-z0-9_\-áéíóúñ ]{2,})", text)
    if m_prod:
        val = m_prod.group(2).strip()
        val = re.split(r"\b(en|por|de|del|la|el|and|by|of)\b", val)[0].strip()
        val = strip_accents(val.lower())

        cat_real = CATEGORIA_MAP.get(val)

        if cat_real:
            where.append(f"categoria_producto = '{cat_real}'")
        else:
            where.append(
                f"categoria_producto LIKE '%{val.replace('\'','\'\'')}%'"
            )

    m_cat = re.search(r"(categor[ií]a)\s+([a-z0-9_\-áéíóúñ ]{2,})", text)
    if m_cat:
        val = m_cat.group(2).strip()
        val = re.split(r"\b(en|por|de|del|la|el|and|by|of)\b", val)[0].strip()
        val = strip_accents(val.lower())

        cat_real = CATEGORIA_MAP.get(val)

        if cat_real:
            where.append(f"categoria_producto = '{cat_real}'")
        else:
            where.append(
                f"categoria_producto LIKE '%{val.replace('\'','\'\'')}%'"
            )

    # Género
    if re.search(r"\b(masculino|macho?s|varon?es|hombre|hombres|male|m)\b", text):
        where.append("genero IN ('M')")
    if re.search(r"\b(femenino|hembra?s|mujer|mujeres|female|f)\b", text):
        where.append("genero IN ('F')")

    # Edad
    m_gt = re.search(r"(mayores de|mas de|over|older than)\s+(\d{1,3})", text)
    if m_gt:
        where.append(f"edad > {int(m_gt.group(2))}")
    m_lt = re.search(r"(menores de|menos de|under|younger than)\s+(\d{1,3})", text)
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

## Generador de SQL
def generar_sql(texto: str):
    doc, idioma = detectar_idioma(texto)
    tokens_norm = _normalize_tokens(doc)
        
    # Detectar GROUP BY, agregación y métricas
    where = detectar_filtros(doc, tokens_norm, idioma)

    group_by = detectar_groupbys(tokens_norm, idioma, filtros=where)
    
    agg = detectar_agregacion(tokens_norm, idioma)
    metric = detectar_metricas(tokens_norm, idioma)

    has_ranking = detectar_ranking(tokens_norm, idioma)
    ranking_impl = detectar_ranking_semantico(texto, idioma)
    ranking_dim = detectar_dimension_ranking(tokens_norm, idioma)


    if ranking_impl:
        agg, metric = ranking_impl
    else:
        agg = detectar_agregacion(tokens_norm, idioma)
        metric = detectar_metricas(tokens_norm, idioma)

    if has_ranking and ranking_dim:
        group_by = [ranking_dim]

    if has_ranking and not group_by:
        if "producto" in tokens_norm or "productos" in tokens_norm:
            group_by = ["producto"]
        elif "cliente" in tokens_norm or "clientes" in tokens_norm:
            group_by = ["id_cliente"]
        elif "pais" in tokens_norm or "paises" in tokens_norm:
            group_by = ["pais"]

    # Ajustes razonables por defecto
    if agg == "count" and not metric:
        metric = "id_transaccion"
        
    # Defaults "razonables"
    if agg in {"avg", "sum", "max", "min"} and metric is None:
        metric = "importe_total"
    
    # Si hay GROUP BY pero no se detecta métrica, asumimos SUM(importe_total)
    if not metric and group_by:
        metric = "importe_total"
        agg = "sum"

    if agg is None and metric is not None:
        if metric in {"importe_total", "cantidad"}:
            agg = "sum"

    # FILTROS: directamente los construye detectar_filtros

    alias_metric = None
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
        select_parts.append(f"MIN({metric}) AS {alias_metric}")
    
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
        # Si pide conteo, contamos transacciones por defecto
        alias_metric = "conteo_transacciones"
        select_parts.append(f"COUNT(DISTINCT id_transaccion) AS {alias_metric}")

    else:
        if not group_by:
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

    if has_ranking and alias_metric:
        sql += f" ORDER BY {alias_metric} DESC"
        sql += f" LIMIT {detectar_limit(texto)}"
        
    sql += ";"
    return sql
