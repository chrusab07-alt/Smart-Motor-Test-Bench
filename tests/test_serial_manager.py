import unittest

from backend.serial_manager import SerialManager


class SerialManagerTelemetryTests(unittest.TestCase):
    def test_parse_packet_updates_live_metrics(self) -> None:
        manager = SerialManager()

        parsed = manager.parse_packet("1250,12.4,2.1,26.04,85.5,31.2,72")

        self.assertTrue(parsed)
        self.assertTrue(manager.has_live_data)
        self.assertEqual(manager.get_latest_metrics()["rpm"], 1250.0)
        self.assertEqual(manager.get_latest_metrics()["voltage"], 12.4)
        self.assertEqual(manager.get_latest_metrics()["current"], 2.1)
        self.assertEqual(manager.get_latest_metrics()["power"], 26.04)
        self.assertEqual(manager.get_latest_metrics()["efficiency"], 85.5)
        self.assertEqual(manager.get_latest_metrics()["temperature"], 31.2)
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

        parsed = manager.parse_packet("1450,12.15,0.42,5.10,0,31.6")

        self.assertTrue(parsed)
        self.assertTrue(manager.has_live_data)
        self.assertEqual(manager.get_latest_metrics()["rpm"], 1450.0)
        self.assertEqual(manager.get_latest_metrics()["voltage"], 12.15)
        self.assertEqual(manager.get_latest_metrics()["current"], 0.42)
        self.assertEqual(manager.get_latest_metrics()["power"], 5.10)
        self.assertEqual(manager.get_latest_metrics()["efficiency"], 0.0)
        self.assertEqual(manager.get_latest_metrics()["temperature"], 31.6)


if __name__ == "__main__":
    unittest.main()
