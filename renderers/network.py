from driver import graphics
from utils import center_text_position
from PIL import Image
import debug
import time

NETWORK_ERROR_TEXT = "!"


def render_network_error(canvas, layout, colors):
    font = layout.font("network")
    coords = layout.coords("network")
    bg_coords = coords["background"]
    text_color = colors.graphics_color("network.text")
    bg_color = colors.color("network.background")

    # Fill in the background so it's clearly visible
    for x in range(bg_coords["width"]):
        for y in range(bg_coords["height"]):
            canvas.SetPixel(x + bg_coords["x"], y + bg_coords["y"], bg_color["r"], bg_color["g"], bg_color["b"])
    text = NETWORK_ERROR_TEXT
    x = center_text_position(text, coords["text"]["x"], font["size"]["width"])
    graphics.DrawText(canvas, font["font"], x, coords["text"]["y"], text_color, text)


class NetworkErrorRenderer:
    """Renders network error information on the LED matrix"""

    def __init__(self, matrix, data, colors, coords):
        self.matrix = matrix
        self.data = data
        self.colors = colors
        self.coords = coords
        self.canvas = matrix.CreateFrameCanvas()
        
    def render(self):
        """Render the network error display"""
        # Clear the canvas
        self.canvas.Clear()
        
        # Draw error icon or symbol (could be added later)
        
        # Draw error message
        self._draw_error_message()
        
        # Update the canvas
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
        
    def _draw_error_message(self):
        """Display the network error message"""
        # Draw the title
        title = "Network Error"
        font = self.data.font.get_font("6x9")
        self.canvas.SetFont(font)
        
        # Get color from network settings or use default red
        color = self.colors.get("network", {}).get("text", {"r": 255, "g": 0, "b": 0})
        
        # Center the text
        width = font.CharacterWidth(ord('A')) * len(title)
        x = center_text_position(self.canvas.width, width)
        y = 15
        
        self.canvas.DrawText(
            self.canvas,
            title,
            x,
            y,
            color["r"],
            color["g"],
            color["b"]
        )
        
        # Draw detailed message
        message = "Connecting to BART..."
        message_font = self.data.font.get_font("5x7")
        self.canvas.SetFont(message_font)
        
        # Center the message
        message_width = message_font.CharacterWidth(ord('A')) * len(message)
        message_x = center_text_position(self.canvas.width, message_width)
        message_y = 25
        
        self.canvas.DrawText(
            self.canvas,
            message,
            message_x,
            message_y,
            color["r"],
            color["g"],
            color["b"]
        )
        
        # Add a visual indicator that updates
        animation_frame = int(time.time() * 2) % 4
        dots = "." * animation_frame
        self.canvas.DrawText(
            self.canvas,
            dots,
            message_x + message_width,
            message_y,
            color["r"],
            color["g"],
            color["b"]
        )
