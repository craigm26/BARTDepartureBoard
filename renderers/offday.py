from driver import graphics

import time

from PIL import Image

from data.time_formats import TIME_FORMAT_12H
from data.config.color import Color
from data.config.layout import Layout
from data.headlines import Headlines
from data.weather import Weather
from renderers import scrollingtext
from utils import center_text_position

import debug

class OffdayRenderer:
    """Renders information for when no trains are running at a station"""

    def __init__(self, matrix, data, colors, coords):
        self.matrix = matrix
        self.data = data
        self.colors = colors
        self.coords = coords
        self.canvas = matrix.CreateFrameCanvas()
        
    def render(self):
        """Render the offday screen"""
        # Clear the canvas
        self.canvas.Clear()
        
        # Draw header with message
        self._draw_header()
        
        # Draw the current time
        self._draw_time()
        
        # Draw the weather
        self._draw_weather()
        
        # Draw scrolling text with news/alerts if available
        self._draw_scrolling_text()
        
        # Update the canvas
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
        
    def _draw_header(self):
        """Draw a header indicating that no trains are running"""
        # Get defaults
        font = self.data.font.get_font("6x9")
        self.canvas.SetFont(font)
        
        # Draw header text centered
        title = "No Service"
        color = self.colors["offday"]["time"]
        width = font.CharacterWidth(ord('A')) * len(title)
        x = center_text_position(self.canvas.width, width)
        
        self.canvas.DrawText(
            self.canvas,
            title,
            x,
            10,
            color["r"],
            color["g"],
            color["b"]
        )
        
    def _draw_time(self):
        """Draw the current time"""
        # Get defaults
        font = self.data.font.get_font("6x9")
        self.canvas.SetFont(font)
        
        # Format time based on config
        time_format = "%H:%M" if self.data.config.time_format == "24h" else "%I:%M %p"
        time_text = time.strftime(time_format)
        
        if self.data.config.time_format != "24h":
            # Remove leading zero from 12-hour format
            time_text = time_text.lstrip("0")
            
        # Draw time centered
        color = self.colors["offday"]["time"]
        width = font.CharacterWidth(ord('A')) * len(time_text)
        x = center_text_position(self.canvas.width, width)
        coords = self.coords["offday"]["time"] 
        
        self.canvas.DrawText(
            self.canvas,
            time_text,
            x,
            coords["y"],
            color["r"],
            color["g"],
            color["b"]
        )
        
    def _draw_weather(self):
        """Draw weather information if available"""
        if not hasattr(self.data, 'weather') or not self.data.weather:
            return
            
        # Format weather data
        try:
            weather = self.data.weather
            conditions = weather.conditions
            temperature = f"{int(weather.temperature)}°"
            
            # Draw temperature
            temp_font = self.data.font.get_font("5x7")
            self.canvas.SetFont(temp_font)
            temp_color = self.colors["offday"]["temperature"]
            temp_coords = self.coords["offday"]["temperature"]
            
            self.canvas.DrawText(
                self.canvas,
                temperature,
                temp_coords["x"],
                temp_coords["y"],
                temp_color["r"],
                temp_color["g"],
                temp_color["b"]
            )
            
            # Draw conditions text
            cond_font = self.data.font.get_font("4x6")
            self.canvas.SetFont(cond_font)
            cond_color = self.colors["offday"]["conditions"]
            cond_coords = self.coords["offday"]["conditions"]
            
            # Center the conditions text
            width = cond_font.CharacterWidth(ord('A')) * len(conditions)
            x = center_text_position(self.canvas.width, width)
            
            self.canvas.DrawText(
                self.canvas,
                conditions,
                x,
                cond_coords["y"],
                cond_color["r"],
                cond_color["g"],
                cond_color["b"]
            )
            
            # Draw weather icon if available
            if hasattr(weather, 'icon_id') and weather.icon_id:
                icon_path = f"./assets/weather/{weather.icon_id}.png"
                try:
                    icon = Image.open(icon_path)
                    icon_coords = self.coords["offday"]["weather_icon"]
                    self.canvas.SetImage(
                        icon.convert("RGB"),
                        icon_coords["x"],
                        icon_coords["y"]
                    )
                except Exception as e:
                    debug.error(f"Failed to load weather icon {icon_path}: {e}")
        except Exception as e:
            debug.error(f"Error rendering weather: {e}")
            
    def _draw_scrolling_text(self):
        """Draw scrolling news/alerts text at the bottom of the screen"""
        # Get text to display
        text = ""
        if hasattr(self.data, 'news_ticker') and self.data.news_ticker:
            text = self.data.news_ticker.text
            
        if not text and hasattr(self.data, 'system_status') and self.data.system_status:
            status = self.data.system_status
            if 'alerts' in status and status['alerts']:
                text = " | ".join([alert['title'] for alert in status['alerts']])
                
        if not text:
            # Default message
            text = "BART service hours: Weekdays 5am-12am, Sat 6am-12am, Sun 8am-9pm"
            
        # Render scrolling text
        if text:
            coords = self.coords["offday"]["scrolling_text"]
            colors = self.colors["offday"]["scrolling_text"]
            
            # Get font and configure
            font = self.data.font.get_font("4x6")
            self.canvas.SetFont(font)
            
            # Calculate position based on the current scroll offset
            text_width = font.CharacterWidth(ord('A')) * len(text)
            scroll_position = int(time.time() * self.data.config.scrolling_speed) % (text_width + coords["width"])
            
            self.canvas.DrawText(
                self.canvas,
                text,
                coords["x"] - scroll_position,
                coords["y"],
                colors["r"],
                colors["g"],
                colors["b"]
            )
