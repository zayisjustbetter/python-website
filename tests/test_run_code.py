import unittest
from types import SimpleNamespace
from unittest.mock import patch

import app as app_module


class RunCodeEndpointTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    @patch("urllib.request.urlopen")
    @patch("subprocess.run")
    def test_code_runs_locally_without_remote_runner(self, mock_run, mock_urlopen):
        mock_run.return_value = SimpleNamespace(
            returncode=0,
            stdout="hello\n",
            stderr="",
        )

        response = self.client.post("/api/run-code", json={"code": "print('hello')"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["stdout"], "hello\n")
        mock_urlopen.assert_not_called()

    def test_auth_modal_includes_hcaptcha_container(self):
        response = self.client.get("/")
        page_html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("auth-captcha", page_html)
        self.assertIn("h-captcha", page_html.lower())
        self.assertIn("01f4e24a-3376-48ca-85a2-7e069f0aa5de", page_html)
        self.assertNotIn("ES_8582c9b4f8724ba086eb7e68af308e97", page_html)

    @patch("urllib.request.urlopen")
    def test_captcha_verification_endpoint_uses_server_secret(self, mock_urlopen):
        app_module.app.config["HCAPTCHA_SECRET_KEY"] = "ES_8582c9b4f8724ba086eb7e68af308e97"
        mock_urlopen.return_value.__enter__.return_value.read.return_value = b'{"success": true}'

        response = self.client.post("/api/verify-captcha", json={"captcha_token": "abc123"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])
        mock_urlopen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
