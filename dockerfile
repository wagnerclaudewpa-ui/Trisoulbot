# Imagem base: Python 3.11 enxuta (slim = menos peso, build mais rápido)
FROM python:3.11-slim

# Pasta de trabalho dentro do container
WORKDIR /app

# Copia só o requirements primeiro (aproveita cache do Docker:
# se as dependências não mudarem, não reinstala tudo de novo)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Agora copia o resto do código (bot.py, etc.)
COPY . .

# Comando que roda quando o container sobe
CMD ["python", "bot.py"]
