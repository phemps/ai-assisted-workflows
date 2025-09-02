#!/usr/bin/env python3
"""
Memory Management System for High-Performance Code Analysis

Monitors memory usage and automatically adjusts processing parameters to prevent
out-of-memory errors while maximizing throughput. Integrates with AsyncSymbolProcessor
for memory-aware concurrent processing.

Key Features:
- Real-time memory monitoring with configurable thresholds
- Automatic batch size adjustment based on available memory
- Memory pressure detection and throttling
- Garbage collection optimization
- Resource cleanup and memory leak detection
"""

from __future__ import annotations

import gc
import logging
import sys
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Callable, Any, List
from contextlib import contextmanager

# Setup import paths
try:
    from utils import path_resolver  # noqa: F401
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)

# Try to import psutil for advanced memory monitoring
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """Configuration for memory management system."""

    # Memory thresholds (as percentage of total system memory)
    warning_threshold: float = 75.0  # Start warning at 75%
    throttle_threshold: float = 85.0  # Start throttling at 85%
    critical_threshold: float = 95.0  # Critical level at 95%

    # Batch size management
    min_batch_size: int = 5
    max_batch_size: int = 100
    default_batch_size: int = 20

    # Memory monitoring
    monitor_interval: float = 5.0  # Check every 5 seconds
    enable_auto_gc: bool = True  # Enable automatic garbage collection
    gc_threshold_mb: float = 200.0  # Trigger GC after 200MB growth

    # Process limits
    max_memory_mb: Optional[float] = None  # Process memory limit
    enable_memory_profiling: bool = False  # Detailed memory profiling


class MemoryStats:
    """Track memory usage statistics."""

    def __init__(self):
        self.peak_usage_mb: float = 0.0
        self.current_usage_mb: float = 0.0
        self.system_total_mb: float = 0.0
        self.available_mb: float = 0.0
        self.usage_percentage: float = 0.0
        self.gc_collections: int = 0
        self.memory_warnings: int = 0
        self.throttling_events: int = 0
        self.last_update: float = time.time()

    def update(self, usage_mb: float, total_mb: float, available_mb: float):
        """Update memory statistics."""
        self.current_usage_mb = usage_mb
        self.system_total_mb = total_mb
        self.available_mb = available_mb
        self.usage_percentage = (usage_mb / total_mb * 100) if total_mb > 0 else 0
        self.peak_usage_mb = max(self.peak_usage_mb, usage_mb)
        self.last_update = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "current_usage_mb": self.current_usage_mb,
            "peak_usage_mb": self.peak_usage_mb,
            "system_total_mb": self.system_total_mb,
            "available_mb": self.available_mb,
            "usage_percentage": self.usage_percentage,
            "gc_collections": self.gc_collections,
            "memory_warnings": self.memory_warnings,
            "throttling_events": self.throttling_events,
            "last_update": self.last_update,
        }


