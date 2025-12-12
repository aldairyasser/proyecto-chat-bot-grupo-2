import spacy
from langdetect import detect

# Cargamos el modelo de lenguaje
nlp_es = spacy.load('es_core_news_sm') # Español
nlp_en = spacy.load('en_core_web_sm') # Ingles

columnas = {
    "es": [
        "id_transaccion", "id_cliente", "fecha_compra", "producto", "categoria_producto",
        "precio_unitario", "cantidad", "importe_total", "metodo_pago",
        "coste_envio", "coste_fabricacion",
        "nombre", "apellidos", "email", "pais", "ciudad", "edad", "genero", "tipo_cliente"
    ],
    "en": [
        "transaction_id", "client_id", "purchase_date", "product", "product_category",
        "unit_price", "quantity", "total_amount", "payment_method",
        "shipping_cost", "manufacturing_cost",
        "name", "surname", "email", "country", "city", "age", "gender", "customer_type"
    ]
}