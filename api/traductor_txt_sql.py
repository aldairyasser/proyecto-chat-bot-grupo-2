
# ## Imports
import re
import spacy
from langdetect import detect
import pandas as pd

# ## Cargamos los modelos 
# Modelos
nlp_es = spacy.load("es_core_news_sm") # Español
nlp_en = spacy.load("en_core_web_sm") # English

# ## Creamos la base de datos
# Cargar los CSVs (ajusta las rutas a tus archivos locales)
#clientes = pd.read_csv("../data/clientes_ecommerce.csv")
#transacciones = pd.read_csv("../data/transacciones_ecommerce.csv")

#df = pd.merge(transacciones, clientes, on="id_cliente", how="outer")
TABLE_NAME = "merge_transaccion_cliente"
# IMPORTANTE: en tu df mergeado las columnas son las del CSV, aquí asumo que usas las españolas.

# ## Mapeo de column
COLS = {
    "id_cliente","nombre","apellidos","email","pais","ciudad","edad","genero",
    "id_transaccion","fecha_compra","producto","categoria_producto",
    "precio_unitario","cantidad","importe_total","metodo_pago",
    "coste_envio","coste_fabricacion"
}

# ## Sinonimos / palabras clave (ES/EN)
SYN_TO_COL = {
    "es": {
        # importe total Ventas / Dinero
        "ventas": "importe_total",
        "dinero": "importe_total",
        "ingresos": "importe_total",
        "beneficios": "importe_total",
        "ganancias": "importe_total",   
        "facturacion": "importe_total",
        "importe": "importe_total",
        "total": "importe_total",
        "monto": "importe_total",      
        "recaudacion": "importe_total", 
        "caja": "importe_total",        
        "pasta": "importe_total",       
        "plata": "importe_total",      
        "valor": "importe_total",
        #cantidad / unidades
        "unidades": "cantidad",
        "cantidad": "cantidad",
        "numero": "cantidad",           
        "volumen": "cantidad",          
        "cuantos": "cantidad",          
        "cuantas": "cantidad",
        #precio
        "precio": "precio_unitario",
        "coste": "precio_unitario",     
        "valor_unitario": "precio_unitario",
        "pvp": "precio_unitario",
      # Costes específicos
        "envio": "coste_envio",
        "transporte": "coste_envio",
        "portes": "coste_envio",
        "logistica": "coste_envio",
        "entregas": "coste_envio",
        "fabricacion": "coste_fabricacion",
        "produccion": "coste_fabricacion",
        "elaboracion": "coste_fabricacion",
        # Ubicación (pais / ciudad)
        "pais": "pais",
        "nacion": "pais",
        "region": "pais",    
        "territorio": "pais",
        "ciudad": "ciudad",
        "capital": "ciudad",
        "municipio": "ciudad",
        "ubicacion": "ciudad",   
        "localidad": "ciudad",
        # Producto y Categoría
        "producto": "producto",
        "articulo": "producto",
        "item": "producto",
        "modelo": "producto",
        "referencia": "producto",
        "categoria": "categoria_producto",
        "tipo": "categoria_producto",
        "clase": "categoria_producto",
        "familia": "categoria_producto", 
        "seccion": "categoria_producto", 
        "gama": "categoria_producto",
        # Cliente (Personas)
        "cliente": "id_cliente",
        "comprador": "id_cliente",
        "usuario": "id_cliente",
        "consumidor": "id_cliente",
        "persona": "id_cliente",
        "clientes": "id_cliente",
        # Demografía
        "genero": "genero",
        "sexo": "genero",
        "hombres": "genero",           
        "mujeres": "genero",
        "edad": "edad",
        "anos": "edad",               
        "nacimiento": "edad",          
        "viejo": "edad",              
        "joven": "edad",
        # Transacción y Fechas
        "transaccion": "id_transaccion",
        "pedido": "id_transaccion",
        "orden": "id_transaccion",
        "ticket": "id_transaccion",
        "factura": "id_transaccion",
        "operacion": "id_transaccion",
        "venta": "id_transaccion",
        "metodo": "metodo_pago",
        "pago": "metodo_pago",
        "forma": "metodo_pago",        
        "tarjeta": "metodo_pago",     
        "efectivo": "metodo_pago",
        "fecha": "fecha_compra",
        "compra": "fecha_compra",
        "dia": "fecha_compra",
        "cuando": "fecha_compra",      
        "momento": "fecha_compra"
    },
    "en": {
        # si el usuario pregunta en inglés, seguimos generando SQL con columnas ES
        # (porque tu dataset está en ES). Solo traducimos la intención.
   # Sales / Money importe_total
        "sales": "importe_total",
        "revenue": "importe_total",
        "income": "importe_total",
        "earnings": "importe_total",
        "profit": "importe_total",     
        "turnover": "importe_total",  
        "amount": "importe_total",
        "total": "importe_total",
        "money": "importe_total",
        "value": "importe_total",       
        "billings": "importe_total",
        # Quantity -> cantidad
        "units": "cantidad",
        "quantity": "cantidad",
        "volume": "cantidad",           
        "count": "cantidad",
        "number": "cantidad",           
        "items": "cantidad",            
        # Price -> precio_unitario
        "price": "precio_unitario",
        "cost": "precio_unitario",      
        "unit": "precio_unitario",      
        "rate": "precio_unitario",
        "worth": "precio_unitario",     
        # Costs
        "shipping": "coste_envio",
        "delivery": "coste_envio",
        "transport": "coste_envio",
        "freight": "coste_envio",
        "logistics": "coste_envio",
        "manufacturing": "coste_fabricacion",
        "production": "coste_fabricacion",
        "making": "coste_fabricacion",  
        # Location -> pais / ciudad
        "country": "pais",
        "nation": "pais",
        "region": "pais",
        "territory": "pais",
        "land": "pais",
        
        "city": "ciudad",
        "town": "ciudad",
        "location": "ciudad",
        "municipality": "ciudad",
        "village": "ciudad",

        # Product
        "product": "producto",
        "item": "producto",
        "article": "producto",
        "model": "producto",
        "sku": "producto",
        "good": "producto",           
        
        "category": "categoria_producto",
        "type": "categoria_producto",
        "class": "categoria_producto",
        "family": "categoria_producto",
        "kind": "categoria_producto",   
        "group": "categoria_producto",

        # Demographics
        "gender": "genero",
        "sex": "genero",
        "male": "genero",
        "female": "genero",
        
        "age": "edad",
        "years": "edad",                
        "old": "edad",                  

        # Transaction details
        "payment": "metodo_pago",
        "method": "metodo_pago",
        "card": "metodo_pago",         
        "cash": "metodo_pago",
        
        "date": "fecha_compra",
        "purchase": "fecha_compra",
        "time": "fecha_compra",
        "when": "fecha_compra",
        "day": "fecha_compra",

        # IDs
        "transaction": "id_transaccion",
        "order": "id_transaccion",
        "deal": "id_transaccion",
        "invoice": "id_transaccion",
        "ticket": "id_transaccion",
        
        "client": "id_cliente",
        "customer": "id_cliente",
        "user": "id_cliente",
        "buyer": "id_cliente",
        "shopper": "id_cliente"
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

# ## Mapeo de paises
PAIS_MAP = {
    "mexico": "México",
    "argentina": "Argentina",
    "espana": "España",
    "españa": "España",
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

# ## Mapeo de categoria
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
    "pc": "Portátiles",
    "laptop": "Portátiles",
    "ordenador": "Portátiles",
    "computadora": "Portátiles",
}

# ## Metricas
AGG_WORDS = {
    "es": {
        "avg": {"promedio", "media", "promediar","valor medio" },
        "sum": {"suma", "total", "sumar", "sumatorio", "acumulado", "agregado",},
        "count": {"cuantos", "cuantas", "numero","veces", "numeros", "conteo", "contar"},
        "max": {"maximo", "maxima", "pico", "tope", "mejor"}, # Sin max, para evitar falsos max
        "min": {"minimo", "minima", "bajo", "peor"}, # Sin min, para evitar falsos min
        "median": {"mediana", "percentil", "percentil 50","valor central"},
        "mode": {"moda", "mas frecuente", "frecuente","habitual", "tendencia"},
        "std": {"desviacion", "desviacion estandar", "variacion", "volatilidad", "dispersion",},
        "var": {"varianza", "variance", "var", "variacion", "variabilidad"},

    },
    "en": {
        "avg": {"average", "avg", "mean"},
        "sum": {"sum", "total"},
        "count": {"count", "how", "many", "number"},
        "max": {"max", "maximum", "highest", "top"},
        "min": {"min", "minimum", "lowest"},
        "median": {"median", "percentile"},
        "mode": {"mode", "most frequent"},
        "std": {"std", "stddev", "standard deviation"},
        "var": {"variance", "var", "variability"},

    }
}
# ## Agrupaciones temporales
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

# ## Mapeo para rankings
RANKING_WORDS = {
"es": {
        # 1. RANKING POR VOLUMEN (Gente que quiere ver movimiento de stock) Se mapea a: COUNT o SUM(cantidad)
        "cantidad": {
            # Basicos
            "mas vendido", "más vendido", "mas vendidos", "más vendidos",
            "top vendidos", "top ventas",
            "productos mas vendidos",
            
            # Negocio / Inventario
            "mayor volumen", "mayor volumen de ventas",
            "mayor rotacion", "mayor rotación", 
            "mas populares", "más populares",   
            "mas demandados", "más demandados",
            "numero uno", "número uno",
            "preferidos", "favoritos"
        },

        # 2. RANKING MONETARIO (Gente que quiere ver dinero)Se mapea a: SUM(importe_total)
        "importe_total": {
            # Básicos
            "mayores ventas", "mayor venta",
            "mas ingresos", "más ingresos",
            "mayores ingresos",
            "facturacion mas alta", "facturación más alta",
            "mayor facturacion", "mayor facturación",
            
            # Negocio / Financiero
            "mas rentables", "más rentables",  
            "mejor rendimiento",
            "mas valiosos", "más valiosos",
            "recaudacion mas alta", "recaudación más alta",
            "mayor impacto",
            "top ingresos",
            "dinero generado"
        },

        # 3. RANKING POR VALOR DEL PRODUCTO (Nuevo: ¿Cuál es el más caro?)mapea a: MAX(precio_unitario) u ORDER BY precio_unitario
        "precio_unitario": {
            "mas caros", "más caros",
            "mas caro", "más caro",
            "mayor precio", "precio mas alto",
            "mas costosos", "más costosos",
            "gama alta", "premium",
            "mayor valor unitario"
        }
    },
    "en": {
# 1. VOLUME RANKING (Quantity)
        "cantidad": {
            # Basic
            "best selling", "best seller",
            "most sold",
            "top selling", "top sellers",
            
            # Business / Stock
            "highest volume", "highest sales volume",
            "most popular",              
            "in high demand",
            "most frequent",
            "number one",
            "market leader"
        },

        # 2. MONETARY RANKING (Revenue)
        "importe_total": {
            # Basic
            "highest revenue", "top revenue",
            "most revenue",
            "top sales", "highest sales",
            
            # Business / Financial
            "highest earning", "top earning",
            "most profitable",          
            "highest grossing",           
            "best performing",
            "top financial",
            "money makers"
        },

        # 3. PRICE RANKING (Unit Price)
        "precio_unitario": {
            "most expensive",
            "highest price", "highest priced",
            "costliest",
            "premium",
            "high end",
            "top tier"
        }
    }
}

# ## Funcion que detecta el idioma
def detectar_idioma(texto: str):
    lang = detect(texto)
    if lang == "es":
        return nlp_es(texto), "es"
    elif lang == "en":
        return nlp_en(texto), "en"
    else:
        return nlp_es(texto), "es"

# ## Prepocesamiento del texto
# ### Quitar tíldes
import unicodedata

def strip_accents(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

# ### Prepocesado minus y mayus
def _normalize_tokens(doc):
    # lemmas en minúscula, sin puntuación/espacios
        return [
        strip_accents(t.lemma_.lower())
        for t in doc
        if not t.is_punct and not t.is_space
    ]

# ## Filtro de fecha
# ### Filtro año
def _find_years(texto: str):
    return sorted(set(re.findall(r"\b(2023|2024)\b", texto)))

# %% [markdown]
# ### SQL año
def _year_range_condition_pg(years):
    # years es lista de strings [“2023”] o [“2023",“2024"]
    start_y = min(years)
    end_y = max(years)
    return (
        f"fecha_compra BETWEEN '{start_y}-01-01' AND '{end_y}-12-31'"
    )

# ### Rango meses
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

# ### SQL rango meses
from calendar import monthrange

def _month_range_condition_pg(start_month, end_month, year):
    start_date = f"{year}-{start_month:02d}-01"
    # último día del mes final
    last_day = monthrange(int(year), end_month)[1]
    end_date = f"{year}-{end_month:02d}-{last_day}"
    return f"fecha_compra BETWEEN '{start_date}' AND '{end_date}'"

# ### Filtro un mes en concreto de un año en concreto
def _find_single_month(texto: str, idioma: str):
    texto = texto.lower()
    for m, num in MONTHS[idioma].items():
        m_match = re.search(rf"\b{m}\b(?:\s+(?:de|del|of))?\s*(\d{{4}})?", texto)
        if m_match:
            year = m_match.group(1)
            return num, year
    return None

# ### SQL un mes en concreto de un año en concreto
def _single_month_condition_pg(month, year):
    start_date = f"{year}-{month:02d}-01"
    end_day = monthrange(int(year), month)[1]
    end_date = f"{year}-{month:02d}-{end_day}"
    return f"fecha_compra BETWEEN '{start_date}' AND '{end_date}'"

# ### Fechas relativas
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
    m_months = re.search(
        r"(?:los|las|the)?\s*"
        r"(ultim(?:o|a|os|as)?|primer(?:o|a|os|as)?|last|first)\s+"
        r"(\d{1,2})\s*"
        r"(mes|meses|month|months)"
        r"(?:\s+de\s+(\d{4}))?",
        texto
        )
    
    if m_months:
        tipo_raw = m_months.group(1)
        n_months = int(m_months.group(2))
        n_months = min(max(n_months, 1), 12)

        tipo = "last" if ("ultim" in tipo_raw or tipo_raw == "last") else "first"

        year_in_match = m_months.group(4)
        if year_in_match:
            year = int(year_in_match)
            
        elif not year:
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

COMPARATIVE_WORDS = { "es": { "mas", "menos", "mayor", "menores", "mayores", "vendido", "vendidos", "vendida", "vendidas", "popular", "populares" }, 
                     "en": { "most", "least", "highest", "lowest", "sold", "popular" } } 

def _is_comparative(val: str, idioma: str) -> bool: 
    tokens = val.split()
    return any(t in COMPARATIVE_WORDS[idioma] for t in tokens)

# ## Ranking
# ### Filtro ranking
def detectar_ranking(texto: str):
    texto_low = strip_accents(texto.lower())

    # Top explícito
    m_top = re.search(r"\btop\s+(\d+)", texto_low)
    if m_top:
        return True, "DESC", int(m_top.group(1))

    # Singular implícito → "más X" / "menos X"
    if re.search(r"\b(el|la)\s+\w+(?:\s+\w+)*\s+mas\b", texto_low):
        return True, "DESC", 1
    if re.search(r"\b(el|la)\s+\w+(?:\s+\w+)*\s+menos\b", texto_low):
        return True, "ASC", 1

    # Plural implícito → top por defecto
    if re.search(r"\b(los|las)\s+\w+(?:\s+\w+)*\s+mas\b", texto_low):
        return True, "DESC", 5
    if re.search(r"\b(los|las)\s+\w+(?:\s+\w+)*\s+mas\b", texto_low):
        return True, "ASC", 5

    # Inglés
    if re.search(r"\bthe\s+\w+(?:\s+\w+)*\s+most\b", texto_low):
        return True, "DESC", 1
    if re.search(r"\bthe\s+\w+(?:\s+\w+)*\s+least\b", texto_low):
        return True, "ASC", 1

    return False, None, None


# ### Ranking implicito
def detectar_ranking_implicito(texto, idioma):
    texto = strip_accents(texto.lower())

    if re.search(r"\b(mayor(?:es)?|menor(?:es)?|mas|menos|over|under)\s+de?\s*\d{1,3}\b", texto) and \
       re.search(r"\b(edad|anos|año|years?|cliente|clientes)\b", texto):
        return False

    patrones = [
        r"mas\s+\w+",         
        r"menos\s+\w+",        
        r"mayor(es)?",         
        r"menor(es)?",
        r"highest|lowest|most|least"
    ]

    return any(re.search(p, texto) for p in patrones)

# ### Ranking
def detectar_ranking_semantico(texto: str, idioma: str):
    t = strip_accents(texto.lower())

    for metric, phrases in RANKING_WORDS[idioma].items():
        for p in phrases:
            if p in t:
                return "sum", metric

    return None

# ## Dimesión del ranking
def detectar_dimension_ranking(tokens, idioma):
    tokens_norm = [strip_accents(t.lower()) for t in tokens]
    syn_norm = {strip_accents(k.lower()): v for k, v in SYN_TO_COL[idioma].items()}

    for tok in tokens_norm:
        if tok in syn_norm:
            col = syn_norm[tok]
            if col in {"pais", "producto", "id_cliente", "ciudad", "categoria_producto"}:
                return col
    return None

# ## Conteo de compras
def detectar_conteo_compras(tokens, idioma):
    palabras = {"es": {"compra", "compras", "pedido", "pedidos"},
                "en": {"purchase", "purchases", "orders"}}

    return any(t in palabras[idioma] for t in tokens)

# ## Filtro agrupaciones
def detectar_agregacion(tokens, idioma):
    # default: None (si no pide nada, se puede devolver *)
    text = " ".join(tokens)
    if re.search(r"\b(mayor(?:es)?|menor(?:es)?|mas|menos|over|under)\s+de?\s*\d{1,3}\b", text):
        if re.search(r"\b(edad|ano|anos|years?|cliente|clientes)\b", text):
            return None

    for agg, words in AGG_WORDS[idioma].items():
        for w in words:
            w_norm = strip_accents(w.lower())
            # si es una frase, búscala en el texto; si es una palabra, también vale con tokens
            if " " in w_norm:
                if w_norm in text:
                    return agg
            else:
                if w_norm in tokens:
                    return agg
    return None

# ## Detección de where
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

# ## Detección de group
def detectar_groupbys(tokens, idioma, filtros=None):
    group_cols = []

    # Tiempo
    time_map = {
        "quarter": ("date_trunc('quarter', fecha_compra)", "trimestre"),
        "month": ("date_trunc('month', fecha_compra)", "mes"),
        "year": ("date_trunc('year', fecha_compra)", "anio"),
    }

    tokens_norm = [strip_accents(t.lower()) for t in tokens]
    
    # Si hay contexto de edad, NO interpretar "año" como agrupación temporal
    text_norm = strip_accents(" ".join(tokens).lower())
    age_context = ("edad" in tokens_norm) or bool(
        re.search(r"\b(entre|between)\s+\d{1,3}\s+(y|and)\s+\d{1,3}\s*(anos|año|years?)\b", text_norm
                  ))

    # Agrupaciones temporales
    relative_month_span = bool(re.search(
        r"(ultim(?:o|a|os|as)?|primer(?:o|a|os|as)?|last|first)\s+\d{1,2}\s+(meses?|months?)",
        text_norm
    ))
    
    if not age_context and not relative_month_span:
        for granularity, (expr, alias) in time_map.items():
            wanted = [strip_accents(w) for w in TIME_GROUP_WORDS[idioma][granularity]]
            if any(t in wanted for t in tokens_norm):
                group_cols.append(expr)
                break

    # Normalizar SYN_TO_COL
    syn_norm = {strip_accents(k.lower()): v for k, v in SYN_TO_COL[idioma].items()}

    # Detectar dimensiones mencionadas usando trigger ("por"/"by")
    trigger_words = {"es": {"por"}, "en": "by"}
    trigger = trigger_words[idioma]

    for i, tok in enumerate(tokens_norm):
        if tok in trigger and i + 1 < len(tokens_norm):
            next_tok = tokens_norm[i + 1]
            if next_tok in syn_norm:
                col = syn_norm[next_tok]
                if col in COLS and col not in group_cols:
                    group_cols.append(col)

    return group_cols

# ### Función de métrica
def agg_func(metric):
    if metric == "id_transaccion":
        return "COUNT(DISTINCT id_transaccion)"
    if metric == "id_cliente":
        return "COUNT(DISTINCT id_cliente)"
    if metric == "cantidad":
        return "SUM(cantidad)"
    if metric == "importe_total":
        return "SUM(importe_total)"
    return None

def agg_expr_sql(agg: str, metric: str) -> str:
    if agg == "count":
        return "COUNT(DISTINCT id_transaccion)" if metric == "id_transaccion" else f"COUNT(DISTINCT {metric})"
    if agg == "sum":
        return f"SUM({metric})"
    if agg == "avg":
        return f"AVG({metric})"
    if agg == "max":
        return f"MAX({metric})"
    if agg == "min":
        return f"MIN({metric})"
    if agg == "std":
        return f"STDDEV_POP({metric})"
    if agg == "var":
        return f"VAR_POP({metric})"
    if agg == "median":
        return f"PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {metric})"
    if agg == "mode":
        return f"MODE() WITHIN GROUP (ORDER BY {metric})"
    return None

# ## Detección de having
def detectar_having(texto: str):
    texto = strip_accents(texto.lower())

    patrones = [
        # Español (variantes frecuentes)
        (r"\b(mas|mayor(?:es)?|superior(?:es)?)\s+(?:a|de|que)\s+(\d+)\b", ">"),
        (r"\b(menos|menor(?:es)?|inferior(?:es)?)\s+(?:a|de|que)\s+(\d+)\b", "<"),
        (r"\b(?:por\s+encima\s+de|por\s+debajo\s+de)\s+(\d+)\b", None),  # se resuelve abajo

        # Inglés
        (r"\b(greater\s+than|more\s+than|above|over)\s+(\d+)\b", ">"),
        (r"\b(less\s+than|below|under)\s+(\d+)\b", "<"),

        # Operadores explícitos
        (r"\b(>=|<=|=|>|<)\s*(\d+)\b", None),
    ]

    for pat, op in patrones:
        m = re.search(pat, texto)
        if not m:
            continue

        # Caso "por encima/debajo de N"
        if op is None and "por encima de" in m.group(0):
            return ">", int(m.group(1))
        if op is None and "por debajo de" in m.group(0):
            return "<", int(m.group(1))

        valor = int(m.group(2))
        operador = op or m.group(1)
        return operador, valor

    return None

def detectar_having_rango(texto: str):
    t = strip_accents(texto.lower())
    m = re.search(r"\bentre\s+(\d+)\s+y\s+(\d+)\b", t) or re.search(r"\bbetween\s+(\d+)\s+and\s+(\d+)\b", t)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        lo, hi = sorted([a, b])
        return lo, hi
    return None

# ## Detección de filtro
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
        if ent.label_ in {"LOC", "GPE"}: # Aquí si pones el país en minus puedes fallar
            span_start = max(ent.start - 2, 0)
            span_end = min(ent.end + 2, len(doc))
            window = " ".join([strip_accents(t.lemma_.lower()) for t in doc[span_start:span_end]])
            if ("ciudad" in window) or ("city" in window):
                where.append(f"ciudad = '{ent_text_norm}'")
            else:
                pais_real = PAIS_MAP.get(ent_text_norm, ent.text)
                where.append(f"pais = '{pais_real}'")

    # Producto
    m_prod = re.search(r"(producto)\s+([a-z0-9_\-áéíóúñ ]{2,})", text)
    if m_prod:
        val = m_prod.group(2).strip()
        val = re.split(r"\b(en|por|de|del|la|el|and|by|of)\b", val)[0].strip()
        val = strip_accents(val.lower())

        if not _is_comparative(val, idioma):
            cat_real = CATEGORIA_MAP.get(val)
            if cat_real:
                where.append(f"categoria_producto = '{cat_real}'")
            else:
                where.append("producto LIKE '%" + val.replace("'", "''") + "%'")
    # Categoría
    m_cat = re.search(r"(categor[ií]a)\s+([a-z0-9_\-áéíóúñ ]{2,})", text)
    if m_cat:
        val = m_cat.group(2).strip()
        val = re.split(r"\b(en|por|de|del|la|el|and|by|of)\b", val)[0].strip()
        val = strip_accents(val.lower())

        if not _is_comparative(val, idioma):
            cat_real = CATEGORIA_MAP.get(val)
            if cat_real:
                where.append(f"categoria_producto = '{cat_real}'")
            else:
                where.append("categoria producto LIKE '%" + val.replace("'", "''") + "%'")

    # Género
    if re.search(r"\b(masculino|macho?s|varon?es|hombre|hombres|male|m)\b", text):
        where.append("genero IN ('M')")
    if re.search(r"\b(femenino|hembra?s|mujer|mujeres|female|f)\b", text):
        where.append("genero IN ('F')")

    # Entre años
    m_between_age = re.search(r"\b(entre|between)\s+(\d{1,3})\s+(y|and)\s+(\d{1,3})\s*(anos|año|anos|years?)\b", text)
    if m_between_age:
        a = int(m_between_age.group(2))
        b = int(m_between_age.group(4))
        lo, hi = sorted([a, b])
        where.append(f"edad BETWEEN {lo} AND {hi}")

    # Edad
    age_context = bool(re.search(r"\b(edad|anos|año|years?)\b", text)) or bool(re.search(r"\bclientes?\b", text))
    m_gt = re.search(r"\b(mayores de|mas de|over|older than)\s+(\d{1,3})\b", text)
    if m_gt and age_context:
        where.append(f"edad > {int(m_gt.group(2))}")
    m_lt = re.search(r"\b(menores de|menos de|under|younger than)\s+(\d{1,3})\b", text)
    if m_lt and age_context:
        where.append(f"edad < {int(m_lt.group(2))}")

    # Dedup
    where_out = []
    seen = set()
    for w in where:
        if w not in seen:
            where_out.append(w)
            seen.add(w)

    return where_out

# ## Generador de SQL
def generar_sql(texto: str):
    doc, idioma = detectar_idioma(texto)
    tokens_norm = _normalize_tokens(doc)
        
    # Detectar GROUP BY, agregación y métricas
    where = detectar_filtros(doc, tokens_norm, idioma)
    group_by = detectar_groupbys(tokens_norm, idioma, filtros=where)

    # Modo listado de clientes (sin agregación)
    wants_clients = ("cliente" in tokens_norm or "clientes" in tokens_norm)
    has_age_filter = any(w.startswith("edad ") for w in where)
    t = strip_accents(texto.lower())

    forced_metric = False
    if re.search(r"\b(numero|número|cuantos?|cuantas?)\b", t) and re.search(r"\bcliente(s)?\b", t):
        agg = "count"
        metric = "id_cliente"
        forced_metric = True

    if wants_clients and group_by:
        agg = "count"
        metric = "id_cliente"

    if not forced_metric:
        agg = detectar_agregacion(tokens_norm, idioma)
        metric = detectar_metricas(tokens_norm, idioma)

    if wants_clients and has_age_filter and (not group_by) and not detectar_agregacion(tokens_norm, idioma):
        agg = None
        metric = None
        group_by = []
    
    if wants_clients and re.search(r"\b(compras?|pedidos?|transacciones?)\b", t):
        agg = "count"
        metric = "id_transaccion"
        if not group_by:
            group_by = ["id_cliente"]

    if re.search(r"\bmes(es)?\b", t) and re.search(r"\b(mas|más)\b", t) and re.search(r"\b(ventas?|importe|ingresos?)\b", t):
        group_by = ["date_trunc('month', fecha_compra)"]
        agg = "sum"
        metric = "importe_total"
        has_ranking = True
        ranking_order = "DESC"
        limit = 12 
    
    if wants_clients and re.search(r"\b(mujer|mujeres|female|femenino)\b", t):
        agg = "count"
        metric = "id_cliente"
        group_by = []
    
    if re.search(r"\bmes\b", t) and re.search(r"\b(menos)\b", t) and re.search(r"\b(2024)\b", t):
        group_by = ["date_trunc('month', fecha_compra)"]
        agg = "sum"
        metric = "importe_total"
        has_ranking = True
        ranking_order = "ASC"
        limit = 1

    has_ranking, ranking_order, limit= detectar_ranking(texto)
    ranking_impl = detectar_ranking_semantico(texto, idioma)
    dimension = detectar_dimension_ranking(tokens_norm, idioma)
    has_ranking_implicito = detectar_ranking_implicito(texto, idioma)

    if ranking_impl:
        agg, metric = ranking_impl
    else:
        if not forced_metric:
            agg = detectar_agregacion(tokens_norm, idioma)
            metric = detectar_metricas(tokens_norm, idioma)
    
    if (not forced_metric) and detectar_conteo_compras(tokens_norm, idioma):
        agg = "count"
        metric = "id_transaccion"

    if (has_ranking or has_ranking_implicito) and dimension:
        group_by = [dimension]
        agg = agg or "sum"
        metric = metric or "cantidad"

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
    if agg in {"avg", "sum", "max", "min"} and metric is None:
        metric = "importe_total"
    if not metric and group_by:
        metric = "importe_total"
        agg = "sum"
    if agg is None and metric is not None:
        if metric in {"importe_total", "cantidad"}:
            agg = "sum"
    
    having_range = detectar_having_rango(texto)
    having_cond = detectar_having(texto)
    having = []
    post_filter = None

    has_age_filter = any(w.startswith("edad ") for w in where)  # ya lo tienes arriba, reutilízalo si quieres
    if has_age_filter:
        having_cond = None
        having_range = None

    if having_cond:
        has_ranking = False
        has_ranking_implicito = False
        ranking_order = None
        limit = None

    if having_range and re.search(r"\b(compras?|pedidos?|transacciones?)\b", strip_accents(texto.lower())):
        agg = "count"
        metric = "id_transaccion"
        lo, hi = having_range
        having.append(f"{agg_expr_sql(agg, metric)} BETWEEN {lo} AND {hi}")
        if wants_clients and (having_cond or having_range) and not group_by:
            group_by = ["id_cliente"]

    if detectar_conteo_compras(tokens_norm, idioma):
        agg = "count"
        metric = "id_transaccion"
    
    if (not forced_metric) and agg == "count" and metric != "id_cliente":
        metric = "id_transaccion"
    
    if agg is not None:
        agg = agg or "sum"
        metric = metric or "importe_total"

    if having_cond:
        operador, valor = having_cond
        expr = agg_expr_sql(agg, metric)
        if expr:
            if group_by:
                having.append(f"{expr} {operador} {valor}")
            else:
                post_filter = (operador, valor)
    
    # SELECT
    alias_metric = None
    select_parts = []
    if group_by:
        select_parts.extend(group_by)
    if agg == "var" and metric not in {"importe_total", "cantidad", "precio_unitario", "coste_envio", "coste_fabricacion"}:
        metric = "importe_total"
    if agg == "avg":
        alias_metric = f"promedio_{metric}"
        select_parts.append(f"AVG({metric}) AS {alias_metric}")
    elif agg == "sum":
        alias_metric = f"total_{metric}"
        select_parts.append(f"{agg_func(metric)} AS {alias_metric}")
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
    elif agg == "var":
        alias_metric = f"var_{metric}"
        select_parts.append(f"VAR_POP({metric}) AS {alias_metric}")
    elif agg == "count":
        # Si pide conteo, contamos transacciones por defecto
        alias_metric = "conteo_clientes" if metric == "id_cliente" else "conteo_transacciones"
        select_parts.append(f"{agg_func(metric)} AS {alias_metric}")
    else:
        if not group_by:
            if wants_clients:
                select_parts.extend(["id_cliente", "nombre", "apellidos", "edad", "pais", "ciudad", "email"])
            else:
                select_parts.extend(["id_transaccion", "fecha_compra", "importe_total", "cantidad"])
    

    sql = "SELECT " + ", ".join(select_parts) + f" FROM {TABLE_NAME}"

    if where:
        sql += " WHERE " + " AND ".join(where)

    if group_by:
        sql += " GROUP BY " + ", ".join(group_by)
    
    if having:
        sql += " HAVING " + " AND ".join(having)

    if (has_ranking or has_ranking_implicito) and dimension:
        sql += f" ORDER BY {alias_metric} {ranking_order or 'DESC'}"
        if not limit and has_ranking_implicito:
            if re.search(r"\b(productos|clientes|paises|categorias|ciudades)\b", strip_accents(texto.lower())):
                limit = 5
                
        sql += f" LIMIT {limit or 1}"

    if post_filter:
        operador, valor = post_filter
        # aquí alias_metric YA existe porque ya construiste el SELECT
        sql = f"SELECT * FROM ({sql}) t WHERE {alias_metric} {operador} {valor}"

    sql += ";"
    return sql