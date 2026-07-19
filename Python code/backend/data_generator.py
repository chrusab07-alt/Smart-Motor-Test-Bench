"""
data_generator.py
-----------------
Data generator for the Smart Motor Test Bench.
Produces either real motor telemetry data from Arduino via SerialManager,
or realistic-looking simulated data using sine waves, noise, and smooth transitions.
Can be swapped between real and simulated modes on the fly.
"""

import time


class DataGenerator:
    """
    Generates motor sensor readings from serial data (when available) or simulation.

    All public properties are updated by calling :meth:`update` once
    per timer tick. When a SerialManager is attached and connected, real data
    is read from Arduino. Otherwise, the generator falls back to simulation.
    """

    # ------------------------------------------------------------------ #
    #  Public configuration
    # ------------------------------------------------------------------ #
    RPM_BASE: float = 1500.0       # Nominal RPM at 100 % PWM
    VOLTAGE_BASE: float = 12.0     # Nominal supply voltage (V)
    CURRENT_BASE: float = 2.0      # Nominal current draw (A)

    def __init__(self) -> None:
        self._start_time: float = time.time()
        self._tick: int = 0
        self._serial_manager = None  # Will be set later if serial is available
        self._hold_zero: bool = False

        # Control States
        self.is_running: bool = True
        self.direction: str = "FORWARD"
        
        # Session Timer
        self.session_time_seconds: float = 0.0
        self._last_tick_time: float = time.time()

        # Current metric values
        self.rpm: float = 0.0
        self.voltage: float = 0.0
        self.current: float = 0.0
        self.power: float = 0.0
        self.efficiency: float = 0.0
        self.temperature: float = 25.0
        self.pwm_duty: int = 72       # 0-100 %

        # Running statistics
        self.max_rpm: float = 0.0
        self.min_rpm: float = float("inf")
        self.max_voltage: float = 0.0
        self.min_voltage: float = float("inf")
        self.max_current: float = 0.0
        self.min_current: float = float("inf")
        self.max_power: float = 0.0
        self.min_power: float = float("inf")
        self.max_efficiency: float = 0.0
        self.min_efficiency: float = float("inf")
        self.max_temperature: float = 0.0
        self.min_temperature: float = float("inf")
        self.max_pwm_duty: int = 0

        # Sums for averages
        self.sum_rpm: float = 0.0
        self.sum_voltage: float = 0.0
        self.sum_current: float = 0.0
        self.sum_power: float = 0.0
        self.sum_efficiency: float = 0.0

        self.data_points: int = 0
        self._is_using_serial: bool = False

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #
    def set_serial_manager(self, serial_mgr) -> None:
        """
        Attach a SerialManager instance for reading real Arduino data.
        
        Args:
            serial_mgr: The SerialManager instance (or None to disable).
        """
        self._serial_manager = serial_mgr

    def reset_to_idle(self) -> None:
        """Zero all telemetry metrics and stop the motor when serial disconnects."""
        self.is_running = False
        self.pwm_duty = 0
        self.rpm = 0.0
        self.voltage = 0.0
        self.current = 0.0
        self.power = 0.0
        self.efficiency = 0.0
        self.temperature = 0.0
        self.data_points = 0
        self._is_using_serial = False

    def reset_stats(self) -> None:
        """Reset all statistical tracking (max/min/sums) for a new session."""
        self.max_rpm = 0.0
        self.min_rpm = float("inf")
        self.max_voltage = 0.0
        self.min_voltage = float("inf")
        self.max_current = 0.0
        self.min_current = float("inf")
        self.max_power = 0.0
        self.min_power = float("inf")
        self.max_efficiency = 0.0
        self.min_efficiency = float("inf")
        self.max_temperature = 0.0
        self.min_temperature = float("inf")
        self.max_pwm_duty = 0
        self.sum_rpm = 0.0
        self.sum_voltage = 0.0
        self.sum_current = 0.0
        self.sum_power = 0.0
        self.sum_efficiency = 0.0
        self.data_points = 0

    def hold_zero(self, enabled: bool) -> None:
        """Hold all generated telemetry values at zero until live data returns."""
        self._hold_zero = enabled
        if enabled:
            self.reset_to_idle()

    def update(self) -> None:
        """Refresh the generator state from serial telemetry only."""
        now = time.time()
        dt = now - self._last_tick_time
        self._last_tick_time = now
        
        if self.is_running:
            self.session_time_seconds += dt

        if self._hold_zero:
            self.reset_to_idle()
            return

        if self._serial_manager and self._serial_manager.is_connected:
            self._update_from_serial()
        else:
            self._is_using_serial = False
            self.reset_to_idle()

    def _update_from_serial(self) -> None:
        """Copy the latest serial telemetry into the generator state."""
        if self._serial_manager and self._serial_manager.has_live_data:
            metrics = self._serial_manager.get_latest_metrics()
            self._is_using_serial = True
            self.rpm = float(metrics["rpm"])
            self.voltage = float(metrics["voltage"])
            self.current = float(metrics["current"])
            self.power = float(metrics["power"])
            self.efficiency = float(metrics["efficiency"])
            self.temperature = float(metrics["temperature"])
            self.pwm_duty = int(metrics["pwm_duty"])
            if "direction" in metrics:
                self.direction = "FORWARD" if metrics["direction"] == "FWD" else "REVERSE"
            self.data_points += 1
            self._update_stats()
            return

        self._is_using_serial = False
        self.reset_to_idle()

    def set_pwm_duty(self, value: int) -> None:
        """Set the PWM duty cycle (0–100)."""
        self.pwm_duty = max(0, min(100, value))

    def set_running(self, running: bool) -> None:
        """Set motor running state."""
        if running and not self.is_running:
            # Reset timer when a new test begins (Start is pressed)
            self.session_time_seconds = 0.0
            self._last_tick_time = time.time()
            self.reset_stats()
        self.is_running = running

    def set_direction(self, direction: str) -> None:
        """Set motor direction ('FORWARD' or 'REVERSE')."""
        self.direction = direction

    @property
    def uptime(self) -> str:
        """Return a formatted HH:MM:SS uptime string."""
        elapsed = int(time.time() - self._start_time)
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @property
    def session_time_str(self) -> str:
        """Return a formatted HH:MM:SS string for the active session."""
        h, rem = divmod(int(self.session_time_seconds), 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @property
    def sampling_rate(self) -> str:
        """Return a human-readable sampling rate string."""
        return "1000 samples/s"

    @property
    def avg_rpm(self) -> float:
        return self.sum_rpm / self.data_points if self.data_points > 0 else 0.0

    @property
    def avg_voltage(self) -> float:
        return self.sum_voltage / self.data_points if self.data_points > 0 else 0.0

    @property
    def avg_current(self) -> float:
        return self.sum_current / self.data_points if self.data_points > 0 else 0.0

    @property
    def avg_power(self) -> float:
        return self.sum_power / self.data_points if self.data_points > 0 else 0.0

    @property
    def avg_efficiency(self) -> float:
        return self.sum_efficiency / self.data_points if self.data_points > 0 else 0.0

    # ------------------------------------------------------------------ #
    #  Private helpers
    # ------------------------------------------------------------------ #
    def _update_stats(self) -> None:
        """Update running min/max statistics."""
        self.max_rpm = max(self.max_rpm, self.rpm)
        self.min_rpm = min(self.min_rpm, self.rpm)

        self.max_voltage = max(self.max_voltage, self.voltage)
        self.min_voltage = min(self.min_voltage, self.voltage)

        self.max_current = max(self.max_current, self.current)
        self.min_current = min(self.min_current, self.current)

        self.max_power = max(self.max_power, self.power)
        self.min_power = min(self.min_power, self.power)

        self.max_efficiency = max(self.max_efficiency, self.efficiency)
        self.min_efficiency = min(self.min_efficiency, self.efficiency)

        self.max_temperature = max(self.max_temperature, self.temperature)
        self.min_temperature = min(self.min_temperature, self.temperature)

        self.max_pwm_duty = max(self.max_pwm_duty, self.pwm_duty)
        
        self.sum_rpm += self.rpm
        self.sum_voltage += self.voltage
        self.sum_current += self.current
        self.sum_power += self.power
        self.sum_efficiency += self.efficiency
