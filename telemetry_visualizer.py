#!/usr/bin/env python3
"""
Telemetry history visualizer using matplotlib.
Demonstrates the functionality of the telemetry history system with a simple real-time plot.
"""
import time
import math
import random
import threading
import sys
from typing import Dict

try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib.lines import Line2D
except ImportError:
    print("Error: Matplotlib is required for this demo.")
    print("Install with: pip install matplotlib")
    sys.exit(1)

# Import the stand-alone history buffer implementation
from standalone_test import HistoryBuffer


class TelemetryVisualizer:
    """Simple visualizer for telemetry metrics using matplotlib."""
    
    def __init__(self):
        self.history = HistoryBuffer()
        self.metrics = ["util", "mem", "temp", "power"]
        self.colors = ["blue", "red", "green", "orange"]
        self.start_time = time.monotonic()
        
        # Setup plot
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.fig.canvas.manager.set_window_title('Telemetry History Visualizer')
        
        # Initialize lines
        self.lines: Dict[str, Line2D] = {}
        for metric, color in zip(self.metrics, self.colors):
            line, = self.ax.plot([], [], lw=2, color=color, label=metric)
            self.lines[metric] = line
        
        # Configure axes
        self.ax.set_xlim(0, 60)  # 60 seconds of history
        self.ax.set_ylim(0, 100)
        self.ax.set_xlabel('Seconds Ago')
        self.ax.set_ylabel('Value')
        self.ax.set_title('Real-time Telemetry History (60s)')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper right')
        
        # Start data generator thread
        self.running = True
        self.data_thread = threading.Thread(target=self._generate_data, daemon=True)
        self.data_thread.start()
    
    def _generate_data(self):
        """Generate simulated telemetry data."""
        while self.running:
            # Calculate simulated values based on time
            elapsed = time.monotonic() - self.start_time
            
            # Different patterns for each metric
            values = {
                "util": 50 + 30 * math.sin(elapsed / 5) + random.uniform(-5, 5),
                "mem": 70 + 20 * math.sin(elapsed / 8 + 1) + random.uniform(-3, 3),
                "temp": 60 + 15 * math.sin(elapsed / 12 + 2) + random.uniform(-2, 2),
                "power": 80 + 25 * math.sin(elapsed / 10 + 3) + random.uniform(-4, 4)
            }
            
            # Push values to history buffer
            for metric, value in values.items():
                self.history.push(metric, value)
            
            # Sleep for a short time
            time.sleep(0.1)
    
    def update_plot(self, frame):
        """Update the plot with the latest data."""
        now = time.monotonic()
        
        for metric, line in self.lines.items():
            # Get historical data
            data = self.history.snapshot(metric)
            
            if data:
                # Convert to x, y arrays for plotting
                times = [60 - (now - ts) for ts, _ in data]  # Convert to seconds ago
                values = [val for _, val in data]
                
                # Update line data
                line.set_data(times, values)
        
        return list(self.lines.values())
    
    def run(self):
        """Run the visualization."""
        animation.FuncAnimation(
            self.fig, self.update_plot, interval=100, blit=True
        )
        plt.tight_layout()
        plt.show()
        
        # Clean up
        self.running = False
        self.data_thread.join(timeout=1.0)


if __name__ == "__main__":
    try:
        print("Starting telemetry visualizer...")
        print("Press Ctrl+C to exit")
        visualizer = TelemetryVisualizer()
        visualizer.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 