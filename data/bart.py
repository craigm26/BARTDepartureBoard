import requests
import time
from google.transit import gtfs_realtime_pb2
import logging
import debug
from typing import Dict, List, Optional, Tuple

class BARTStation:
    def __init__(self, name: str, abbreviation: str, station_id: str):
        self.name = name
        self.abbreviation = abbreviation
        self.station_id = station_id
        self.departures = []
        self.last_updated = 0

class BARTDeparture:
    def __init__(self, destination_name: str, minutes: int, platform: str, direction: str, 
                 line_color: str, train_length: int, delay: int = 0):
        self.destination_name = destination_name
        self.minutes = minutes
        self.platform = platform
        self.direction = direction
        self.line_color = line_color
        self.train_length = train_length
        self.delay = delay

class BARTData:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('bartled')
        self.api_key = config.bart_api_key
        self.stations = self._initialize_stations()
        self.base_url = "https://api.bart.gov/gtfsrt/tripupdate.aspx"
        self.station_url = "https://api.bart.gov/api/stn.aspx"
        self.alert_url = "https://api.bart.gov/gtfsrt/alerts.aspx"
        self.last_update = 0
        self.update_frequency = config.api_refresh_rate or 30  # Default to 30 seconds
        self.current_station = None
        self._set_default_station()

    def _initialize_stations(self) -> Dict[str, BARTStation]:
        """Initialize all BART stations"""
        # This is a static map of station abbreviations to full names
        # In a real implementation, you would fetch this from the BART API
        station_map = {
            "12TH": BARTStation("12th St. Oakland City Center", "12TH", "12TH"),
            "16TH": BARTStation("16th St. Mission", "16TH", "16TH"),
            "19TH": BARTStation("19th St. Oakland", "19TH", "19TH"),
            "24TH": BARTStation("24th St. Mission", "24TH", "24TH"),
            "ASHB": BARTStation("Ashby", "ASHB", "ASHB"),
            "BALB": BARTStation("Balboa Park", "BALB", "BALB"),
            "BAYF": BARTStation("Bay Fair", "BAYF", "BAYF"),
            "BERY": BARTStation("Berryessa", "BERY", "BERY"),
            "CAST": BARTStation("Castro Valley", "CAST", "CAST"),
            "CIVC": BARTStation("Civic Center/UN Plaza", "CIVC", "CIVC"),
            "COLM": BARTStation("Colma", "COLM", "COLM"),
            "CONC": BARTStation("Concord", "CONC", "CONC"),
            "DALY": BARTStation("Daly City", "DALY", "DALY"),
            "DBRK": BARTStation("Downtown Berkeley", "DBRK", "DBRK"),
            "DUBL": BARTStation("Dublin/Pleasanton", "DUBL", "DUBL"),
            "DELN": BARTStation("El Cerrito del Norte", "DELN", "DELN"),
            "PLZA": BARTStation("El Cerrito Plaza", "PLZA", "PLZA"),
            "EMBR": BARTStation("Embarcadero", "EMBR", "EMBR"),
            "FRMT": BARTStation("Fremont", "FRMT", "FRMT"),
            "FTVL": BARTStation("Fruitvale", "FTVL", "FTVL"),
            "GLEN": BARTStation("Glen Park", "GLEN", "GLEN"),
            "HAYW": BARTStation("Hayward", "HAYW", "HAYW"),
            "LAFY": BARTStation("Lafayette", "LAFY", "LAFY"),
            "LAKE": BARTStation("Lake Merritt", "LAKE", "LAKE"),
            "MCAR": BARTStation("MacArthur", "MCAR", "MCAR"),
            "MLBR": BARTStation("Millbrae", "MLBR", "MLBR"),
            "MONT": BARTStation("Montgomery St.", "MONT", "MONT"),
            "NBRK": BARTStation("North Berkeley", "NBRK", "NBRK"),
            "NCON": BARTStation("North Concord/Martinez", "NCON", "NCON"),
            "OAKL": BARTStation("Oakland Airport", "OAKL", "OAKL"),
            "ORIN": BARTStation("Orinda", "ORIN", "ORIN"),
            "PITT": BARTStation("Pittsburg/Bay Point", "PITT", "PITT"),
            "PCTR": BARTStation("Pittsburg Center", "PCTR", "PCTR"),
            "PHIL": BARTStation("Pleasant Hill/Contra Costa Centre", "PHIL", "PHIL"),
            "POWL": BARTStation("Powell St.", "POWL", "POWL"),
            "RICH": BARTStation("Richmond", "RICH", "RICH"),
            "ROCK": BARTStation("Rockridge", "ROCK", "ROCK"),
            "SBRN": BARTStation("San Bruno", "SBRN", "SBRN"),
            "SFIA": BARTStation("San Francisco Airport", "SFIA", "SFIA"),
            "SANL": BARTStation("San Leandro", "SANL", "SANL"),
            "SHAY": BARTStation("South Hayward", "SHAY", "SHAY"),
            "SSAN": BARTStation("South San Francisco", "SSAN", "SSAN"),
            "UCTY": BARTStation("Union City", "UCTY", "UCTY"),
            "WARM": BARTStation("Warm Springs/South Fremont", "WARM", "WARM"),
            "WCRK": BARTStation("Walnut Creek", "WCRK", "WCRK"),
            "WDUB": BARTStation("West Dublin/Pleasanton", "WDUB", "WDUB"),
            "WOAK": BARTStation("West Oakland", "WOAK", "WOAK")
        }
        return station_map
        
    def _set_default_station(self):
        """Set the default station based on config"""
        # Check if we have preferred stations in config
        preferred_stations = getattr(self.config, 'preferred_stations', ["WCRK"])
        
        # Default to Walnut Creek if no preference is specified
        default_station_code = preferred_stations[0] if preferred_stations else "WCRK"
        
        # Find the station in our map
        if default_station_code in self.stations:
            self.current_station = self.stations[default_station_code]
            
            # Apply station name override if specified
            if hasattr(self.config, 'station_name_override') and self.config.station_name_override:
                self.current_station.name = self.config.station_name_override
            
            debug.info(f"Default station set to {self.current_station.name}")
        else:
            debug.error(f"Default station code {default_station_code} not found")
            # Fallback to Walnut Creek if the configured station is invalid
            if "WCRK" in self.stations:
                self.current_station = self.stations["WCRK"]
                debug.info(f"Falling back to Walnut Creek station")

    def get_line_color(self, route_id: str) -> str:
        """Get the color for a BART line based on the route ID"""
        line_colors = {
            "ROUTE 1": "yellow",  # Antioch - SFO/Millbrae
            "ROUTE 2": "yellow",  # Pittsburg/Bay Point - SFO/Millbrae
            "ROUTE 3": "orange",  # Richmond - Warm Springs/South Fremont
            "ROUTE 4": "orange",  # Richmond - Warm Springs/South Fremont
            "ROUTE 5": "green",   # Warm Springs/South Fremont - Daly City
            "ROUTE 6": "green",   # Warm Springs/South Fremont - Daly City
            "ROUTE 7": "red",     # Warm Springs/South Fremont - Richmond
            "ROUTE 8": "red",     # Warm Springs/South Fremont - Richmond
            "ROUTE 11": "blue",   # Dublin/Pleasanton - Daly City
            "ROUTE 12": "blue"    # Dublin/Pleasanton - Daly City
        }
        return line_colors.get(route_id, "white")

    def update_departures(self) -> None:
        """Update departure information for all stations"""
        current_time = time.time()
        
        # Only update if enough time has passed since last update
        if current_time - self.last_update < self.update_frequency:
            return
            
        try:
            # Make request to BART GTFS Realtime API
            response = requests.get(self.base_url, params={'api_key': self.api_key})
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            # Clear existing departure information
            for station in self.stations.values():
                station.departures = []
            
            # Process each entity in the GTFS feed
            for entity in feed.entity:
                if entity.HasField('trip_update'):
                    trip_update = entity.trip_update
                    route_id = trip_update.trip.route_id
                    line_color = self.get_line_color(route_id)
                    
                    # Process each stop time update
                    for stop_time_update in trip_update.stop_time_update:
                        station_id = stop_time_update.stop_id
                        
                        # Skip if we don't have this station in our map
                        if station_id not in self.stations:
                            continue
                            
                        station = self.stations[station_id]
                        
                        # Calculate minutes until arrival
                        if stop_time_update.HasField('arrival'):
                            arrival_time = stop_time_update.arrival.time
                            minutes = int((arrival_time - current_time) / 60)
                            delay = stop_time_update.arrival.delay
                        else:
                            # If no arrival time, use departure time
                            departure_time = stop_time_update.departure.time
                            minutes = int((departure_time - current_time) / 60)
                            delay = stop_time_update.departure.delay
                        
                        # Only add future departures
                        if minutes >= 0:
                            # Get destination from trip headsign
                            destination = trip_update.trip.trip_id.split("-")[-1]
                            
                            # Create departure object
                            departure = BARTDeparture(
                                destination_name=destination,
                                minutes=minutes,
                                platform="1",  # Default, would need more GTFS data for actual platform
                                direction="N",  # Default, would need more GTFS data for actual direction
                                line_color=line_color,
                                train_length=10,  # Default, would need more GTFS data for actual train length
                                delay=delay
                            )
                            
                            # Add to station's departures
                            station.departures.append(departure)
            
            self.last_update = current_time
            debug.log(f"Successfully updated BART departure information for all stations")
            
        except Exception as e:
            self.logger.error(f"Error updating BART departures: {e}")
            debug.error(f"Error updating BART departures: {e}")
    
    def get_departures_for_station(self, station_name: str) -> List[BARTDeparture]:
        """Get departures for a specific station"""
        # First update all departure information
        self.update_departures()
        
        # Find station by name or abbreviation
        station = None
        for s in self.stations.values():
            if s.name.lower() == station_name.lower() or s.abbreviation.lower() == station_name.lower():
                station = s
                break
        
        if not station:
            debug.error(f"Station '{station_name}' not found")
            return []
        
        # Sort departures by minutes
        departures = sorted(station.departures, key=lambda d: d.minutes)
        return departures
    
    def get_system_status(self) -> Dict:
        """Get system-wide alerts and status information"""
        try:
            response = requests.get(self.alert_url, params={'api_key': self.api_key})
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            alerts = []
            for entity in feed.entity:
                if entity.HasField('alert'):
                    alert = {
                        'title': entity.alert.header_text.translation[0].text if entity.alert.header_text.translation else "Alert",
                        'description': entity.alert.description_text.translation[0].text if entity.alert.description_text.translation else "",
                        'effect': entity.alert.effect,
                        'cause': entity.alert.cause
                    }
                    alerts.append(alert)
            
            return {
                'alerts': alerts,
                'status': 'normal' if not alerts else 'alert'
            }
        except Exception as e:
            self.logger.error(f"Error fetching system status: {e}")
            debug.error(f"Error fetching system status: {e}")
            return {'alerts': [], 'status': 'unknown'}
    
    def get_screen_type(self):
        """Determine which screen type to show based on the current state"""
        from data.screens import ScreenType
        
        # Update departure info first
        self.update_departures()
        
        # If we have network issues, let the main renderer decide
        
        # If we have a current station with departures, show them
        if self.current_station and self.current_station.departures:
            return ScreenType.DEPARTURES
            
        # If system is not running (late night), show offday screen
        # This would need to be implemented with actual BART service hours
        # For now, assume if there are no departures, it's off hours
        if self.current_station and not self.current_station.departures:
            return ScreenType.SYSTEM_OFFDAY
            
        # Default to showing system status
        return ScreenType.ALWAYS_SYSTEM_STATUS