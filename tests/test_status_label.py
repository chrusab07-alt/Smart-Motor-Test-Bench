import unittest

from main import _connection_status_text


class ConnectionStatusLabelTests(unittest.TestCase):
    def test_connection_status_text_uses_connected_or_not_connected(self) -> None:
        self.assertEqual(_connection_status_text(True, "COM3"), "CONNECTED (COM3)")
        self.assertEqual(_connection_status_text(False, "COM3"), "NOT CONNECTED")


if __name__ == "__main__":
    unittest.main()
