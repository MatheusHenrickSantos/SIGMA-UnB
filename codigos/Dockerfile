FROM python:3.12-slim

WORKDIR /app/codigos

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Baixa os dados abertos para /app/dados/bruto (montado pelo compose) e depois
# carrega no banco. Se o download falhar, a carga não roda.
CMD ["sh", "-c", "python baixar_dados.py && python carregar.py"]
