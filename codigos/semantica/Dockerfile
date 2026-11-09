# Imagem do serviço `semantica` (python -m semantica).
# Separada das imagens de ingestão e transformação porque o PyTorch pesa ~1 GB:
# as etapas que só carregam ou transformam dados não precisam dele.
#
# Construída com contexto ./codigos (ver docker-compose.yml), mas só copia o
# pacote semantica, que não depende dos outros scripts.
FROM python:3.12-slim

WORKDIR /app/codigos

# PyTorch só de CPU, do índice oficial do PyTorch (o do PyPI traz CUDA, vários GB)
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.14.1

COPY semantica/requirements.txt /tmp/requirements-semantica.txt
RUN pip install --no-cache-dir -r /tmp/requirements-semantica.txt

COPY semantica/ semantica/
# medições do ADR 0005 (busca exata x HNSW)
COPY medir_adr0005.py .

# Modelos baixados do Hugging Face ficam no volume montado em /modelos,
# para não baixar de novo a cada execução.
ENV HF_HOME=/modelos \
    PYTHONUNBUFFERED=1

CMD ["python", "-m", "semantica", "tudo"]
