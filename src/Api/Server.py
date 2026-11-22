import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import requests

from src.Repository.ListStudant import ListStudentRepository
from src.Service.WhatsappService import WhatsappService


VALID_DAYS = {
    "monday": ("monday", "get_monday_students"),
    "tuesday": ("tuesday", "get_tuesday_students"),
    "wednesday": ("wednesday", "get_wednesday_students"),
    "thursday": ("thursday", "get_thursday_students"),
    "friday": ("friday", "get_friday_students"),
    "saturday": ("saturday", "get_saturday_students"),
}
DAY_ALIASES = {
    "monday": "monday",
    "segunda": "monday",
    "segunda-feira": "monday",
    "tuesday": "tuesday",
    "terca": "tuesday",
    "terca-feira": "tuesday",
    "terça": "tuesday",
    "terça-feira": "tuesday",
    "wednesday": "wednesday",
    "quarta": "wednesday",
    "quarta-feira": "wednesday",
    "thursday": "thursday",
    "quinta": "thursday",
    "quinta-feira": "thursday",
    "friday": "friday",
    "sexta": "friday",
    "sexta-feira": "friday",
    "saturday": "saturday",
    "sabado": "saturday",
    "sábado": "saturday",
}
MAX_REQUEST_BYTES = 16_384
ABSENCE_MESSAGE = (
    "Olá! Sentimos falta de {name} na aula de hoje. Está tudo bem? "
    "Aconteceu algum imprevisto? Quando puder, nos avise."
)


def _allowed_origins():
    configured_origins = os.environ.get("FRONTEND_ORIGINS")
    if configured_origins is None:
        return {
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        }
    return {
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    }


def _student_json(student):
    return {
        "name": student.get_name(),
        "telephone": student.get_telephone(),
    }


