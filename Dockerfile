# Imagen base
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Dependencias del sistema (necesarias para spaCy)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiamos requirements
COPY requirements.txt .

# Instalamos dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Descargamos modelos spaCy
RUN python -m spacy download es_core_news_sm
RUN python -m spacy download en_core_web_sm

# Copiamos el proyecto
COPY . .

# Puerto que expone Flask
EXPOSE 5000

# Comando de arranque (PRODUCCIÓN)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "api.app:app"]
