import os

import requests

API_KEY = os.environ.get("EVOLUTION_API_KEY")
if not API_KEY:
    raise RuntimeError("Configure EVOLUTION_API_KEY no ambiente.")

INSTANCE_NAME = os.environ.get("EVOLUTION_INSTANCE_NAME", "whatsapp-demo")
BASE_URL = os.environ.get("EVOLUTION_API_URL", "http://127.0.0.1:8080")
url = f"{BASE_URL.rstrip('/')}/instance/create"

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

payload = {
    "instanceName": INSTANCE_NAME,
    "qrcode": True,
    "integration": "WHATSAPP-BAILEYS"
}

print("Solicitando criação da instância...")
response = requests.post(url, headers=headers, json=payload, timeout=30)
response.raise_for_status()
print("Resposta do Servidor:", response.status_code)