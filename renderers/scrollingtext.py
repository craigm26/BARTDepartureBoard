from driver import graphics
import time
from PIL import Image
import debug

from utils import center_text_position


def render_text(canvas, x, y, width, font, text_color, bg_color, text, scroll_pos, center=True):
    if __text_should_scroll(text, font, width):

        w = font["size"]["width"]
        total_width = w * len(text)

        # if the text is long enough to scroll, we can trim it to only the visible
        # part plus one letter on either side to minimize drawing
        left = None
        right = None

        empty_space_at_start = scroll_pos - x

        # Offscreen to the left
        if empty_space_at_start < 0:
            left = abs(empty_space_at_start) // w

        # Offscreen to the right
        visible_width = total_width + empty_space_at_start
        if visible_width > width + w:
            right =  -((visible_width - width) // w)

        # Trim the text to only the visible part
        text = text[left:right]

        if len(text) == 0:
            return 0

        # if we trimmed to the left, we need to adjust the scroll position accordingly
        if left:
            scroll_pos += w * left

        graphics.DrawText(canvas, font["font"], scroll_pos, y, text_color, text)

        # draw one-letter boxes to left and right to hide previous and next letters
        top = y + 1
        bottom = top - font["size"]["height"]
        for xi in range(0, w):
            left = x - xi - 1
            graphics.DrawLine(canvas, left, top, left, bottom, bg_color)
            right = x + width + xi
            graphics.DrawLine(canvas, right, top, right, bottom, bg_color)

        return total_width
    else:
        draw_x = __center_position(text, font, width, x) if center else x
        graphics.DrawText(canvas, font["font"], draw_x, y, text_color, text)
        return 0


# Maybe the text is too short and we should just center it instead?
def __text_should_scroll(text, font, width):
    return len(text) * font["size"]["width"] > width


def __center_position(text, font, width, x):
    return center_text_position(text, abs(width // 2) + x, font["size"]["width"])


class ScrollingText:
    """Renders a scrolling text ticker at the bottom of the matrix"""

    def __init__(self, matrix, data):
        self.matrix = matrix
        self.data = data
        self.canvas = matrix.CreateFrameCanvas()
        self.scroll_pos = 0
        self.last_scroll_time = time.time()
        
    def render_scrolling_text(self, text, coords, colors):
        """Render scrolling text at the specified coordinates with the specified colors"""
        if not text:
            return
            
        # Get font and configure coordinates
        font = self.data.font.get_font("4x6")
        self.canvas.SetFont(font)
        
        # Calculate text width for scrolling
        text_width = font.CharacterWidth(ord('A')) * len(text)
        
        # Calculate scroll position based on time and scrolling speed
        current_time = time.time()
        if current_time - self.last_scroll_time >= (0.15 / self.data.config.scrolling_speed):
            self.scroll_pos = (self.scroll_pos + 1) % (text_width + coords["width"])
            self.last_scroll_time = current_time
            
        # Draw the text
        self.canvas.DrawText(
            self.canvas,
            text,
            coords["x"] - self.scroll_pos,
            coords["y"],
            colors["r"],
            colors["g"],
            colors["b"]
        )
        
        # Draw the same text again when it starts to scroll off
        if self.scroll_pos > text_width - coords["width"]:
            self.canvas.DrawText(
                self.canvas,
                text,
                coords["x"] - self.scroll_pos + text_width + coords["width"],
                coords["y"],
                colors["r"],
                colors["g"],
                colors["b"]
            )
            
    def render(self):
        """Render scrolling news or alerts text"""
        # Clear the canvas
        self.canvas.Clear()
        
        # Get the news text from the data source
        text = self.data.news_ticker.text
        
        # Get coordinates and colors
        coords = self.data.config.layout.coords["scrolling_text"]
        colors = self.data.config.colors["scrolling_text"]
        
        # Render the scrolling text
        self.render_scrolling_text(text, coords, colors)
        
        # Update the canvas
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
