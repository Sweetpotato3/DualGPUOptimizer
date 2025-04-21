"""
CPU-based memory pattern analysis.

Implements memory usage pattern detection algorithms that run exclusively on CPU
to avoid consuming GPU memory during analysis.
"""

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Dict, List, Optional, Any
import threading

import numpy as np

try:
    from dualgpuopt.services.resource_manager import get_resource_manager

    resource_manager = get_resource_manager()
    resource_manager_available = True
except ImportError:
    resource_manager_available = False

# Setup logging
logger = logging.getLogger("DualGPUOpt.Memory.CPUAnalyzer")

class PatternType(str, Enum):
    """Types of memory usage patterns that can be detected."""
    GROWTH = "growth"           # Steady memory growth
    LEAK = "leak"               # Significant memory leak
    FRAGMENTATION = "fragmentation"  # Memory fragmentation
    IMBALANCE = "imbalance"     # Uneven memory distribution
    STABLE = "stable"           # Stable memory usage
    FLUCTUATION = "fluctuation" # Regular memory fluctuations
    SPIKE = "spike"             # Sudden memory spikes
    UNKNOWN = "unknown"         # Unknown pattern


class SeverityLevel(str, Enum):
    """Severity levels for detected patterns."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PatternResult:
    """Results of a memory pattern analysis."""

    def __init__(
        self,
        pattern_type: PatternType,
        severity: SeverityLevel,
        details: Dict[str, Any],
        recommendation: str
    ):
        """
        Initialize a pattern result.

        Args:
            pattern_type: Type of pattern detected
            severity: Severity level of the pattern
            details: Additional details about the pattern
            recommendation: Recommended action to address the pattern
        """
        self.pattern_type = pattern_type
        self.severity = severity
        self.details = details
        self.recommendation = recommendation
        self.timestamp = time.time()


class CPUMemoryAnalyzer:
    """
    Analyzes GPU memory usage patterns using CPU resources.

    This class implements memory analysis algorithms that run entirely on
    CPU to avoid consuming valuable GPU resources during analysis.
    """

    def __init__(self):
        """Initialize the CPU memory analyzer."""
        self._lock = threading.RLock()
        self._analysis_cache: Dict[str, PatternResult] = {}
        self._last_analysis_time = 0
        self._analysis_interval = 5.0  # Only analyze every 5 seconds by default

    def analyze_memory_samples(
        self,
        samples: List[int],
        timestamps: List[float],
        gpu_index: int,
        total_memory: int,
        force_refresh: bool = False
    ) -> List[PatternResult]:
        """
        Analyze memory usage samples to detect patterns.

        Args:
            samples: List of memory usage samples (in MB)
            timestamps: List of timestamps for each sample
            gpu_index: Index of the GPU being analyzed
            total_memory: Total memory available on the GPU (in MB)
            force_refresh: Force a fresh analysis even if cached

        Returns:
            List of detected patterns
        """
        # Check if we should use a cached result
        cache_key = f"gpu{gpu_index}"
        current_time = time.time()

        with self._lock:
            if (
                not force_refresh and
                cache_key in self._analysis_cache and
                current_time - self._last_analysis_time < self._analysis_interval
            ):
                return [self._analysis_cache[cache_key]]

        # Run the analysis on CPU
        if resource_manager_available:
            results = resource_manager.run_on_cpu(
                self._analyze_samples_impl,
                samples,
                timestamps,
                gpu_index,
                total_memory
            )
        else:
            # Fallback to direct implementation
            results = self._analyze_samples_impl(samples, timestamps, gpu_index, total_memory)

        # Update the cache
        with self._lock:
            if results:
                self._analysis_cache[cache_key] = results[0]
                self._last_analysis_time = current_time

        return results

    def _analyze_samples_impl(
        self,
        samples: List[int],
        timestamps: List[float],
        gpu_index: int,
        total_memory: int
    ) -> List[PatternResult]:
        """
        Implementation of the memory analysis algorithm.
        This runs on CPU to avoid VRAM usage.

        Args:
            samples: List of memory usage samples (in MB)
            timestamps: List of timestamps for each sample
            gpu_index: Index of the GPU being analyzed
            total_memory: Total memory available on the GPU (in MB)

        Returns:
            List of detected patterns
        """
        if not samples or len(samples) < 5:
            return []

        results = []

        # Convert to numpy arrays for efficient processing
        try:
            sample_array = np.array(samples, dtype=np.float64)
            time_array = np.array(timestamps, dtype=np.float64)
            time_diff = time_array - time_array[0]  # Time since start
        except Exception as e:
            logger.error(f"Error converting memory samples to numpy array: {e}")
            return []

        # Detect memory growth pattern
        growth_result = self._detect_growth_pattern(
            sample_array, time_diff, gpu_index, total_memory
        )
        if growth_result:
            results.append(growth_result)

        # Detect memory imbalance (only if we have data from multiple GPUs)
        # This would require data from other GPUs, which we don't have here

        # Detect memory fragmentation pattern
        frag_result = self._detect_fragmentation_pattern(
            sample_array, time_diff, gpu_index, total_memory
        )
        if frag_result:
            results.append(frag_result)

        # Detect memory spikes
        spike_result = self._detect_spike_pattern(
            sample_array, time_diff, gpu_index, total_memory
        )
        if spike_result:
            results.append(spike_result)

        # If no patterns detected, report stable pattern
        if not results and len(samples) >= 10:
            results.append(
                PatternResult(
                    PatternType.STABLE,
                    SeverityLevel.LOW,
                    {
                        "mean": float(np.mean(sample_array)),
                        "std_dev": float(np.std(sample_array)),
                        "duration": float(time_diff[-1]),
                    },
                    "Memory usage is stable. No action needed."
                )
            )

        return results

    def _detect_growth_pattern(
        self,
        samples: np.ndarray,
        time_diff: np.ndarray,
        gpu_index: int,
        total_memory: int
    ) -> Optional[PatternResult]:
        """
        Detect memory growth pattern using linear regression.

        Args:
            samples: Numpy array of memory samples
            time_diff: Numpy array of time differences
            gpu_index: GPU index being analyzed
            total_memory: Total GPU memory in MB

        Returns:
            PatternResult if growth detected, None otherwise
        """
        try:
            # Perform linear regression to detect growth trend
            if len(samples) < 5:
                return None

            # Calculate slope (MB/s)
            slope, intercept = np.polyfit(time_diff, samples, 1)

            # Calculate R-squared to determine fit quality
            p = np.poly1d([slope, intercept])
            predicted = p(time_diff)
            ss_total = np.sum((samples - np.mean(samples))**2)
            ss_residual = np.sum((samples - predicted)**2)
            r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0

            # Determine if growth is significant
            # Slope is in MB/second, convert to MB/minute for easier interpretation
            slope_mb_per_min = slope * 60

            if slope_mb_per_min > 50 and r_squared > 0.7:
                # Critical growth
                severity = SeverityLevel.CRITICAL
                recommendation = (
                    "Critical memory growth detected. Immediate intervention required. "
                    "Consider terminating the process or implementing emergency memory recovery."
                )
            elif slope_mb_per_min > 20 and r_squared > 0.6:
                # High growth
                severity = SeverityLevel.HIGH
                recommendation = (
                    "Significant memory growth detected. Review memory usage patterns "
                    "and consider implementing memory cleanup after each inference batch."
                )
            elif slope_mb_per_min > 5 and r_squared > 0.5:
                # Medium growth
                severity = SeverityLevel.MEDIUM
                recommendation = (
                    "Moderate memory growth detected. Monitor the situation and consider "
                    "implementing periodic memory cleanup if growth continues."
                )
            elif slope_mb_per_min > 1 and r_squared > 0.4:
                # Low growth
                severity = SeverityLevel.LOW
                recommendation = (
                    "Minimal memory growth detected. No immediate action required, "
                    "but continue monitoring for changes in the pattern."
                )
            else:
                # No significant growth
                return None

            # Calculate time until OOM at current growth rate
            if slope > 0:
                remaining_mb = total_memory - samples[-1]
                time_to_oom_seconds = remaining_mb / slope if slope > 0 else float('inf')
                time_to_oom_minutes = time_to_oom_seconds / 60
            else:
                time_to_oom_minutes = float('inf')

            return PatternResult(
                PatternType.GROWTH,
                severity,
                {
                    "slope_mb_per_min": float(slope_mb_per_min),
                    "r_squared": float(r_squared),
                    "time_to_oom_minutes": float(time_to_oom_minutes) if time_to_oom_minutes < 1e6 else float('inf'),
                    "current_mb": float(samples[-1]),
                    "total_mb": float(total_memory),
                },
                recommendation
            )
        except Exception as e:
            logger.error(f"Error detecting memory growth pattern: {e}")
            return None

    def _detect_fragmentation_pattern(
        self,
        samples: np.ndarray,
        time_diff: np.ndarray,
        gpu_index: int,
        total_memory: int
    ) -> Optional[PatternResult]:
        """
        Detect memory fragmentation pattern.

        Args:
            samples: Numpy array of memory samples
            time_diff: Numpy array of time differences
            gpu_index: GPU index being analyzed
            total_memory: Total GPU memory in MB

        Returns:
            PatternResult if fragmentation detected, None otherwise
        """
        try:
            if len(samples) < 10:
                return None

            # Look for sawtooth pattern - repeating up and down with overall upward trend
            # Calculate local minima and maxima
            peaks = []
            valleys = []

            for i in range(1, len(samples) - 1):
                if samples[i] > samples[i-1] and samples[i] > samples[i+1]:
                    peaks.append(i)
                elif samples[i] < samples[i-1] and samples[i] < samples[i+1]:
                    valleys.append(i)

            # We need at least 2 peaks and 2 valleys to detect a pattern
            if len(peaks) < 2 or len(valleys) < 2:
                return None

            # Calculate metrics
            peak_values = samples[peaks]
            valley_values = samples[valleys]

            # Check if valley floor is rising (a key fragmentation indicator)
            rising_floor = False
            if len(valley_values) >= 3:
                valley_slope, _ = np.polyfit(range(len(valley_values)), valley_values, 1)
                rising_floor = valley_slope > 0.5  # MB per sample

            # Check peak-to-valley ratio
            avg_peak = np.mean(peak_values)
            avg_valley = np.mean(valley_values)

            if avg_peak > 0:
                peak_valley_ratio = (avg_peak - avg_valley) / avg_peak
            else:
                peak_valley_ratio = 0

            # Detect fragmentation based on rising valley floor and peak-valley cycles
            if rising_floor and peak_valley_ratio < 0.3 and len(peaks) >= 3:
                # High fragmentation
                severity = SeverityLevel.HIGH
                recommendation = (
                    "Memory fragmentation detected. Consider implementing complete memory "
                    "release between model executions or switching to a session-based "
                    "approach to manage memory allocation."
                )
            elif rising_floor and peak_valley_ratio < 0.5 and len(peaks) >= 2:
                # Medium fragmentation
                severity = SeverityLevel.MEDIUM
                recommendation = (
                    "Moderate memory fragmentation detected. Consider periodic complete "
                    "memory reset to address fragmentation issues."
                )
            else:
                return None

            return PatternResult(
                PatternType.FRAGMENTATION,
                severity,
                {
                    "peak_valley_ratio": float(peak_valley_ratio),
                    "peaks_count": len(peaks),
                    "rising_floor": rising_floor,
                    "avg_peak_mb": float(avg_peak),
                    "avg_valley_mb": float(avg_valley),
                },
                recommendation
            )
        except Exception as e:
            logger.error(f"Error detecting memory fragmentation pattern: {e}")
            return None

    def _detect_spike_pattern(
        self,
        samples: np.ndarray,
        time_diff: np.ndarray,
        gpu_index: int,
        total_memory: int
    ) -> Optional[PatternResult]:
        """
        Detect memory spike pattern.

        Args:
            samples: Numpy array of memory samples
            time_diff: Numpy array of time differences
            gpu_index: GPU index being analyzed
            total_memory: Total GPU memory in MB

        Returns:
            PatternResult if spikes detected, None otherwise
        """
        try:
            if len(samples) < 5:
                return None

            # Calculate the mean and standard deviation
            mean_memory = np.mean(samples)
            std_dev = np.std(samples)

            if std_dev == 0:
                return None  # No variation

            # Find samples that exceed threshold (mean + 2*std_dev)
            threshold = mean_memory + 2 * std_dev
            spikes = samples > threshold

            if not np.any(spikes):
                return None

            # Count spikes and calculate their magnitude
            spike_indices = np.where(spikes)[0]
            spike_values = samples[spike_indices]
            max_spike = np.max(spike_values)
            spike_magnitude = (max_spike - mean_memory) / mean_memory if mean_memory > 0 else 0

            # Determine severity based on spike magnitude and count
            if spike_magnitude > 0.5 and len(spike_indices) >= 3:
                # High severity - multiple large spikes
                severity = SeverityLevel.HIGH
                recommendation = (
                    "Multiple large memory spikes detected. Consider reducing batch size "
                    "or implementing batch splitting to avoid these spikes."
                )
            elif spike_magnitude > 0.3 or len(spike_indices) >= 5:
                # Medium severity
                severity = SeverityLevel.MEDIUM
                recommendation = (
                    "Memory usage spikes detected. Monitor for potential out-of-memory "
                    "conditions and consider optimizing memory usage during peak operations."
                )
            elif spike_magnitude > 0.2:
                # Low severity
                severity = SeverityLevel.LOW
                recommendation = (
                    "Minor memory spikes detected. No immediate action required "
                    "but continue monitoring memory patterns."
                )
            else:
                return None

            return PatternResult(
                PatternType.SPIKE,
                severity,
                {
                    "spike_count": int(np.sum(spikes)),
                    "max_spike_mb": float(max_spike),
                    "spike_magnitude": float(spike_magnitude),
                    "mean_memory_mb": float(mean_memory),
                    "std_dev_mb": float(std_dev),
                },
                recommendation
            )
        except Exception as e:
            logger.error(f"Error detecting memory spike pattern: {e}")
            return None


# Singleton instance
_cpu_memory_analyzer: Optional[CPUMemoryAnalyzer] = None


def get_cpu_memory_analyzer() -> CPUMemoryAnalyzer:
    """
    Get the singleton CPU memory analyzer instance.

    Returns:
        The global CPU memory analyzer instance
    """
    global _cpu_memory_analyzer
    if _cpu_memory_analyzer is None:
        _cpu_memory_analyzer = CPUMemoryAnalyzer()
    return _cpu_memory_analyzer