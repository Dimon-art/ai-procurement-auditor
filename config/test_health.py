from unittest.mock import patch

from django.test import TestCase, override_settings


@override_settings(ALLOWED_HOSTS=["testserver"])
class HealthCheckTests(TestCase):
    def test_health_check_returns_200_when_database_is_available(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "database": "ok",
            },
        )

    @patch(
        "config.health.connection.cursor",
        side_effect=Exception("Database unavailable"),
    )
    def test_health_check_returns_503_when_database_is_unavailable(
        self,
        mock_cursor,
    ):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {
                "status": "error",
                "database": "error",
            },
        )