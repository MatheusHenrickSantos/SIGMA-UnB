import hashlib

def calcular_hash(texto: str) -> str:
    "Calcula o hash SHA-256 de uma string."
    
    return hashlib.sha256(texto.encode()).hexdigest()