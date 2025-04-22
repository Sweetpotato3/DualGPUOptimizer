#!/usr/bin/env python3
"""
Test script to verify signal-based telemetry updates are working correctly.
"""
import logging
import sys

from PySide6.QtCore import QObject, QTimer, Slot
from PySide6.QtWidgets import QApplication

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Import telemetry worker
from dualgpuopt.services.telemetry import TelemetryWorker

logger = logging.getLogger("TelemetryTest")


class TelemetryTester(QObject):
    """Test class to verify telemetry signal connections"""

    def __init__(self):
        super().__init__()
        self.update_counts = {"util": 0, "vram": 0, "temp": 0, "power": 0, "clock": 0, "pcie": 0}

        # Create telemetry worker in mock mode
        self.telemetry_worker = TelemetryWorker(mock_mode=True)

        # Connect signals
        self.telemetry_worker.util_updated.connect(self._handle_util)
        self.telemetry_worker.vram_updated.connect(self._handle_vram)
        self.telemetry_worker.temp_updated.connect(self._handle_temp)
        self.telemetry_worker.power_updated.connect(self._handle_power)
        self.telemetry_worker.clock_updated.connect(self._handle_clock)
        self.telemetry_worker.pcie_updated.connect(self._handle_pcie)

        # Start telemetry worker
        self.telemetry_worker.start()
        logger.info("Telemetry worker started")

        # Set up timer to check results
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_updates)
        self.check_timer.start(1000)  # Check every second

        # Set up timer to exit after test
        self.exit_timer = QTimer()
        self.exit_timer.timeout.connect(self._finish_test)
        self.exit_timer.setSingleShot(True)
        self.exit_timer.start(10000)  # Run test for 10 seconds

    @Slot(int, int)
    def _handle_util(self, gpu_id, util_percent):
        self.update_counts["util"] += 1
        logger.debug(f"Util update: GPU {gpu_id}, {util_percent}%")

    @Slot(int, int, int, float)
    def _handle_vram(self, gpu_id, used_mb, total_mb, percent):
        self.update_counts["vram"] += 1
        logger.debug(f"VRAM update: GPU {gpu_id}, {used_mb}/{total_mb} MB ({percent:.1f}%)")

    @Slot(int, int)
    def _handle_temp(self, gpu_id, temp_c):
        self.update_counts["temp"] += 1
        logger.debug(f"Temp update: GPU {gpu_id}, {temp_c}°C")

    @Slot(int, int, int, float)
    def _handle_power(self, gpu_id, power_w, power_limit, percent):
        self.update_counts["power"] += 1
        logger.debug(f"Power update: GPU {gpu_id}, {power_w}/{power_limit}W ({percent:.1f}%)")

    @Slot(int, int, int)
    def _handle_clock(self, gpu_id, sm_clock, mem_clock):
        self.update_counts["clock"] += 1
        logger.debug(f"Clock update: GPU {gpu_id}, SM: {sm_clock} MHz, Mem: {mem_clock} MHz")

    @Slot(int, int, int)
    def _handle_pcie(self, gpu_id, tx_kb_s, rx_kb_s):
        self.update_counts["pcie"] += 1
        logger.debug(
            f"PCIe update: GPU {gpu_id}, TX: {tx_kb_s/1024:.1f} MB/s, RX: {rx_kb_s/1024:.1f} MB/s"
        )

    def _check_updates(self):
        """Display update counts"""
        logger.info("Signal update counts:")
        for signal_name, count in self.update_counts.items():
            logger.info(f"  {signal_name}: {count} updates")

    def _finish_test(self):
        """Complete the test and exit"""
        logger.info("Test complete - final counts:")
        for signal_name, count in self.update_counts.items():
            logger.info(f"  {signal_name}: {count} updates")

        # Stop telemetry worker
        self.telemetry_worker.stop()
        logger.info("Telemetry worker stopped")

        # Exit application
        QApplication.quit()


def main():
    """Main entry point"""
    # Create Qt application
    app = QApplication(sys.argv)

    # Create tester
    TelemetryTester()

    # Start event loop
    logger.info("Starting telemetry test...")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
