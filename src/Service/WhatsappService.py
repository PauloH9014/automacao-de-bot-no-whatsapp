import requests

class WhatsappService:
    def __init__(
        self, api_key, instance_name, base_url="http://127.0.0.1:8080"
    ):
        self.api_key = api_key
        self.base_url = (
            f"{base_url.rstrip('/')}/message/sendText/{instance_name}"
        )

    def send_message(self, phone_number, message):
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        # Formato correto exigido pela Evolution API
        payload = {
            "number": phone_number,
            "text": message
        }

        response = requests.post(
            self.base_url, headers=headers, json=payload, timeout=30
        )
        response.raise_for_status()
        if not response.content:
            return None
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            return {"raw_response": response.text}