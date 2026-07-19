"""
serial_manager.py
-----------------
Serial communication manager for Arduino connection.

Uses PySerial to open a COM port and read/write data to/from an Arduino.
Provides automatic connection attempts, robust error handling, and a single
live telemetry state for the dashboard and graph pages.
"""

from __future__ import annotations

import time

import serial
import serial.tools.list_ports


class SerialManager:
    """Manage serial communication and keep the latest telemetry snapshot."""

    def __init__(self) -> None:
        self._port: str = "COM3"
        self._baud: int = 9600
        self._connected: bool = False
        self._serial: serial.Serial | None = None
        self._last_error: str = ""
        self._latest_metrics: dict[str, float | int] = {
            "rpm": 0.0,
            "voltage": 0.0,
            "current": 0.0,
            "power": 0.0,
            "efficiency": 0.0,
            "temperature": 0.0,
            "pwm_duty": 0,
        }
        self._has_live_data: bool = False
        self._last_packet_time: float | None = None
        self._packet_timestamps: list[float] = []
        self._packet_sizes: list[tuple[float, int]] = []

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #
    def connect(self, port: str, baud_rate: int = 9600) -> bool:
        """Open the serial port."""
        try:
            if self._serial and self._serial.is_open:
                self._serial.close()

            self._port = port
            self._baud = baud_rate

            self._serial = serial.Serial(
                port=port,
                baudrate=baud_rate,
                timeout=0.1,
                write_timeout=0.1,
            )
            # Enable DTR/RTS to support various Arduino models/clones (e.g. CH340)
            try:
                self._serial.dtr = True
                self._serial.rts = True
            except Exception as e:
                print(f"[SerialManager] Warning: could not set DTR/RTS: {e}")

            # Flush any initial connection/reset bootloader garbage from RX buffer
            try:
                self._serial.reset_input_buffer()
            except Exception:
                pass

            self._connected = True
            self._last_error = ""
            self._has_live_data = False
            print(f"[SerialManager] Connected to {port} at {baud_rate} bps")
            return True

        except serial.SerialException as exc:
            self._connected = False
            err_msg = str(exc)
            if "PermissionError" in err_msg or "Access is denied" in err_msg:
                self._last_error = "Port already in use. Please close other serial tools or zombie application processes."
            else:
                self._last_error = err_msg
            print(f"[SerialManager] Connection failed on {port}: {exc}")
            return False
        except Exception as exc:
            self._connected = False
            self._last_error = str(exc)
            print(f"[SerialManager] Unexpected error during connection: {exc}")
            return False

    def disconnect(self) -> None:
        """Close the serial port and clear any live telemetry state."""
        try:
            if self._serial and self._serial.is_open:
                self._serial.close()
        except Exception as e:
            print(f"[SerialManager] Error during disconnect: {e}")
        finally:
            self._connected = False
            self._serial = None
            self._reset_live_data()

    def read_line(self) -> str | None:
        """Read one line from the serial buffer and update live telemetry state."""
        if not self._connected or not self._serial:
            self._reset_live_data()
            return None

        try:
            if self._serial.in_waiting <= 0:
                return None

            raw_bytes = self._serial.readline()
            # Strip null bytes (\x00) and surrounding whitespace
            line = raw_bytes.decode("utf-8", errors="ignore").replace("\x00", "").strip()
            if line and self.parse_packet(line):
                return line
        except Exception as e:
            print(f"[SerialManager] Error reading from port: {e}")
            self._connected = False
            self._reset_live_data()

        return None

    def consume_serial_data(self) -> bool:
        """Consume one serial packet if available and return whether it was parsed."""
        return self.read_line() is not None

    def parse_packet(self, line: str) -> bool:
        """Parse a telemetry packet and store it as the latest live payload.

        Supported packet formats:
        - Positional: RPM,Voltage,Current,Power,Temperature,Efficiency [,PWM,DIR]
        - Labeled: RPM:1500,V:12.0,I:2.5,P:30.0,Temp:38.5,Eff:85.0,PWM:75,DIR:FWD
        """
        if not line:
            return False

        try:
            raw_parts = [part.strip() for part in line.split(",")]
            if len(raw_parts) < 6:
                print(f"[SerialManager] Data format warning: line has less than 6 parts ({len(raw_parts)} parts): {repr(line)}")
                return False

            key_map: dict[str, str] = {}
            for part in raw_parts:
                if ":" in part or "=" in part:
                    delim = ":" if ":" in part else "="
                    k, v = part.split(delim, 1)
                    key_map[k.strip().upper()] = v.strip()

            rpm: float | None = None
            voltage: float | None = None
            current: float | None = None
            power: float | None = None
            efficiency: float | None = None
            temperature: float | None = None
            pwm_duty = self._latest_metrics.get("pwm_duty", 0)
            direction = self._latest_metrics.get("direction", "FWD")

            if key_map:
                for k, v in key_map.items():
                    try:
                        num_val = float(v)
                    except ValueError:
                        num_val = None

                    if k in ("RPM", "SPEED"):
                        rpm = num_val
                    elif k in ("VOLTAGE", "VOLT", "V"):
                        voltage = num_val
                    elif k in ("CURRENT", "CURR", "I", "AMP"):
                        current = num_val
                    elif k in ("POWER", "PWR", "P", "WATT"):
                        power = num_val
                    elif k in ("EFFICIENCY", "EFF", "EFF%"):
                        efficiency = num_val
                    elif k in ("TEMPERATURE", "TEMP", "TMP", "T", "DEG"):
                        temperature = num_val
                    elif k in ("PWM", "DUTY"):
                        if num_val is not None:
                            pwm_duty = int(num_val)
                    elif k in ("DIR", "DIRECTION"):
                        direction = v.upper()

            def _extract_val(idx: int) -> float:
                val_str = raw_parts[idx]
                if ":" in val_str:
                    val_str = val_str.split(":", 1)[1]
                elif "=" in val_str:
                    val_str = val_str.split("=", 1)[1]
                return float(val_str.strip())

            if rpm is None:
                rpm = _extract_val(0)
            if voltage is None:
                voltage = _extract_val(1)
            if current is None:
                current = _extract_val(2)
            if power is None:
                power = _extract_val(3)
            if temperature is None:
                temperature = _extract_val(4)
            if efficiency is None:
                efficiency = _extract_val(5)

            if len(raw_parts) >= 7 and "PWM" not in key_map and "DUTY" not in key_map:
                try:
                    pwm_duty = int(_extract_val(6))
                except (ValueError, IndexError):
                    pass
            if len(raw_parts) >= 8 and "DIR" not in key_map and "DIRECTION" not in key_map:
                direction = raw_parts[7].replace('DIR:', '').strip()

            self._latest_metrics = {
                "rpm": rpm,
                "voltage": voltage,
                "current": current,
                "power": power,
                "efficiency": efficiency,
                "temperature": temperature,
                "pwm_duty": pwm_duty,
                "direction": direction,
            }
            self._has_live_data = True
            self._last_packet_time = time.time()
            self._packet_timestamps.append(self._last_packet_time)
            self._packet_sizes.append((self._last_packet_time, len(line) + 1))
            return True
        except (ValueError, IndexError, AttributeError) as exc:
            print(f"[SerialManager] Parsing error on line {repr(line)}: {exc}")
            self._has_live_data = False
            return False

        self._has_live_data = False
        return False

    def get_latest_metrics(self) -> dict[str, float | int]:
        """Return a copy of the latest telemetry snapshot."""
        return dict(self._latest_metrics)

    def send_command(self, command: str) -> bool:
        """Send a command string to the Arduino."""
        if not self._connected or not self._serial:
            return False

        try:
            self._serial.write(f"{command}\n".encode("utf-8"))
            if command.startswith("PWM:"):
                try:
                    self._latest_metrics["pwm_duty"] = int(command.split(":")[1])
                except Exception:
                    pass
            elif command.startswith("DIR:"):
                self._latest_metrics["direction"] = command.split(":")[1]
            elif command == "STOP":
                self._latest_metrics["pwm_duty"] = 0
            return True
        except Exception as e:
            print(f"[SerialManager] Error sending command: {e}")
            self._connected = False
            self._reset_live_data()
            return False

    def check_connection(self) -> bool:
        """Validate the currently open serial connection without blocking UI loops."""
        if not self._serial or not self._serial.is_open:
            self._connected = False
            self._reset_live_data()
            return False

        try:
            _ = self._serial.in_waiting
            self._connected = True
            return True
        except serial.SerialException as exc:
            self._connected = False
            self._last_error = str(exc)
            self._reset_live_data()
            print(f"[SerialManager] Connection lost: {exc}")
            return False
        except Exception as exc:
            self._connected = False
            self._last_error = str(exc)
            self._reset_live_data()
            print(f"[SerialManager] Connection validation error: {exc}")
            return False

    @staticmethod
    def list_available_ports() -> list[str]:
        """Get list of available COM ports."""
        try:
            ports = []
            for port_info in serial.tools.list_ports.comports():
                ports.append(port_info.device)
            return sorted(ports)
        except Exception as e:
            print(f"[SerialManager] Error listing ports: {e}")
            return []

    def _reset_live_data(self) -> None:
        self._has_live_data = False
        self._last_packet_time = None
        self._packet_timestamps = []
        self._packet_sizes = []
        self._latest_metrics = {
            "rpm": 0.0,
            "voltage": 0.0,
            "current": 0.0,
            "power": 0.0,
            "efficiency": 0.0,
            "temperature": 0.0,
            "pwm_duty": 0,
        }

    # ------------------------------------------------------------------ #
    #  Properties
    # ------------------------------------------------------------------ #
    @property
    def is_connected(self) -> bool:
        """True when a serial port is open and connected."""
        return self._connected

    @property
    def has_live_data(self) -> bool:
        """True when at least one valid serial packet has been parsed."""
        return self._has_live_data

    @property
    def port(self) -> str:
        """Current COM port string."""
        return self._port

    @property
    def baud_rate(self) -> int:
        """Current baud rate."""
        return self._baud

    @property
    def packets_per_second(self) -> int:
        """Calculate rolling packets per second over the last 1.0s."""
        now = time.time()
        self._packet_timestamps = [t for t in self._packet_timestamps if now - t <= 1.0]
        return len(self._packet_timestamps)

    @property
    def data_rate_bps(self) -> int:
        """Calculate rolling data rate in Bytes/sec over the last 1.0s."""
        now = time.time()
        self._packet_sizes = [item for item in self._packet_sizes if now - item[0] <= 1.0]
        return sum(item[1] for item in self._packet_sizes)

    @property
    def last_error(self) -> str:
        """Last error message from connection attempt."""
        return self._last_error