def create_handler(repository=None, whatsapp_service_factory=None):
    repository = repository or ListStudentRepository()

    def default_whatsapp_service_factory():
        api_key = os.environ.get("EVOLUTION_API_KEY")
        if not api_key:
            raise RuntimeError("EVOLUTION_API_KEY não está configurada.")
        instance_name = os.environ.get(
            "EVOLUTION_INSTANCE_NAME", "whatsapp-demo"
        )
        base_url = os.environ.get(
            "EVOLUTION_API_URL", "http://localhost:8080"
        )
        return WhatsappService(api_key, instance_name, base_url=base_url)

    service_factory = (
        whatsapp_service_factory or default_whatsapp_service_factory
    )

    class ApiHandler(BaseHTTPRequestHandler):
        def _send_json(self, status, payload):
            response_body = json.dumps(payload, ensure_ascii=False).encode(
                "utf-8"
            )
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response_body)))

            origin = self.headers.get("Origin")
            if origin in _allowed_origins():
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
                self.send_header(
                    "Access-Control-Allow-Methods", "GET, POST, OPTIONS"
                )
                self.send_header(
                    "Access-Control-Allow-Headers",
                    "Content-Type, Authorization",
                )

            self.end_headers()
            self.wfile.write(response_body)

        def do_OPTIONS(self):
            self._send_json(200, {})

        def do_GET(self):
            parsed_url = urlparse(self.path)
            if parsed_url.path == "/api/health":
                self._send_json(200, {"status": "ok"})
                return

            if parsed_url.path == "/api/days":
                self._send_json(
                    200,
                    {
                        "days": [
                            {
                                "key": day,
                                "label": label,
                            }
                            for day, label in (
                                ("monday", "Segunda-feira"),
                                ("tuesday", "Terça-feira"),
                                ("wednesday", "Quarta-feira"),
                                ("thursday", "Quinta-feira"),
                                ("friday", "Sexta-feira"),
                                ("saturday", "Sábado"),
                            )
                        ]
                    },
                )
                return

            if parsed_url.path != "/api/students":
                self._send_json(404, {"error": "Rota não encontrada."})
                return

            query = parse_qs(parsed_url.query)
            day_values = query.get("day", [])
            normalized_day = (
                DAY_ALIASES.get(day_values[0].strip().casefold())
                if len(day_values) == 1
                else None
            )
            if normalized_day is None:
                self._send_json(
                    400,
                    {
                        "error": (
                            "Informe um dia válido no parâmetro 'day': "
                            + ", ".join(DAY_ALIASES)
                            + "."
                        )
                    },
                )
                return

            day, method_name = VALID_DAYS[normalized_day]
            students_by_hour = getattr(repository, method_name)()
            self._send_json(
                200,
                {
                    "day": day,
                    "hours": {
                        hour: [
                            _student_json(student)
                            for student in students
                        ]
                        for hour, students in students_by_hour.items()
                    },
                },
            )

        def do_POST(self):
            route = urlparse(self.path).path
            if route not in ("/api/messages", "/api/messages/absence"):
                self._send_json(404, {"error": "Rota não encontrada."})
                return

            api_token = os.environ.get("BACKEND_API_TOKEN")
            authorization = self.headers.get("Authorization", "")
            expected_authorization = f"Bearer {api_token or ''}"
            if api_token and not hmac.compare_digest(
                authorization.encode("utf-8"),
                expected_authorization.encode("utf-8"),
            ):
                self._send_json(401, {"error": "Autenticação necessária."})
                return

            content_type = self.headers.get("Content-Type", "")
            if not content_type.lower().startswith("application/json"):
                self._send_json(
                    415, {"error": "Envie o corpo como application/json."}
                )
                return

            try:
                content_length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                self._send_json(
                    400, {"error": "Content-Length inválido."}
                )
                return

            if content_length <= 0:
                self._send_json(400, {"error": "O corpo JSON é obrigatório."})
                return
            if content_length > MAX_REQUEST_BYTES:
                self._send_json(413, {"error": "Corpo da requisição muito grande."})
                return

            try:
                payload = json.loads(self.rfile.read(content_length))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send_json(400, {"error": "JSON inválido."})
                return

            if not isinstance(payload, dict):
                self._send_json(400, {"error": "O corpo deve ser um objeto JSON."})
                return

            if route == "/api/messages/absence":
                self._send_absence_messages(payload)
                return

            telephone = payload.get("telephone")
            message = payload.get("message")
            if (
                not isinstance(telephone, str)
                or not telephone.isdigit()
                or not isinstance(message, str)
                or not message.strip()
            ):
                self._send_json(
                    400,
                    {
                        "error": (
                            "'telephone' deve conter somente dígitos e "
                            "'message' não pode ser vazia."
                        )
                    },
                )
                return

            try:
                whatsapp = service_factory()
            except RuntimeError as error:
                self._send_json(503, {"error": str(error)})
                return

            try:
                provider_response = whatsapp.send_message(
                    telephone, message.strip()
                )
            except requests.exceptions.RequestException:
                self._send_json(
                    502, {"error": "A Evolution API não conseguiu enviar a mensagem."}
                )
                return

            self._send_json(
                200,
                {
                    "status": "sent",
                    "telephone": telephone,
                    "provider_response": provider_response,
                },
            )

        def _send_absence_messages(self, payload):
            day_values = [payload.get("day")]
            normalized_day = (
                DAY_ALIASES.get(day_values[0].strip().casefold())
                if isinstance(day_values[0], str)
                else None
            )
            hour = payload.get("hour")
            selected_students = payload.get("students")
            if normalized_day is None:
                self._send_json(
                    400, {"error": "Informe um dia válido no campo 'day'."}
                )
                return
            if not isinstance(hour, str) or not hour:
                self._send_json(
                    400, {"error": "Informe o horário da turma no campo 'hour'."}
                )
                return
            if not isinstance(selected_students, list) or not selected_students:
                self._send_json(
                    400,
                    {"error": "Selecione pelo menos um aluno para enviar."},
                )
                return

            _, method_name = VALID_DAYS[normalized_day]
            students_by_hour = getattr(repository, method_name)()
            class_students = students_by_hour.get(hour)
            if class_students is None:
                self._send_json(
                    400,
                    {"error": "O horário informado não existe para esse dia."},
                )
                return

            registered_students = {
                (student.get_name(), student.get_telephone()): student
                for student in class_students
            }
            selected = []
            seen = set()
            for item in selected_students:
                if not isinstance(item, dict):
                    self._send_json(
                        400,
                        {
                            "error": (
                                "Cada aluno selecionado deve conter "
                                "'name' e 'telephone'."
                            )
                        },
                    )
                    return

                name = item.get("name")
                telephone = item.get("telephone")
                if not isinstance(name, str) or not name.strip():
                    self._send_json(
                        400, {"error": "O nome do aluno selecionado é inválido."}
                    )
                    return
                if not isinstance(telephone, str) or not telephone.isdigit():
                    self._send_json(
                        400,
                        {
                            "error": (
                                f"{name}: não há um telefone válido "
                                "cadastrado para envio."
                            )
                        },
                    )
                    return

                key = (name, telephone)
                if key not in registered_students:
                    self._send_json(
                        400,
                        {
                            "error": (
                                f"{name} não pertence à turma informada."
                            )
                        },
                    )
                    return
                if key in seen:
                    self._send_json(
                        400,
                        {"error": f"{name} foi selecionado mais de uma vez."},
                    )
                    return
                seen.add(key)
                selected.append(registered_students[key])

            try:
                whatsapp = service_factory()
            except RuntimeError as error:
                self._send_json(503, {"error": str(error)})
                return

            results = []
            for student in selected:
                name = student.get_name()
                telephone = student.get_telephone()
                message = ABSENCE_MESSAGE.format(name=name)
                try:
                    provider_response = whatsapp.send_message(
                        telephone, message
                    )
                except requests.exceptions.RequestException:
                    results.append(
                        {
                            "name": name,
                            "telephone": telephone,
                            "status": "failed",
                            "error": (
                                "A Evolution API não conseguiu enviar "
                                "esta mensagem."
                            ),
                        }
                    )
                    continue

                results.append(
                    {
                        "name": name,
                        "telephone": telephone,
                        "status": "sent",
                        "provider_response": provider_response,
                    }
                )

            failures = sum(
                result["status"] == "failed" for result in results
            )
            status = 502 if failures else 200
            self._send_json(
                status,
                {
                    "status": "partial_failure" if failures else "sent",
                    "sent": len(results) - failures,
                    "failed": failures,
                    "results": results,
                },
            )

        def log_message(self, format, *args):
            # Keep request content and student phone numbers out of console logs.
            super().log_message(format, *args)

    return ApiHandler


def run_server():
    host = os.environ.get("BACKEND_HOST", "127.0.0.1")
    api_token = os.environ.get("BACKEND_API_TOKEN")
    if host not in {"127.0.0.1", "localhost", "::1"} and not api_token:
        raise RuntimeError(
            "BACKEND_API_TOKEN é obrigatório para escutar em interface externa."
        )

    try:
        port = int(os.environ.get("BACKEND_PORT", "8000"))
    except ValueError as error:
        raise ValueError("BACKEND_PORT deve ser um número inteiro.") from error

    server = ThreadingHTTPServer(
        (host, port), create_handler()
    )
    print(f"Backend disponível em http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando o backend...")
    finally:
        server.server_close()
