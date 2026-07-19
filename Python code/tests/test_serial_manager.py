import unittest

from backend.serial_manager import SerialManager


class SerialManagerTelemetryTests(unittest.TestCase):
    def test_parse_packet_updates_live_metrics(self) -> None:
        manager = SerialManager()

        parsed = manager.parse_packet("1250,12.4,2.1,26.04,31.2,85.5,72")

        self.assertTrue(parsed)
        self.assertTrue(manager.has_live_data)
        self.assertEqual(manager.get_latest_metrics()["rpm"], 1250.0)
        self.assertEqual(manager.get_latest_metrics()["voltage"], 12.4)
        self.assertEqual(manager.get_latest_metrics()["current"], 2.1)
        self.assertEqual(manager.get_latest_metrics()["power"], 26.04)
        self.assertEqual(manager.get_latest_metrics()["temperature"], 31.2)
        self.assertEqual(manager.get_latest_metrics()["efficiency"], 85.5)
        self.assertEqual(manager.get_latest_metrics()["pwm_duty"], 72)

    def test_parse_labeled_packet_updates_live_metrics(self) -> None:
        manager = SerialManager()

        parsed = manager.parse_packet("RPM:1250,Voltage:12.4,Current:2.1,Power:26.04,Efficiency:85.5,Temperature:31.2,PWM:72")

        self.assertTrue(parsed)
        self.assertTrue(manager.has_live_data)
        self.assertEqual(manager.get_latest_metrics()["rpm"], 1250.0)
        self.assertEqual(manager.get_latest_metrics()["voltage"], 12.4)
        self.assertEqual(manager.get_latest_metrics()["current"], 2.1)
        self.assertEqual(manager.get_latest_metrics()["power"], 26.04)
        self.assertEqual(manager.get_latest_metrics()["efficiency"], 85.5)
        self.assertEqual(manager.get_latest_metrics()["temperature"], 31.2)
        self.assertEqual(manager.get_latest_metrics()["pwm_duty"], 72)

    def test_parse_6_value_packet_updates_live_metrics(self) -> None:
        manager = SerialManager()

        # Testing with user's exact packet line format: 1611,12.13,0.60,7.28,30.9,89.0
        parsed = manager.parse_packet("1611,12.13,0.60,7.28,30.9,89.0")

        self.assertTrue(parsed)
        self.assertTrue(manager.has_live_data)
        self.assertEqual(manager.get_latest_metrics()["rpm"], 1611.0)
        self.assertEqual(manager.get_latest_metrics()["voltage"], 12.13)
        self.assertEqual(manager.get_latest_metrics()["current"], 0.60)
        self.assertEqual(manager.get_latest_metrics()["power"], 7.28)
        self.assertEqual(manager.get_latest_metrics()["temperature"], 30.9)
        self.assertEqual(manager.get_latest_metrics()["efficiency"], 89.0)

    def test_parse_null_and_invalid_packet_returns_false(self) -> None:
        manager = SerialManager()
        self.assertFalse(manager.parse_packet(""))
        self.assertFalse(manager.parse_packet("invalid,data"))


if __name__ == "__main__":
    unittest.main()