class MemoryManager:
    """
    Intelligent memory management for high-performance processing.

    Monitors system and process memory usage, automatically adjusts processing
    parameters, and provides memory-aware processing capabilities.
    """

    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        Initialize memory manager.

        Args:
            config: Memory management configuration (uses defaults if None)
        """
        self.config = config or MemoryConfig()
        self.stats = MemoryStats()

        # Memory monitoring state
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Memory tracking
        self._last_gc_usage = 0.0
        self._baseline_usage = 0.0

        # Callbacks for memory events
        self._warning_callbacks: List[Callable] = []
        self._throttle_callbacks: List[Callable] = []
        self._critical_callbacks: List[Callable] = []

        # Initialize memory monitoring
        self._initialize_monitoring()

        logger.info(
            f"MemoryManager initialized: thresholds={self.config.warning_threshold}%/"
            f"{self.config.throttle_threshold}%/{self.config.critical_threshold}%"
        )

    def _initialize_monitoring(self) -> None:
        """Initialize memory monitoring capabilities."""
        if not HAS_PSUTIL:
            logger.warning("psutil not available - using basic memory monitoring")

        # Get initial memory baseline
        self._update_memory_stats()
        self._baseline_usage = self.stats.current_usage_mb
        self._last_gc_usage = self._baseline_usage

        # Start monitoring thread if enabled
        if self.config.monitor_interval > 0:
            self.start_monitoring()

    def start_monitoring(self) -> None:
        """Start background memory monitoring."""
        if self._monitoring:
            logger.warning("Memory monitoring already active")
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="MemoryMonitor"
        )
        self._monitor_thread.start()
        logger.info("Memory monitoring started")

    def stop_monitoring(self) -> None:
        """Stop background memory monitoring."""
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        logger.info("Memory monitoring stopped")

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._monitoring:
            try:
                with self._lock:
                    self._update_memory_stats()
                    self._check_memory_thresholds()
                    self._check_gc_triggers()

                time.sleep(self.config.monitor_interval)

            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(self.config.monitor_interval)

    def _update_memory_stats(self) -> None:
        """Update current memory statistics."""
        if HAS_PSUTIL:
            # Use psutil for accurate memory information
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()

            self.stats.update(
                usage_mb=process_memory.rss / (1024 * 1024),
                total_mb=memory.total / (1024 * 1024),
                available_mb=memory.available / (1024 * 1024),
            )
        else:
            # Fallback to basic memory estimation
            import resource

            # Get process memory usage
            usage = resource.getrusage(resource.RUSAGE_SELF)
            process_mb = (
                usage.ru_maxrss / 1024
            )  # Convert KB to MB on Linux, already MB on macOS

            # Estimate system memory (rough approximation)
            try:
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.read()
                    total_kb = int(
                        [
                            line.split()[1]
                            for line in meminfo.split("\n")
                            if "MemTotal" in line
                        ][0]
                    )
                    available_kb = int(
                        [
                            line.split()[1]
                            for line in meminfo.split("\n")
                            if "MemAvailable" in line
                        ][0]
                    )
                    total_mb = total_kb / 1024
                    available_mb = available_kb / 1024
            except (FileNotFoundError, IndexError, ValueError):
                # Fallback estimates
                total_mb = 8192.0  # Assume 8GB
                available_mb = max(
                    4096.0, total_mb - process_mb
                )  # Conservative estimate

            self.stats.update(
                usage_mb=process_mb, total_mb=total_mb, available_mb=available_mb
            )

    def _check_memory_thresholds(self) -> None:
        """Check memory usage against thresholds and trigger callbacks."""
        usage_percent = self.stats.usage_percentage

        if usage_percent >= self.config.critical_threshold:
            self.stats.memory_warnings += 1
            logger.critical(f"Critical memory usage: {usage_percent:.1f}%")
            for callback in self._critical_callbacks:
                try:
                    callback(self.stats)
                except Exception as e:
                    logger.error(f"Critical callback failed: {e}")

        elif usage_percent >= self.config.throttle_threshold:
            self.stats.throttling_events += 1
            logger.warning(f"High memory usage, throttling: {usage_percent:.1f}%")
            for callback in self._throttle_callbacks:
                try:
                    callback(self.stats)
                except Exception as e:
                    logger.error(f"Throttle callback failed: {e}")

        elif usage_percent >= self.config.warning_threshold:
            self.stats.memory_warnings += 1
            logger.info(f"Memory usage warning: {usage_percent:.1f}%")
            for callback in self._warning_callbacks:
                try:
                    callback(self.stats)
                except Exception as e:
                    logger.error(f"Warning callback failed: {e}")

    def _check_gc_triggers(self) -> None:
        """Check if garbage collection should be triggered."""
        if not self.config.enable_auto_gc:
            return

        current_usage = self.stats.current_usage_mb
        usage_growth = current_usage - self._last_gc_usage

        if usage_growth >= self.config.gc_threshold_mb:
            logger.debug(f"Triggering GC: memory grew by {usage_growth:.1f}MB")
            collected = gc.collect()
            self.stats.gc_collections += 1
            self._last_gc_usage = current_usage

            if collected > 0:
                logger.debug(f"GC collected {collected} objects")

    def get_current_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        with self._lock:
            self._update_memory_stats()
            return self.stats

    def should_throttle(self) -> bool:
        """Check if processing should be throttled due to memory pressure."""
        with self._lock:
            self._update_memory_stats()
            return self.stats.usage_percentage >= self.config.throttle_threshold

    def is_memory_critical(self) -> bool:
        """Check if memory usage is at critical levels."""
        with self._lock:
            self._update_memory_stats()
            return self.stats.usage_percentage >= self.config.critical_threshold

    def calculate_optimal_batch_size(
        self, base_batch_size: Optional[int] = None
    ) -> int:
        """
        Calculate optimal batch size based on current memory usage.

        Args:
            base_batch_size: Base batch size to adjust (uses config default if None)

        Returns:
            Optimal batch size for current memory conditions
        """
        if base_batch_size is None:
            base_batch_size = self.config.default_batch_size

        with self._lock:
            self._update_memory_stats()
            usage_percent = self.stats.usage_percentage

        # Adjust batch size based on memory pressure
        if usage_percent >= self.config.critical_threshold:
            # Critical: use minimum batch size
            return self.config.min_batch_size
        elif usage_percent >= self.config.throttle_threshold:
            # High usage: reduce batch size by 50%
            return max(self.config.min_batch_size, base_batch_size // 2)
        elif usage_percent >= self.config.warning_threshold:
            # Warning: reduce batch size by 25%
            return max(self.config.min_batch_size, int(base_batch_size * 0.75))
        else:
            # Normal usage: can use larger batch size
            return min(self.config.max_batch_size, base_batch_size)

    def estimate_memory_for_files(
        self, file_count: int, avg_symbols_per_file: int = 50
    ) -> float:
        """
        Estimate memory requirements for processing files.

        Args:
            file_count: Number of files to process
            avg_symbols_per_file: Average symbols per file estimate

        Returns:
            Estimated memory usage in MB
        """
        # Rough estimates based on observed usage patterns
        # Each symbol: ~1KB metadata + embedding data
        # Each file: ~10KB base overhead
        # ChromaDB overhead: ~50% additional

        symbol_count = file_count * avg_symbols_per_file
        base_memory = (file_count * 0.01) + (symbol_count * 0.001)  # MB
        chromadb_overhead = base_memory * 0.5
        total_estimate = base_memory + chromadb_overhead + 100  # 100MB base overhead

        return total_estimate

    def can_process_files(
        self, file_count: int, avg_symbols_per_file: int = 50
    ) -> bool:
        """
        Check if files can be processed within memory limits.

        Args:
            file_count: Number of files to process
            avg_symbols_per_file: Average symbols per file estimate

        Returns:
            True if processing is recommended
        """
        estimated_memory = self.estimate_memory_for_files(
            file_count, avg_symbols_per_file
        )
        current_stats = self.get_current_stats()

        # Check if we have enough available memory
        required_memory = estimated_memory + current_stats.current_usage_mb
        memory_limit = current_stats.system_total_mb * (
            self.config.throttle_threshold / 100
        )

        return required_memory < memory_limit

    @contextmanager
    def memory_monitoring_context(self, description: str = "operation"):
        """
        Context manager for monitoring memory usage during an operation.

        Args:
            description: Description of the operation being monitored
        """
        start_stats = self.get_current_stats()
        start_time = time.time()

        logger.info(
            f"Starting {description} - Memory: {start_stats.current_usage_mb:.1f}MB"
        )

        try:
            yield start_stats
        finally:
            end_stats = self.get_current_stats()
            duration = time.time() - start_time
            memory_delta = end_stats.current_usage_mb - start_stats.current_usage_mb

            logger.info(
                f"Completed {description} in {duration:.2f}s - "
                f"Memory: {end_stats.current_usage_mb:.1f}MB ({memory_delta:+.1f}MB)"
            )

    def add_warning_callback(self, callback: Callable[[MemoryStats], None]) -> None:
        """Add callback for memory warning events."""
        self._warning_callbacks.append(callback)

    def add_throttle_callback(self, callback: Callable[[MemoryStats], None]) -> None:
        """Add callback for memory throttling events."""
        self._throttle_callbacks.append(callback)

    def add_critical_callback(self, callback: Callable[[MemoryStats], None]) -> None:
        """Add callback for critical memory events."""
        self._critical_callbacks.append(callback)

    def force_garbage_collection(self) -> int:
        """Force garbage collection and return number of objects collected."""
        logger.info("Forcing garbage collection")
        collected = gc.collect()
        self.stats.gc_collections += 1
        self._last_gc_usage = self.stats.current_usage_mb

        # Update stats after GC
        self._update_memory_stats()

        logger.info(
            f"GC collected {collected} objects, memory now: {self.stats.current_usage_mb:.1f}MB"
        )
        return collected

    def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory usage report."""
        current_stats = self.get_current_stats()

        return {
            "timestamp": time.time(),
            "memory_stats": current_stats.to_dict(),
            "config": {
                "warning_threshold": self.config.warning_threshold,
                "throttle_threshold": self.config.throttle_threshold,
                "critical_threshold": self.config.critical_threshold,
                "batch_size_range": [
                    self.config.min_batch_size,
                    self.config.max_batch_size,
                ],
                "gc_enabled": self.config.enable_auto_gc,
            },
            "recommendations": self._get_memory_recommendations(current_stats),
            "monitoring_active": self._monitoring,
        }

    def _get_memory_recommendations(self, stats: MemoryStats) -> List[str]:
        """Get memory usage recommendations."""
        recommendations = []

        if stats.usage_percentage > self.config.critical_threshold:
            recommendations.append(
                "CRITICAL: Consider reducing batch size or freeing memory"
            )
        elif stats.usage_percentage > self.config.throttle_threshold:
            recommendations.append("HIGH: Processing may be throttled, monitor closely")
        elif stats.usage_percentage > self.config.warning_threshold:
            recommendations.append("MODERATE: Memory usage elevated but manageable")
        else:
            recommendations.append("NORMAL: Memory usage within acceptable limits")

        if stats.gc_collections > 10:
            recommendations.append(
                "Consider tuning GC thresholds if frequent collections"
            )

        if stats.throttling_events > 5:
            recommendations.append(
                "Frequent throttling detected - consider reducing workload"
            )

        return recommendations

    def __del__(self):
        """Cleanup when memory manager is destroyed."""
        try:
            self.stop_monitoring()
        except Exception:
            pass  # Ignore errors during cleanup


