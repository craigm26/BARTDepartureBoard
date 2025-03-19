import time
from typing import Callable, NoReturn
from data.screens import ScreenType

import debug
from renderers.departures import DepartureRenderer
from renderers.offday import OffdayRenderer
from renderers.system_status import SystemStatusRenderer
from renderers.scrollingtext import ScrollingText
from renderers.network import NetworkErrorRenderer

class MainRenderer:
    """The main renderer that determines what to render on the matrix"""

    def __init__(self, matrix, data):
        self.matrix = matrix
        self.data = data
        
        # Get the layout and color data
        self.coords = data.config.layout.coords
        self.colors = data.config.colors
        
        # Initialize various renderers
        self.departure_renderer = DepartureRenderer(matrix, data, self.colors, self.coords)
        self.offday_renderer = OffdayRenderer(matrix, data, self.colors, self.coords)
        self.system_status_renderer = SystemStatusRenderer(matrix, data, self.colors, self.coords)
        self.scrolling_text = ScrollingText(matrix, data)
        self.network_renderer = NetworkErrorRenderer(matrix, data, self.colors, self.coords)
        
        # Record whether we're showing the network error screen
        self.showing_network_error = False

    def render(self):
        """Main loop to render the correct screen based on current state"""
        while True:
            if self.data.network_issues:
                if not self.showing_network_error:
                    debug.warning("Network issues detected. Showing error screen.")
                self.showing_network_error = True
                self.network_renderer.render()
                continue
            else:
                self.showing_network_error = False
            
            # Determine which screen to show
            screen = self.data.get_screen_type()
            if screen == ScreenType.ALWAYS_SYSTEM_STATUS:
                self._render_system_status()
            elif screen == ScreenType.ALWAYS_NEWS:
                self._render_news()
            elif screen == ScreenType.SYSTEM_OFFDAY or screen == ScreenType.PREFERRED_STATION_OFFDAY:
                self._render_offday()
            else:
                # Default to departure display
                self._render_departures()

    def _render_departures(self):
        """Render the departure board screen"""
        self.departure_renderer.render()

    def _render_system_status(self):
        """Render the system status screen"""
        self.system_status_renderer.render()

    def _render_news(self):
        """Render the news ticker screen"""
        debug.info("News render not implemented yet, showing offday instead")
        self._render_offday()

    def _render_offday(self):
        """Render the offday screen"""
        self.offday_renderer.render()
