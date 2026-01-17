"""
Signal Generator Module

Generates deterministic time-series data with seeded randomness.
Uses NumPy for reproducible signal generation.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Generator

from app.models.telemetry import TelemetryPoint, QualityFlag
from app.models.simulation import SensorSpec


class SignalGenerator:
    """
    Generates deterministic sensor signals for simulation.
    
    Uses seeded random number generation to ensure reproducibility.
    The same seed and parameters will always produce identical output.
    """
    
    def __init__(self, seed: int = 42):
        """Initialize with a random seed for reproducibility"""
        self.seed = seed
        self._rng = np.random.default_rng(seed)
        self._base_time: datetime | None = None
    
    def reset(self, seed: int | None = None) -> None:
        """Reset the generator with optional new seed"""
        if seed is not None:
            self.seed = seed
        self._rng = np.random.default_rng(self.seed)
        self._base_time = None
    
    def set_base_time(self, base_time: datetime) -> None:
        """Set the base time for timestamp generation"""
        self._base_time = base_time
    
    def generate_base_signal(
        self,
        duration_sec: float,
        sample_rate: float,
        baseline: float = 100.0,
        noise_std: float = 0.05,
        trend_rate: float = 0.0,
        oscillation_amplitude: float = 0.0,
        oscillation_period_sec: float = 60.0,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Generate a base signal with optional trend and oscillation.
        
        Args:
            duration_sec: Duration of signal in seconds
            sample_rate: Samples per second
            baseline: Mean value of the signal
            noise_std: Standard deviation of Gaussian noise (relative to baseline)
            trend_rate: Linear trend per second
            oscillation_amplitude: Amplitude of sine wave oscillation
            oscillation_period_sec: Period of sine wave in seconds
            
        Returns:
            Tuple of (time_array, signal_array)
        """
        n_samples = int(duration_sec * sample_rate)
        t = np.linspace(0, duration_sec, n_samples)
        
        # Base value
        signal = np.full(n_samples, baseline, dtype=np.float64)
        
        # Add linear trend
        if trend_rate != 0:
            signal += trend_rate * t
        
        # Add oscillation (sine wave)
        if oscillation_amplitude != 0:
            omega = 2 * np.pi / oscillation_period_sec
            signal += oscillation_amplitude * np.sin(omega * t)
        
        # Add Gaussian noise
        if noise_std > 0:
            noise = self._rng.normal(0, noise_std * baseline, n_samples)
            signal += noise
        
        return t, signal
    
    def generate_sensor_signal(
        self,
        sensor: SensorSpec,
        duration_sec: float,
        sample_rate: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Generate signal for a specific sensor configuration.
        
        Args:
            sensor: Sensor specification
            duration_sec: Duration in seconds
            sample_rate: Samples per second
            
        Returns:
            Tuple of (time_array, signal_array)
        """
        return self.generate_base_signal(
            duration_sec=duration_sec,
            sample_rate=sample_rate,
            baseline=sensor.baseline_value,
            noise_std=sensor.noise_std,
            trend_rate=sensor.trend_rate,
            oscillation_amplitude=sensor.oscillation_amplitude,
            oscillation_period_sec=sensor.oscillation_period_sec,
        )
    
    def generate_telemetry_stream(
        self,
        sensor: SensorSpec,
        duration_sec: float,
        sample_rate: float,
        base_time: datetime | None = None,
    ) -> Generator[TelemetryPoint, None, None]:
        """
        Generate a stream of TelemetryPoint objects.
        
        Args:
            sensor: Sensor specification
            duration_sec: Duration in seconds
            sample_rate: Samples per second
            base_time: Base timestamp (defaults to now)
            
        Yields:
            TelemetryPoint objects
        """
        if base_time is None:
            base_time = self._base_time or datetime.utcnow()
        
        t_array, signal_array = self.generate_sensor_signal(
            sensor, duration_sec, sample_rate
        )
        
        for i, (t, value) in enumerate(zip(t_array, signal_array)):
            timestamp = base_time + timedelta(seconds=float(t))
            yield TelemetryPoint(
                tag_id=sensor.tag_id,
                timestamp=timestamp,
                value=float(value),
                quality=QualityFlag.GOOD,
                metadata={"sample_index": i}
            )
    
    def generate_multiple_sensors(
        self,
        sensors: list[SensorSpec],
        duration_sec: float,
        sample_rate: float,
        base_time: datetime | None = None,
    ) -> dict[str, list[TelemetryPoint]]:
        """
        Generate telemetry for multiple sensors.
        
        Args:
            sensors: List of sensor specifications
            duration_sec: Duration in seconds
            sample_rate: Samples per second
            base_time: Base timestamp
            
        Returns:
            Dict mapping tag_id to list of TelemetryPoint
        """
        if base_time is None:
            base_time = self._base_time or datetime.utcnow()
        
        result = {}
        for sensor in sensors:
            points = list(self.generate_telemetry_stream(
                sensor, duration_sec, sample_rate, base_time
            ))
            result[sensor.tag_id] = points
        
        return result
    
    def get_value_at_time(
        self,
        sensor: SensorSpec,
        time_sec: float,
    ) -> float:
        """
        Get the deterministic value for a sensor at a specific time.
        
        This allows point queries without generating the full signal.
        """
        # Recreate RNG state for this specific point
        # Use a sub-seed based on sensor and time for reproducibility
        point_seed = hash((self.seed, sensor.tag_id, int(time_sec * 1000))) % (2**32)
        point_rng = np.random.default_rng(point_seed)
        
        value = sensor.baseline_value
        
        # Add trend
        if sensor.trend_rate != 0:
            value += sensor.trend_rate * time_sec
        
        # Add oscillation
        if sensor.oscillation_amplitude != 0:
            omega = 2 * np.pi / sensor.oscillation_period_sec
            value += sensor.oscillation_amplitude * np.sin(omega * time_sec)
        
        # Add noise
        if sensor.noise_std > 0:
            noise = point_rng.normal(0, sensor.noise_std * sensor.baseline_value)
            value += noise
        
        return float(value)
