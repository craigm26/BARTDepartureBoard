#!/usr/bin/env python3
"""
Test script for visualizing BART departure board screens using Pygame.
This allows you to preview how screens will look without physical hardware.
"""
import os
import sys
import time
import argparse
from datetime import datetime
import pygame
import requests
import gtfs_realtime_pb2

# Define colors (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 50, 98)  # BART blue
RED = (230, 30, 34)  # BART red line
YELLOW = (255, 215, 0)  # BART yellow line
GREEN = (0, 165, 81)  # BART green line
ORANGE = (250, 146, 0)  # BART orange line
LIGHT_BLUE = (0, 118, 206)  # BART blue line

class PygameSimulator:
    """Simulator for BART LED Matrix display using Pygame"""
    
    def __init__(self, width, height, scale=10):
        """Initialize the simulator
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
            scale: Display scale factor (for better visibility)
        """
        self.width = width
        self.height = height
        self.scale = scale
        self.screen_width = width * scale
        self.screen_height = height * scale
        
        # Initialize Pygame
        pygame.init()
        pygame.display.set_caption("BART Departure Board Simulator")
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()
        
        # Font setup
        self.font = {
            'small': pygame.font.SysFont('monospace', 8 * scale // 2),
            'medium': pygame.font.SysFont('monospace', 10 * scale // 2),
            'large': pygame.font.SysFont('monospace', 12 * scale // 2)
        }
        
    def clear(self):
        """Clear the screen"""
        self.screen.fill(BLACK)
    
    def update(self):
        """Update the display"""
        pygame.display.flip()
    
    def check_quit(self):
        """Check if the user wants to quit"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return True
        return False
    
    def draw_pixel(self, x, y, color):
        """Draw a pixel at the specified coordinates"""
        pygame.draw.rect(self.screen, color, 
                        (x * self.scale, y * self.scale, 
                         self.scale, self.scale))
    
    def draw_rect(self, x, y, width, height, color):
        """Draw a rectangle at the specified coordinates"""
        pygame.draw.rect(self.screen, color, 
                        (x * self.scale, y * self.scale, 
                         width * self.scale, height * self.scale))
    
    def draw_text(self, text, x, y, color, size='small'):
        """Draw text at the specified coordinates"""
        text_surface = self.font[size].render(text, True, color)
        self.screen.blit(text_surface, (x * self.scale, y * self.scale))

def fetch_live_departures(api_key, station):
    """Fetch live departure data from the BART GTFS Realtime API."""
    url = f"https://api.bart.gov/gtfsrt/tripupdates.aspx?key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        departures = []

        for entity in feed.entity:
            if entity.trip_update and entity.trip_update.trip.route_id == station:
                for stop_time_update in entity.trip_update.stop_time_update:
                    departures.append({
                        "destination": entity.trip_update.trip.trip_id,
                        "minutes": int(stop_time_update.arrival.time - time.time()) // 60,
                        "platform": stop_time_update.stop_id,
                        "line_color": "blue"  # Placeholder for line color
                    })
        return departures
    else:
        print("Error fetching live data:", response.status_code)
        return []

# Replace the mock data in render_departures
def render_departures(display, api_key, station):
    """Render the departures screen with live data."""
    # Fetch live data
    departures = fetch_live_departures(api_key, station)

    # Draw station header
    display.draw_rect(0, 0, display.width, 8, BLUE)
    display.draw_text(station, 2, 1, WHITE, 'large')

    current_time = datetime.now().strftime("%H:%M")
    display.draw_text(current_time, display.width - 15, 1, WHITE, 'medium')

    # Draw table header
    display.draw_rect(0, 9, display.width, 4, (50, 50, 50))
    display.draw_text("Dest", 6, 10, WHITE, 'small')
    display.draw_text("Min", display.width - 18, 10, WHITE, 'small')
    display.draw_text("Plat", display.width - 8, 10, WHITE, 'small')

    # Draw departures
    for i, train in enumerate(departures[:3]):  # Limit to 3 departures
        y_offset = 15 + (i * 5)

        # Draw line color indicator
        display.draw_rect(1, y_offset, 3, 4, train["line_color"])

        # Draw destination
        display.draw_text(train["destination"], 6, y_offset, WHITE, 'medium')

        # Draw minutes
        min_color = WHITE
        if train["minutes"] <= 1:
            min_color = YELLOW
        if train["minutes"] == 0:
            min_text = "Now"
            min_color = GREEN
        else:
            min_text = str(train["minutes"])
        display.draw_text(min_text, display.width - 16, y_offset, min_color, 'medium')

        # Draw platform
        display.draw_text(train["platform"], display.width - 7, y_offset, WHITE, 'medium')

    # Draw scrolling text at bottom
    scroll_text = "BART service hours: Weekdays 5am-12am, Sat 6am-12am, Sun 8am-9pm"
    scroll_pos = int(time.time() * 2) % (len(scroll_text) + display.width)
    visible_text = scroll_text[max(0, scroll_pos - display.width):scroll_pos]
    display.draw_text(visible_text, 0, display.height - 5, WHITE, 'small')

def render_system_status(display):
    """Render the system status screen"""
    # Draw header
    display.draw_text("BART System", display.width // 3, 5, WHITE, 'large')
    
    # Draw status
    status = "ALERT"
    status_color = YELLOW  # Alert color
    display.draw_text(status, display.width // 3 + 5, 15, status_color, 'large')
    
    # Draw alert details
    alert = "Delay: Embarcadero - West Oakland"
    scroll_pos = int(time.time() * 2) % (len(alert) + display.width)
    visible_text = alert[max(0, scroll_pos - display.width):scroll_pos]
    display.draw_text(visible_text, 0, display.height - 5, WHITE, 'small')

def render_offday(display):
    """Render the offday screen when no trains are running"""
    # Draw "No Service" text
    display.draw_text("No Service", display.width // 3, 5, WHITE, 'large')
    
    # Draw time
    current_time = datetime.now().strftime("%H:%M")
    display.draw_text(current_time, display.width // 2 - 5, 12, WHITE, 'large')
    
    # Draw weather
    display.draw_text("68°F Partly Cloudy", display.width // 3 - 2, 20, WHITE, 'medium')
    
    # Draw scrolling text
    scroll_text = "BART service hours: Weekdays 5am-12am, Sat 6am-12am, Sun 8am-9pm"
    scroll_pos = int(time.time() * 2) % (len(scroll_text) + display.width)
    visible_text = scroll_text[max(0, scroll_pos - display.width):scroll_pos]
    display.draw_text(visible_text, 0, display.height - 5, WHITE, 'small')

def render_network_error(display):
    """Render the network error screen"""
    # Draw error message
    display.draw_text("Network Error", display.width // 3 - 2, 10, RED, 'large')
    
    # Draw connecting message with animated dots
    message = "Connecting to BART"
    dots = "." * (int(time.time() * 2) % 4)
    display.draw_text(message + dots, display.width // 3 - 8, 20, WHITE, 'medium')

# Update the main function to pass API key and station
def main():
    """Main function to run the simulator"""
    parser = argparse.ArgumentParser(description="Pygame BART Board Simulator")
    parser.add_argument('--mode', type=str, default='departures',
                        choices=['departures', 'system_status', 'offday', 'network_error', 'cycle'],
                        help='Screen to test (Default: departures)')
    parser.add_argument('--width', type=int, default=64,
                        help='Display width in pixels (Default: 64)')
    parser.add_argument('--height', type=int, default=32,
                        help='Display height in pixels (Default: 32)')
    parser.add_argument('--scale', type=int, default=10,
                        help='Display scale factor (Default: 10)')

    args = parser.parse_args()

    # Hardcoded API key and station
    api_key = "MW9S-E7SL-26DU-VV8V"
    station = "WCRK"  # Walnut Creek

    # Create the simulator
    display = PygameSimulator(args.width, args.height, args.scale)

    # Select the render function based on mode
    render_functions = {
        'departures': render_departures,
        'system_status': render_system_status,
        'offday': render_offday,
        'network_error': render_network_error
    }
    
    running = True
    
    # If cycling through screens
    if args.mode == 'cycle':
        screens = list(render_functions.keys())
        screen_index = 0
        last_change = time.time()
        
        while running:
            if display.check_quit():
                running = False
                break
                
            # Switch screen every 5 seconds
            current_time = time.time()
            if current_time - last_change >= 5:
                screen_index = (screen_index + 1) % len(screens)
                last_change = current_time
                print(f"Showing {screens[screen_index]} screen...")
                
            # Render current screen
            display.clear()
            render_functions[screens[screen_index]](display, api_key, station)
            display.update()
            display.clock.tick(30)
    else:
        # Render just the selected screen
        print(f"Showing {args.mode} screen. Press ESC to exit.")
        while running:
            if display.check_quit():
                running = False
                break
                
            display.clear()
            render_functions[args.mode](display, api_key, station)
            display.update()
            display.clock.tick(30)
    
    # Clean up
    pygame.quit()
    print("Test ended.")

if __name__ == "__main__":
    main()