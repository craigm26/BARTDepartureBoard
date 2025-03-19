from enum import Enum

class ScreenType(Enum):
    """Kinds of screen we render"""
    ALWAYS_NEWS = "news"
    ALWAYS_SYSTEM_STATUS = "system_status"
    SYSTEM_OFFDAY = "system_offday"  # BART system not running (late night), implies at least news
    PREFERRED_STATION_OFFDAY = (
        "preferred_station_offday"  # No trains at preferred station AND news/system_status are enabled for station offdays
    )
    DEPARTURES = "departures"  # Trains are running today. May also show system status and news if no trains are live
