from PIL import Image
import debug
import time
from utils import center_text_position
from data.screens import ScreenType

class SystemStatusRenderer:
    """Renders BART system status information on the LED matrix"""

    def __init__(self, matrix, data, colors, coords):
        self.matrix = matrix
        self.data = data
        self.colors = colors
        self.coords = coords
        self.canvas = matrix.CreateFrameCanvas()
        
    def render(self):
        """Render the system status display"""
        system_status = self.data.system_status
        
        # Clear the canvas
        self.canvas.Clear()
        
        # Draw a header saying "System Status"
        self._draw_header()
        
        # Draw the status information
        self._draw_status(system_status)
        
        # Update the canvas
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
        
    def _draw_header(self):
        """Draw the header with "BART System Status" text"""
        # Get defaults
        font = self.data.font.get_font("6x9")
        self.canvas.SetFont(font)
        
        # Draw header text centered
        title = "BART System"
        color = self.colors["system_status"]["title"]
        width = font.CharacterWidth(ord('A')) * len(title)
        x = center_text_position(self.canvas.width, width)
        
        coords = self.coords["system_status"]["title"]
        self.canvas.DrawText(
            self.canvas,
            title,
            x,
            coords["y"],
            color["r"],
            color["g"],
            color["b"]
        )
        
    def _draw_status(self, status):
        """Draw the actual status information"""
        if not status or status.get('status') == 'unknown':
            self._draw_unknown_status()
            return
            
        # Display the current status
        status_text = status.get('status', 'normal').upper()
        
        # Choose color based on status
        if status_text == 'NORMAL':
            color = self.colors["system_status"]["normal"]
        elif status_text == 'ALERT':
            color = self.colors["system_status"]["alert"]
        else:
            color = self.colors["system_status"]["delay"]
            
        # Draw status text centered
        font = self.data.font.get_font("6x9")
        self.canvas.SetFont(font)
        width = font.CharacterWidth(ord('A')) * len(status_text)
        x = center_text_position(self.canvas.width, width)
        
        coords = self.coords["system_status"]["status_text"]
        self.canvas.DrawText(
            self.canvas,
            status_text,
            x,
            coords["y"],
            color["r"],
            color["g"],
            color["b"]
        )
        
        # Display alert details if any
        alerts = status.get('alerts', [])
        if alerts and len(alerts) > 0:
            # Combine alert titles into scrolling text
            scroll_text = " | ".join([alert['title'] for alert in alerts])
            self._draw_scrolling_alert(scroll_text)
            
    def _draw_unknown_status(self):
        """Display message when status is unknown"""
        message = "Status Unavailable"
        color = self.colors["system_status"]["title"]
        font = self.data.font.get_font("5x7")
        self.canvas.SetFont(font)
        
        # Center the message
        width = font.CharacterWidth(ord('A')) * len(message)
        x = center_text_position(self.canvas.width, width)
        
        coords = self.coords["system_status"]["status_text"]
        self.canvas.DrawText(
            self.canvas,
            message,
            x,
            coords["y"],
            color["r"],
            color["g"],
            color["b"]
        )
        
    def _draw_scrolling_alert(self, text):
        """Display scrolling alert text at the bottom of the screen"""
        if not text:
            return
            
        coords = self.coords["system_status"]["scrolling_text"]
        color = self.colors["system_status"]["scrolling_text"]
        
        # Configure scrolling text
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
            color["r"],
            color["g"],
            color["b"]
        )