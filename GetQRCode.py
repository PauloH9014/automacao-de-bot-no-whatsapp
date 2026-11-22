import base64
import os
from pathlib import Path

import requests

API_KEY = os.environ.get("EVOLUTION_API_KEY")
if not API_KEY:
  raise RuntimeError("Configure EVOLUTION_API_KEY no ambiente.")

INSTANCE_NAME = os.environ.get("EVOLUTION_INSTANCE_NAME", "whatsapp-demo")
BASE_URL = os.environ.get("EVOLUTION_API_URL", "http://127.0.0.1:8080")
url = f"{BASE_URL.rstrip('/')}/instance/connect/{INSTANCE_NAME}"
headers = {"apikey": API_KEY}

print("A contactar o servidor para obter o QR Code...")
response = requests.get(url, headers=headers, timeout=30)
response.raise_for_status()
data = response.json()

# Verifica se a API devolveu o código em base64
if isinstance(data, dict) and data.get("base64"):
  base64_str = data["base64"]
  if "," in base64_str:
    base64_str = base64_str.split(",")[1]

  img_data = base64.b64decode(base64_str, validate=True)

  output_path = Path(os.environ.get("QRCODE_PATH", "qrcode.png"))
  output_path.write_bytes(img_data)

  print(
      f"Sucesso! O QR Code foi salvo em '{output_path}'."
  )
else:
  raise RuntimeError("A Evolution API não retornou um QR Code.")