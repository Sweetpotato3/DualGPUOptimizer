"""
Example of using telemetry history with a UI chart component
"""
import sys
import time
from PySide6 import QtCore, QtWidgets, QtCharts
from typing import List, Tuple

# Import telemetry components
from dualgpuopt.telemetry_history import HistoryBuffer
from dualgpuopt.telemetry.sample import TelemetrySample


class TelemetryChart(QtWidgets.QWidget):
    """Widget for displaying telemetry history"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        
        # Create chart
        self.chart = QtCharts.QChart()
        self.chart.setTitle("GPU Metrics History")
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(QtCore.Qt.AlignBottom)
        
        # Create chart view
        self.chart_view = QtCharts.QChartView(self.chart)
        self.chart_view.setRenderHint(QtWidgets.QPainter.Antialiasing)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.chart_view)
        
        # Series for different metrics
        self.series = {}
        self.create_series("util", "GPU Utilization (%)", QtCore.Qt.blue)
        self.create_series("vram", "Memory Usage (%)", QtCore.Qt.red)
        self.create_series("temp", "Temperature (°C)", QtCore.Qt.green)
        
        # Create axis
        self.create_axes()
        
        # Timer for simulating telemetry updates
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_telemetry)
        self.timer.start(800)  # Update every 800ms
        
        # History buffer (in a real app, this would come from the telemetry service)
        self.history = HistoryBuffer()
        self.start_time = time.monotonic()
    
    def create_series(self, name: str, title: str, color: QtCore.Qt.GlobalColor):
        """Create a line series for a metric"""
        series = QtCharts.QLineSeries()
        series.setName(title)
        pen = series.pen()
        pen.setColor(color)
        pen.setWidth(2)
        series.setPen(pen)
        self.chart.addSeries(series)
        self.series[name] = series
    
    def create_axes(self):
        """Create and attach axes to the chart"""
        # X axis (time)
        self.axis_x = QtCharts.QValueAxis()
        self.axis_x.setTitleText("Time (seconds)")
        self.axis_x.setRange(0, 60)  # 60 seconds of history
        self.axis_x.setTickCount(7)
        
        # Y axis (value)
        self.axis_y = QtCharts.QValueAxis()
        self.axis_y.setTitleText("Value")
        self.axis_y.setRange(0, 100)
        self.axis_y.setTickCount(11)
        
        # Attach axes to series
        for series in self.series.values():
            self.chart.addAxis(self.axis_x, QtCore.Qt.AlignBottom)
            self.chart.addAxis(self.axis_y, QtCore.Qt.AlignLeft)
            series.attachAxis(self.axis_x)
            series.attachAxis(self.axis_y)
    
    def update_chart(self, name: str, sample: TelemetrySample):
        """Update chart with new telemetry sample"""
        if name not in self.series:
            return
            
        series = self.series[name]
        # Clear previous points
        series.clear()
        
        # Current time reference
        now = time.monotonic()
        
        # Add points from history
        for ts, value in sample.series:
            # Convert timestamp to seconds ago (for x-axis)
            seconds_ago = now - ts
            series.append(60 - seconds_ago, value)
        
        # Update axes if needed
        min_y = min([min([p[1] for p in s.pointsVector()]) for s in self.series.values() 
                     if s.count() > 0], default=0)
        max_y = max([max([p[1] for p in s.pointsVector()]) for s in self.series.values() 
                     if s.count() > 0], default=100)
        
        # Add some padding
        min_y = max(0, min_y - 5)
        max_y = min(100, max_y + 5)
        
        # Update Y axis range if values are significantly different
        if abs(min_y - self.axis_y.min()) > 5 or abs(max_y - self.axis_y.max()) > 5:
            self.axis_y.setRange(min_y, max_y)
    
    def update_telemetry(self):
        """Simulate telemetry updates (in a real app, this would come from events)"""
        # Simulate some changing values
        elapsed = time.monotonic() - self.start_time
        
        # Generate some test values with some variation
        import math
        import random
        util = 50 + 30 * math.sin(elapsed / 5) + random.uniform(-5, 5)
        vram = 40 + 20 * math.sin(elapsed / 8 + 1) + random.uniform(-3, 3)
        temp = 60 + 15 * math.sin(elapsed / 12 + 2) + random.uniform(-2, 2)
        
        # Push to history buffer
        self.history.push("util", util)
        self.history.push("vram", vram)
        self.history.push("temp", temp)
        
        # Create samples
        util_sample = TelemetrySample("util", util, self.history.snapshot("util"))
        vram_sample = TelemetrySample("vram", vram, self.history.snapshot("vram"))
        temp_sample = TelemetrySample("temp", temp, self.history.snapshot("temp"))
        
        # Update charts
        self.update_chart("util", util_sample)
        self.update_chart("vram", vram_sample) 
        self.update_chart("temp", temp_sample)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = TelemetryChart()
    window.setWindowTitle("Telemetry History Chart Example")
    window.show()
    sys.exit(app.exec()) 