#!/usr/bin/env python3
"""
Simple test script for visualizing BART departure board screens in the emulator.
This allows you to preview how screens will look without physical hardware.
"""
import sys
import time
import argparse
from datetime import datetime, timedelta
import os
import debug

# Import required modules
try:
    from driver import RGBMatrix, RGBMatrixOptions
    from driver.emulator import RGBMatrixEmulator
except ImportError:
    debug.error("RGBMatrixEmulator not found. Make sure it's installed.")
    sys.exit(1)

from data.bart import BARTData, BARTStation, BARTDeparture
from data.config import Config
from data.screens import ScreenType
from renderers.departures import DepartureRenderer
from renderers.offday import OffdayRenderer
from renderers.system_status import SystemStatusRenderer
from renderers.network import NetworkErrorRenderer

class MockData:
    """Mock data class to simulate BART data for testing renderers"""
    
    def __init__(self, config, test_mode):
        self.config = config
        self.network_issues = False
        self.scrolling_finished = True
        self.test_mode = test_mode
        
        # Create font helper (simplified for testing)
        self.font = FontHelper()
        
        # Initialize mock data based on test mode
        if self.test_mode == "departures":
            self._init_departures_data()
        elif self.test_mode == "system_status":
            self._init_system_status_data()
        elif self.test_mode == "offday":
            self._init_offday_data()
        elif self.test_mode == "network_error":
            self._init_network_error_data()
    
    def _init_departures_data(self):
        """Initialize mock departure data"""
        self.current_station = BARTStation("Powell St", "POWL", "POWL")
        
        # Create some mock departures
        self.current_station.departures = [
            BARTDeparture("Antioch", 4, "1", "N", "yellow", 10),
            BARTDeparture("Richmond", 7, "2", "N", "red", 10),
            BARTDeparture("Berryessa", 12, "1", "S", "green", 8, delay=60),
            BARTDeparture("SFO Airport", 18, "2", "S", "yellow", 10),
            BARTDeparture("Dublin/Pleasanton", 22, "1", "E", "blue", 6)
        ]
        
    def _init_system_status_data(self):
        """Initialize mock system status data"""
        self.system_status = {
            'status': 'alert',
            'alerts': [
                {
                    'title': 'Delay between Embarcadero and West Oakland',
                    'description': 'Trains experiencing delays of 10-15 minutes due to equipment problems'
                },
                {
                    'title': 'Weekend track maintenance',
                    'description': 'Expect reduced service on Richmond line'
                }
            ]
        }
        self.current_station = None
        
    def _init_offday_data(self):
        """Initialize mock offday data"""
        self.weather = MockWeather()
        self.news_ticker = MockNewsTicker()
        self.current_station = None
        
    def _init_network_error_data(self):
        """Initialize mock network error data"""
        self.network_issues = True
        self.current_station = None
        
    def get_screen_type(self):
        """Return the screen type based on test mode"""
        if self.test_mode == "departures":
            return ScreenType.DEPARTURES
        elif self.test_mode == "system_status":
            return ScreenType.ALWAYS_SYSTEM_STATUS
        elif self.test_mode == "offday":
            return ScreenType.SYSTEM_OFFDAY
        else:
            return ScreenType.DEPARTURES

class MockWeather:
    """Mock weather data for testing"""
    
    def __init__(self):
        self.temperature = 68
        self.conditions = "Partly Cloudy"
        self.icon_id = "02d"  # Partly cloudy icon

class MockNewsTicker:
    """Mock news ticker data for testing"""
    
    def __init__(self):
        self.text = "BART service hours: Weekdays 5am-12am, Sat 6am-12am, Sun 8am-9pm | Weekend track maintenance on Richmond line | Plan ahead for holiday schedule"

class FontHelper:
    """Simplified font helper for testing"""
    
    def get_font(self, name="4x6"):
        """Return a font for rendering"""
        from driver import graphics
        
        # Map font names to actual font objects
        font_map = {
            "4x6": graphics.Font(),
            "5x7": graphics.Font(),
            "6x9": graphics.Font()
        }
        
        # For testing, we'll load a default font
        font = font_map.get(name, graphics.Font())
        try:
            font.LoadFont("assets/fonts/patched/4x6.bdf")
        except Exception:
            # Fallback if font can't be loaded
            pass
            
        return font

def parse_args():
    """Parse command line arguments with our own argument parser"""
    parser = argparse.ArgumentParser(description="Test BART departure board screens")
    
    # Define our own arguments
    parser.add_argument('--mode', type=str, default='departures', 
                      choices=['departures', 'system_status', 'offday', 'network_error', 'cycle'],
                      help='Screen to test (Default: departures)')
    parser.add_argument('--rows', type=int, default=32,
                      help='Display rows (Default: 32)')
    parser.add_argument('--cols', type=int, default=64,
                      help='Display columns (Default: 64)')
    parser.add_argument('--brightness', type=int, default=100,
                      help='LED brightness (Default: 100)')
    parser.add_argument('--config', type=str, default='config',
                      help='Config file to use (Default: config)')
    
    return parser.parse_args()

def main():
    """Main function to run the test screen visualizer"""
    args = parse_args()
    
    # Set up the matrix with emulation
    options = RGBMatrixOptions()
    options.rows = args.rows
    options.cols = args.cols
    options.brightness = args.brightness
    options.hardware_mapping = 'regular'
    
    # Create an emulated matrix
    matrix = RGBMatrixEmulator(options=options)
    
    # Load the configuration
    config_base, _ = os.path.splitext(args.config)
    config = Config(config_base, matrix.width, matrix.height)
    
    # Set up the mock data
    data = MockData(config, args.mode)
    
    # Create renderers
    renderers = {
        'departures': DepartureRenderer(matrix, data, config.colors, config.layout.coords),
        'system_status': SystemStatusRenderer(matrix, data, config.colors, config.layout.coords),
        'offday': OffdayRenderer(matrix, data, config.colors, config.layout.coords),
        'network_error': NetworkErrorRenderer(matrix, data, config.colors, config.layout.coords)
    }
    
    # If cycle mode, rotate through all screens
    if args.mode == 'cycle':
        print("Cycling through all screens. Press Ctrl+C to exit.")
        screens = ['departures', 'system_status', 'offday', 'network_error']
        try:
            while True:
                for screen in screens:
                    print(f"Showing {screen} screen...")
                    data.test_mode = screen
                    
                    # Update mock data for the new screen
                    if screen == 'departures':
                        data._init_departures_data()
                    elif screen == 'system_status':
                        data._init_system_status_data()
                    elif screen == 'offday':
                        data._init_offday_data()
                    elif screen == 'network_error':
                        data._init_network_error_data()
                        
                    # Render the screen
                    renderers[screen].render()
                    time.sleep(5)  # Show each screen for 5 seconds
        except KeyboardInterrupt:
            print("\nTest ended.")
    else:
        # Show the selected screen
        print(f"Showing {args.mode} screen. Press Ctrl+C to exit.")
        renderer = renderers[args.mode]
        
        try:
            while True:
                renderer.render()
                time.sleep(0.1)  # Small delay to avoid high CPU usage
        except KeyboardInterrupt:
            print("\nTest ended.")
    
    # Clean up
    matrix.Clear()

if __name__ == "__main__":
    main()