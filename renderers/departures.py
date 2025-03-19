from PIL import Image
import debug
import time
from utils import center_text_position

class DepartureRenderer:
    """Renders BART station departures on the LED matrix"""

    def __init__(self, matrix, data, colors, coords):
        self.matrix = matrix
        self.data = data
        self.colors = colors
        self.coords = coords
        self.canvas = matrix.CreateFrameCanvas()
        
    def render(self):
        """Render the current station departure board"""
        station = self.data.current_station
        if not station:
            return
            
        # Clear the canvas
        self.canvas.Clear()
        
        # Draw the station header
        self._draw_station_header(station.name)
        
        # Draw the departure list header
        self._draw_departure_header()
        
        # Draw departure rows
        self._draw_departures(station.departures)
        
        # Update the canvas
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
        
    def _draw_station_header(self, station_name):
        """Draw the station name and current time at the top of the display"""
        # Draw header background
        header_coords = self.coords["station"]["header"]
        header_color = self.colors["station"]["header"]["background"]
        for x in range(header_coords["width"]):
            for y in range(header_coords["height"]):
                self.canvas.SetPixel(
                    header_coords["x"] + x,
                    header_coords["y"] + y,
                    header_color["r"],
                    header_color["g"],
                    header_color["b"]
                )
                
        # Draw station name
        name_color = self.colors["station"]["header"]["text"]
        name_coords = self.coords["station"]["name"]
        name_font = self.data.font.get_font(name_coords.get("font_name", "6x9"))
        self.canvas.SetFont(name_font)
        self.canvas.DrawText(
            self.canvas,
            station_name[:12],  # Limit length to avoid overflow
            name_coords["x"],
            name_coords["y"],
            name_color["r"],
            name_color["g"],
            name_color["b"]
        )
        
        # Draw current time
        time_color = self.colors["station"]["header"]["text"]
        time_coords = self.coords["station"]["time"]
        time_font = self.data.font.get_font(time_coords.get("font_name", "5x7"))
        time_text = time.strftime("%H:%M" if self.data.config.time_format == "24h" else "%I:%M %p")
        if self.data.config.time_format != "24h":
            # Remove leading zero from 12-hour format
            time_text = time_text.lstrip("0")
            
        self.canvas.SetFont(time_font)
        self.canvas.DrawText(
            self.canvas,
            time_text,
            time_coords["x"],
            time_coords["y"],
            time_color["r"],
            time_color["g"],
            time_color["b"]
        )
        
    def _draw_departure_header(self):
        """Draw the column headers for departure information"""
        header_coords = self.coords["departures"]["header"]
        header_color = self.colors["departures"]["header"]["background"]
        
        # Draw header background
        for x in range(header_coords["width"]):
            for y in range(header_coords["height"]):
                self.canvas.SetPixel(
                    header_coords["x"] + x,
                    header_coords["y"] + y,
                    header_color["r"],
                    header_color["g"],
                    header_color["b"]
                )
                
        # Draw header text
        text_color = self.colors["departures"]["header"]["text"]
        font = self.data.font.get_font(self.coords.get("defaults", {}).get("font_name", "4x6"))
        self.canvas.SetFont(font)
        
        # Draw "Destination" header
        dest_coords = self.coords["departures"]["header_text"]["destination"]
        self.canvas.DrawText(
            self.canvas,
            "Dest",
            dest_coords["x"],
            dest_coords["y"],
            text_color["r"],
            text_color["g"],
            text_color["b"]
        )
        
        # Draw "Minutes" header
        min_coords = self.coords["departures"]["header_text"]["minutes"]
        self.canvas.DrawText(
            self.canvas,
            "Min",
            min_coords["x"],
            min_coords["y"],
            text_color["r"],
            text_color["g"],
            text_color["b"]
        )
        
        # Draw "Platform" header
        plat_coords = self.coords["departures"]["header_text"]["platform"]
        self.canvas.DrawText(
            self.canvas,
            "Plat",
            plat_coords["x"],
            plat_coords["y"],
            text_color["r"],
            text_color["g"],
            text_color["b"]
        )
        
    def _draw_departures(self, departures):
        """Draw the departure rows showing trains"""
        if not departures:
            # No departures to show
            self._draw_no_departures()
            return
            
        # Get coordinates for rows
        rows_config = self.coords["departures"]["rows"]
        font = self.data.font.get_font(self.coords.get("defaults", {}).get("font_name", "4x6"))
        self.canvas.SetFont(font)
        
        # Limit to max rows configured
        max_rows = rows_config.get("max_rows", 3)
        departures_to_show = departures[:max_rows]
        
        for i, departure in enumerate(departures_to_show):
            if i >= max_rows:
                break
                
            # Calculate the y position for this row
            y_offset = 0
            if i == 1:
                y_offset = rows_config.get("row2", {}).get("y_offset", 6)
            elif i == 2:
                y_offset = rows_config.get("row3", {}).get("y_offset", 12)
                
            # Draw line color indicator
            line_coords = rows_config["line_color"]
            line_color = self.colors["departures"]["lines"].get(
                departure.line_color.lower(), 
                {"r": 255, "g": 255, "b": 255}
            )
            
            for x in range(line_coords["width"]):
                for y in range(line_coords["height"]):
                    self.canvas.SetPixel(
                        line_coords["x"] + x,
                        line_coords["y"] + y + y_offset,
                        line_color["r"],
                        line_color["g"],
                        line_color["b"]
                    )
                    
            # Draw destination
            dest_coords = rows_config["destination"]
            dest_text = departure.destination_name
            if len(dest_text) > 12:  # Truncate if too long
                dest_text = dest_text[:10] + ".."
                
            dest_color = self.colors["departures"]["destination"]
            self.canvas.DrawText(
                self.canvas,
                dest_text,
                dest_coords["x"],
                dest_coords["y"] + y_offset,
                dest_color["r"],
                dest_color["g"],
                dest_color["b"]
            )
            
            # Draw minutes
            min_coords = rows_config["minutes"]
            
            # Choose color based on minutes remaining
            if departure.minutes == 0:
                min_color = self.colors["departures"]["minutes"]["boarding"]
            elif departure.minutes <= 1:
                min_color = self.colors["departures"]["minutes"]["arriving"]
            elif departure.delay > 60:  # If delayed more than a minute
                min_color = self.colors["departures"]["minutes"]["delayed"]
            else:
                min_color = self.colors["departures"]["minutes"]["normal"]
                
            # Format minutes text
            if departure.minutes == 0:
                min_text = "Now"
            else:
                min_text = str(departure.minutes)
                
            self.canvas.DrawText(
                self.canvas,
                min_text,
                min_coords["x"],
                min_coords["y"] + y_offset,
                min_color["r"],
                min_color["g"],
                min_color["b"]
            )
            
            # Draw platform
            plat_coords = rows_config["platform"]
            plat_color = self.colors["departures"]["platform"]
            self.canvas.DrawText(
                self.canvas,
                departure.platform,
                plat_coords["x"],
                plat_coords["y"] + y_offset,
                plat_color["r"],
                plat_color["g"],
                plat_color["b"]
            )
            
    def _draw_no_departures(self):
        """Display a message when no departures are available"""
        message = "No departures"
        color = self.colors["departures"]["destination"]
        font = self.data.font.get_font("6x9")
        self.canvas.SetFont(font)
        
        # Center the message
        width = font.CharacterWidth(ord('A')) * len(message)
        x = center_text_position(self.canvas.width, width)
        y = 24  # Position in the middle of the board
        
        self.canvas.DrawText(
            self.canvas,
            message,
            x,
            y,
            color["r"],
            color["g"],
            color["b"]
        )