# Utility functions for integration


def create_memory_aware_processor(
    processor_class, memory_limit_mb: float = 1500.0, **processor_kwargs
):
    """
    Create a processor with integrated memory management.

    Args:
        processor_class: Processor class to create
        memory_limit_mb: Memory limit in MB
        **processor_kwargs: Additional arguments for processor

    Returns:
        Processor instance with memory management
    """
    # Create memory manager
    memory_config = MemoryConfig()
    memory_manager = MemoryManager(memory_config)

    # Create processor with memory integration
    processor = processor_class(memory_limit_mb=memory_limit_mb, **processor_kwargs)

    # Integrate memory manager
    if hasattr(processor, "set_memory_manager"):
        processor.set_memory_manager(memory_manager)

    return processor, memory_manager


if __name__ == "__main__":
    # Test memory manager functionality
    def test_memory_manager():
        """Test memory manager with sample operations."""
        manager = MemoryManager()

        print("Initial memory stats:")
        stats = manager.get_current_stats()
        print(
            f"  Usage: {stats.current_usage_mb:.1f}MB ({stats.usage_percentage:.1f}%)"
        )
        print(f"  Available: {stats.available_mb:.1f}MB")

        # Test batch size calculation
        batch_size = manager.calculate_optimal_batch_size(50)
        print(f"  Optimal batch size: {batch_size}")

        # Test memory estimation
        estimated = manager.estimate_memory_for_files(100, 50)
        print(f"  Estimated memory for 100 files: {estimated:.1f}MB")

        can_process = manager.can_process_files(100, 50)
        print(f"  Can process 100 files: {can_process}")

        # Test context manager
        with manager.memory_monitoring_context("test operation"):
            time.sleep(0.1)  # Simulate work

        print("\nMemory report:")
        report = manager.get_memory_report()
        for rec in report["recommendations"]:
            print(f"  - {rec}")

        manager.stop_monitoring()

    test_memory_manager()
