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

        self.assertEqual(response.status_code, 200)
        self.assertIn("auth-captcha", response.get_data(as_text=True))
        self.assertIn("h-captcha", response.get_data(as_text=True).lower())


if __name__ == "__main__":
    unittest.main()
