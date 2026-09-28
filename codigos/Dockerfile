FROM python:3.12-slim

WORKDIR /app/codigos

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# O script grava em ../dados, que aqui é /app/dados (montado pelo compose).
CMD ["python", "buscar-dados-de-almoxarifado.py"]
