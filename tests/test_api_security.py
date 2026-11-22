import json
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from src.Api.Server import create_handler, run_server
from src.Repository.ListStudant import ListStudentRepository


class FakeWhatsApp:
    def send_message(self, telephone, message):
        return {
            "accepted": True,
            "telephone": telephone,
            "message": message,
        }


class ApiSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            create_handler(whatsapp_service_factory=FakeWhatsApp),
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def _post_message(self, headers):
        body = json.dumps(
            {"telephone": "00000000000", "message": "Test message"}
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/messages",
            data=body,
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        try:
            response = urlopen(request)
        except HTTPError as error:
            return error.code, json.loads(error.read())
        with response:
            return response.status, json.loads(response.read())

    def test_post_requires_configured_bearer_token(self):
        with patch.dict(os.environ, {"BACKEND_API_TOKEN": "test-token"}):
            status, response = self._post_message({})

        self.assertEqual(status, 401)
        self.assertEqual(response["error"], "Autenticação necessária.")

    def test_authenticated_post_calls_the_service(self):
        with patch.dict(os.environ, {"BACKEND_API_TOKEN": "test-token"}):
            status, response = self._post_message(
                {"Authorization": "Bearer test-token"}
            )

        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "sent")

    def test_public_schedule_contains_only_fictional_phone_free_records(self):
        repository = ListStudentRepository()
        students = repository.get_all_students()

        self.assertTrue(students)
        self.assertTrue(
            all(
                student.get_name().startswith("Aluno Fictício")
                and student.get_telephone() is None
                for student in students
            )
        )

    def test_external_bind_requires_an_api_token(self):
        with patch.dict(
            os.environ, {"BACKEND_HOST": "0.0.0.0"}, clear=True
        ):
            with self.assertRaisesRegex(RuntimeError, "BACKEND_API_TOKEN"):
                run_server()


if __name__ == "__main__":
    unittest.main()
