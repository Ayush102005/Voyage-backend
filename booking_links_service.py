"""
Booking Links Service - Generate Deep Links to Booking Platforms
Feature 18: Direct Booking Links

This service generates pre-filled deep links to popular booking platforms
including flights, hotels, trains, buses, and activities.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote
import re
import random

from schemas import (
    BookingLink,
    FlightBookingParams,
    HotelBookingParams,
    TrainBookingParams,
    ActivityBookingParams,
    TasteGraph
)


class BookingLinksGenerator:
    """
    Generates deep links to booking platforms with pre-filled trip details.
    
    Supported Platforms:
    - Flights: MakeMyTrip, Cleartrip, Goibibo, Skyscanner
    - Hotels: MakeMyTrip, Booking.com, Agoda, OYO, Airbnb
    - Trains: IRCTC, ConfirmTkt, RailYatri
    - Buses: RedBus, AbhiBus
    - Activities: GetYourGuide, Viator, Thrillophilia
    """
    
    def __init__(self):
        self.affiliate_codes = {
            "makemytrip": "voyage2025",
            "cleartrip": "voyage",
            "goibibo": "voyageind",
            "booking": "voyage-travel",
            "agoda": "voyage2025",
            "viator": "voyage",
            "thrillophilia": "VOYAGE"
        }
    
    # =========================================================================
    # Flight Booking Links
    # =========================================================================
    
    def generate_flight_links(self, params: FlightBookingParams) -> List[BookingLink]:
        """
        Generate flight booking deep links for multiple platforms.
        """
        links = []
        
        # MakeMyTrip Flight
        links.append(self._makemytrip_flight_link(params))
        
        # Cleartrip Flight
        links.append(self._cleartrip_flight_link(params))
        
        # Goibibo Flight
        links.append(self._goibibo_flight_link(params))
        
        # Skyscanner Flight
        links.append(self._skyscanner_flight_link(params))
        
        return links
    
    def _makemytrip_flight_link(self, params: FlightBookingParams) -> BookingLink:
        """MakeMyTrip flight deep link"""
        trip_type = "R" if params.return_date else "O"  # R=Round, O=One-way
        
        # Format: https://www.makemytrip.com/flight/search?tripType=R&from=DEL&to=GOI&date=20250115&rdate=20250122&pax=2
        url_params = {
            "tripType": trip_type,
            "from": self._get_airport_code(params.origin),
            "to": self._get_airport_code(params.destination),
            "date": params.departure_date.replace("-", ""),  # YYYYMMDD format
            "pax": params.adults + params.children,
            "class": self._cabin_to_makemytrip_class(params.cabin_class)
        }
        
        if params.return_date:
            url_params["rdate"] = params.return_date.replace("-", "")
        
        base_url = "https://www.makemytrip.com/flight/search"
        url = f"{base_url}?{urlencode(url_params)}"
        
        return BookingLink(
            platform="MakeMyTrip",
            category="flight",
            url=url,
            display_text=f"Book Flight: {params.origin} → {params.destination}",
            estimated_price=None,  # To be filled by external API if available
            description=f"Search flights on MakeMyTrip for {params.adults} passengers",
            affiliate_code=self.affiliate_codes.get("makemytrip"),
            priority=1
        )
    
    def _cleartrip_flight_link(self, params: FlightBookingParams) -> BookingLink:
        """Cleartrip flight deep link"""
        trip_type = "R" if params.return_date else "O"
        
        # Format: https://www.cleartrip.com/flights/results?from=DEL&to=GOI&depart_date=15/01/2025&adults=2&childs=0&infants=0&class=Economy
        url_params = {
            "from": self._get_airport_code(params.origin),
            "to": self._get_airport_code(params.destination),
            "depart_date": params.departure_date.replace("-", "/"),  # DD/MM/YYYY
            "adults": params.adults,
            "childs": params.children,
            "infants": 0,
            "class": params.cabin_class.capitalize(),
            "trip_type": trip_type
        }
        
        if params.return_date:
            url_params["return_date"] = params.return_date.replace("-", "/")
        
        base_url = "https://www.cleartrip.com/flights/results"
        url = f"{base_url}?{urlencode(url_params)}"
        
        return BookingLink(
            platform="Cleartrip",
            category="flight",
            url=url,
            display_text=f"Search on Cleartrip: {params.origin} → {params.destination}",
            affiliate_code=self.affiliate_codes.get("cleartrip"),
            priority=2
        )
    
    def _goibibo_flight_link(self, params: FlightBookingParams) -> BookingLink:
        """Goibibo flight deep link"""
        # Format: https://www.goibibo.com/flights/air-DEL-GOI-20250115-R-0-2-0-E/
        trip_code = "R" if params.return_date else "O"
        
        url_parts = [
            "air",
            self._get_airport_code(params.origin),
            self._get_airport_code(params.destination),
            params.departure_date.replace("-", ""),
            trip_code,
            "0",  # Infants
            str(params.adults),
            str(params.children),
            "E"  # Economy
        ]
        
        base_url = "https://www.goibibo.com/flights"
        url = f"{base_url}/{'-'.join(url_parts)}/"
        
        return BookingLink(
            platform="Goibibo",
            category="flight",
            url=url,
            display_text=f"Find deals on Goibibo",
            affiliate_code=self.affiliate_codes.get("goibibo"),
            priority=3
        )
    
    def _skyscanner_flight_link(self, params: FlightBookingParams) -> BookingLink:
        """Skyscanner flight deep link (international comparison)"""
        # Format: https://www.skyscanner.co.in/transport/flights/del/goi/250115/250122/?adults=2
        dep_date = params.departure_date.replace("-", "")[2:]  # YYMMDD
        ret_date = params.return_date.replace("-", "")[2:] if params.return_date else ""
        
        origin_code = self._get_airport_code(params.origin).lower()
        dest_code = self._get_airport_code(params.destination).lower()
        
        if ret_date:
            url = f"https://www.skyscanner.co.in/transport/flights/{origin_code}/{dest_code}/{dep_date}/{ret_date}/?adults={params.adults}"
        else:
            url = f"https://www.skyscanner.co.in/transport/flights/{origin_code}/{dest_code}/{dep_date}/?adults={params.adults}"
        
        return BookingLink(
            platform="Skyscanner",
            category="flight",
            url=url,
            display_text=f"Compare prices on Skyscanner",
            description="Compare prices across 100+ airlines",
            priority=4
        )
    
    # =========================================================================
    # Hotel Booking Links
    # =========================================================================
    
    def generate_hotel_links(self, params: HotelBookingParams) -> List[BookingLink]:
        """
        Generate hotel booking deep links for multiple platforms.
        """
        links = []
        
        # MakeMyTrip Hotels
        links.append(self._makemytrip_hotel_link(params))
        
        # Booking.com
        links.append(self._booking_com_hotel_link(params))
        
        # Agoda
        links.append(self._agoda_hotel_link(params))
        
        # OYO
        links.append(self._oyo_hotel_link(params))
        
        # Airbnb (if applicable)
        links.append(self._airbnb_link(params))
        
        return links
    
    def _makemytrip_hotel_link(self, params: HotelBookingParams) -> BookingLink:
        """MakeMyTrip hotel deep link"""
        # Format: https://www.makemytrip.com/hotels/hotel-listing/?city=GOI&checkin=01152025&checkout=01222025&roomStayQualifier=2e0e
        url_params = {
            "city": self._get_city_code(params.destination),
            "checkin": params.checkin_date.replace("-", ""),  # MMDDYYYY
            "checkout": params.checkout_date.replace("-", ""),
            "roomStayQualifier": f"{params.adults}e{params.children}e",
            "rooms": params.rooms
        }
        
        if params.hotel_name:
            url_params["searchText"] = params.hotel_name
        
        base_url = "https://www.makemytrip.com/hotels/hotel-listing/"
        url = f"{base_url}?{urlencode(url_params)}"
        
        display = params.hotel_name if params.hotel_name else f"Hotels in {params.destination}"
        
        return BookingLink(
            platform="MakeMyTrip",
            category="hotel",
            url=url,
            display_text=f"Book: {display}",
            item_name=params.hotel_name,
            description=f"{params.rooms} room(s), {params.adults} adults",
            affiliate_code=self.affiliate_codes.get("makemytrip"),
            priority=1
        )
    
    def _booking_com_hotel_link(self, params: HotelBookingParams) -> BookingLink:
        """Booking.com hotel deep link"""
        # Format: https://www.booking.com/searchresults.html?ss=Goa&checkin=2025-01-15&checkout=2025-01-22&group_adults=2&no_rooms=1
        url_params = {
            "ss": params.destination,
            "checkin": params.checkin_date,
            "checkout": params.checkout_date,
            "group_adults": params.adults,
            "group_children": params.children,
            "no_rooms": params.rooms,
            "aid": self.affiliate_codes.get("booking")
        }
        
        if params.hotel_name:
            url_params["ss"] = f"{params.hotel_name}, {params.destination}"
        
        base_url = "https://www.booking.com/searchresults.html"
        url = f"{base_url}?{urlencode(url_params)}"
        
        return BookingLink(
            platform="Booking.com",
            category="hotel",
            url=url,
            display_text=f"Search on Booking.com",
            item_name=params.hotel_name,
            description="Free cancellation available on most properties",
            affiliate_code=self.affiliate_codes.get("booking"),
            priority=2
        )
    
    def _agoda_hotel_link(self, params: HotelBookingParams) -> BookingLink:
        """Agoda hotel deep link"""
        # Format: https://www.agoda.com/search?city=12345&checkIn=2025-01-15&checkOut=2025-01-22&rooms=1&adults=2
        url_params = {
            "city": params.destination,
            "checkIn": params.checkin_date,
            "checkOut": params.checkout_date,
            "rooms": params.rooms,
            "adults": params.adults,
            "children": params.children,
            "cid": self.affiliate_codes.get("agoda")
        }
        
        base_url = "https://www.agoda.com/search"
        url = f"{base_url}?{urlencode(url_params)}"
        
        return BookingLink(
            platform="Agoda",
            category="hotel",
            url=url,
            display_text=f"Check Agoda deals",
            description="Best price guarantee + rewards",
            affiliate_code=self.affiliate_codes.get("agoda"),
            priority=3
        )
    
    def _oyo_hotel_link(self, params: HotelBookingParams) -> BookingLink:
        """OYO hotel deep link"""
        # Format: https://www.oyorooms.com/search/?location=Goa&checkin=15/01/2025&checkout=22/01/2025&guests=2
        url_params = {
            "location": params.destination,
            "checkin": params.checkin_date.replace("-", "/"),
            "checkout": params.checkout_date.replace("-", "/"),
            "guests": params.adults + params.children,
            "rooms": params.rooms
        }
        
        base_url = "https://www.oyorooms.com/search/"
        url = f"{base_url}?{urlencode(url_params)}"
        
        return BookingLink(
            platform="OYO",
            category="hotel",
            url=url,
            display_text=f"Browse OYO hotels",
            description="Budget-friendly hotels across India",
            priority=4
        )
    
    def _airbnb_link(self, params: HotelBookingParams) -> BookingLink:
        """Airbnb deep link"""
        # Format: https://www.airbnb.co.in/s/Goa/homes?checkin=2025-01-15&checkout=2025-01-22&adults=2
        url_params = {
            "checkin": params.checkin_date,
            "checkout": params.checkout_date,
            "adults": params.adults,
            "children": params.children
        }
        
        location_slug = params.destination.replace(" ", "-")
        base_url = f"https://www.airbnb.co.in/s/{location_slug}/homes"
        url = f"{base_url}?{urlencode(url_params)}"
        
        return BookingLink(
            platform="Airbnb",
            category="hotel",
            url=url,
            display_text=f"Find unique stays on Airbnb",
            description="Apartments, villas, and unique accommodations",
            priority=5
        )
    
    # =========================================================================
    # Train Booking Links
    # =========================================================================
    
    def generate_train_links(self, params: TrainBookingParams) -> List[BookingLink]:
        """
        Generate train booking deep links.
        """
        links = []
        
        # IRCTC (official)
        links.append(self._irctc_train_link(params))
        
        # ConfirmTkt
        links.append(self._confirmtkt_link(params))
        
        # RailYatri
        links.append(self._railyatri_link(params))
        
        return links
    
    def _irctc_train_link(self, params: TrainBookingParams) -> BookingLink:
        """IRCTC train booking deep link"""
        # IRCTC doesn't support direct deep linking with parameters for security
        # But we can link to the homepage with instructions
        url = "https://www.irctc.co.in/nget/train-search"
        
        return BookingLink(
            platform="IRCTC",
            category="train",
            url=url,
            display_text=f"Book Train: {params.origin} → {params.destination}",
            description=f"Official railway booking • Journey: {params.journey_date} • Class: {params.class_type}",
            priority=1
        )
    
    def _confirmtkt_link(self, params: TrainBookingParams) -> BookingLink:
        """ConfirmTkt train booking deep link"""
        # Format: https://www.confirmtkt.com/trains/from-DEL-to-GOI-on-20250115
        origin_code = self._get_station_code(params.origin)
        dest_code = self._get_station_code(params.destination)
        date = params.journey_date.replace("-", "")
        
        url = f"https://www.confirmtkt.com/trains/from-{origin_code}-to-{dest_code}-on-{date}"
        
        return BookingLink(
            platform="ConfirmTkt",
            category="train",
            url=url,
            display_text=f"Check availability on ConfirmTkt",
            description="Train availability, PNR status, and seat alerts",
            priority=2
        )
    
    def _railyatri_link(self, params: TrainBookingParams) -> BookingLink:
        """RailYatri train booking deep link"""
        url_params = {
            "from_code": self._get_station_code(params.origin),
            "to_code": self._get_station_code(params.destination),
            "date": params.journey_date,
            "class": params.class_type,
            "quota": params.quota
        }
        
        base_url = "https://www.railyatri.in/train-ticket/search"
        url = f"{base_url}?{urlencode(url_params)}"
        
        return BookingLink(
            platform="RailYatri",
            category="train",
            url=url,
            display_text=f"Search on RailYatri",
            description="Live train tracking and updates",
            priority=3
        )
    
    # =========================================================================
    # Bus Booking Links
    # =========================================================================
    
    def generate_bus_links(self, origin: str, destination: str, date: str) -> List[BookingLink]:
        """
        Generate bus booking deep links.
        """
        links = []
        
        # RedBus
        links.append(self._redbus_link(origin, destination, date))
        
        # AbhiBus
        links.append(self._abhibus_link(origin, destination, date))
        
        return links
    
    def _redbus_link(self, origin: str, destination: str, date: str) -> BookingLink:
        """RedBus deep link"""
        # Format: https://www.redbus.in/bus-tickets/delhi-to-agra?fromCityName=Delhi&toCityName=Agra&onward=15-Jan-2025
        origin_slug = origin.lower().replace(" ", "-")
        dest_slug = destination.lower().replace(" ", "-")
        
        # Convert date format
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d-%b-%Y")
        
        url = f"https://www.redbus.in/bus-tickets/{origin_slug}-to-{dest_slug}?fromCityName={origin}&toCityName={destination}&onward={formatted_date}"
        
        return BookingLink(
            platform="RedBus",
            category="bus",
            url=url,
            display_text=f"Book Bus: {origin} → {destination}",
            description="India's largest bus booking platform",
            priority=1
        )
    
    def _abhibus_link(self, origin: str, destination: str, date: str) -> BookingLink:
        """AbhiBus deep link"""
        url_params = {
            "source": origin,
            "destination": destination,
            "date": date
        }
        
        base_url = "https://www.abhibus.com/bus_search"
        url = f"{base_url}?{urlencode(url_params)}"
        
        return BookingLink(
            platform="AbhiBus",
            category="bus",
            url=url,
            display_text=f"Compare on AbhiBus",
            description="24/7 customer support",
            priority=2
        )
    
    # =========================================================================
    # Activity/Experience Booking Links
    # =========================================================================
    
    def generate_activity_links(self, params: ActivityBookingParams) -> List[BookingLink]:
        """
        Generate activity/experience booking deep links.
        """
        links = []
        
        # Thrillophilia
        links.append(self._thrillophilia_link(params))
        
        # GetYourGuide
        links.append(self._getyourguide_link(params))
        
        # Viator
        links.append(self._viator_link(params))
        
        return links
    
    def _thrillophilia_link(self, params: ActivityBookingParams) -> BookingLink:
        """Thrillophilia activity deep link"""
        destination_slug = params.destination.lower().replace(" ", "-")
        
        if params.activity_name:
            # Search for specific activity
            url = f"https://www.thrillophilia.com/search?q={quote(params.activity_name)}"
        else:
            # Browse destination
            url = f"https://www.thrillophilia.com/{destination_slug}"
        
        return BookingLink(
            platform="Thrillophilia",
            category="activity",
            url=url,
            display_text=f"Explore activities in {params.destination}",
            item_name=params.activity_name,
            description="Tours, activities, and experiences",
            affiliate_code=self.affiliate_codes.get("thrillophilia"),
            priority=1
        )
    
    def _getyourguide_link(self, params: ActivityBookingParams) -> BookingLink:
        """GetYourGuide activity deep link"""
        destination_slug = params.destination.lower().replace(" ", "-")
        
        url = f"https://www.getyourguide.com/s/?q={quote(params.destination)}"
        
        if params.activity_type:
            url += f"&activity_type={params.activity_type}"
        
        return BookingLink(
            platform="GetYourGuide",
            category="activity",
            url=url,
            display_text=f"Find tours on GetYourGuide",
            description="Skip-the-line tickets and guided tours",
            priority=2
        )
    
    def _viator_link(self, params: ActivityBookingParams) -> BookingLink:
        """Viator activity deep link"""
        url_params = {
            "searchQuery": params.destination
        }
        
        if params.activity_name:
            url_params["searchQuery"] = params.activity_name
        
        base_url = "https://www.viator.com/searchResults/all"
        url = f"{base_url}?{urlencode(url_params)}"
        
        return BookingLink(
            platform="Viator",
            category="activity",
            url=url,
            display_text=f"Browse Viator experiences",
            description="Trusted by TripAdvisor",
            affiliate_code=self.affiliate_codes.get("viator"),
            priority=3
        )
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _get_airport_code(self, city: str) -> str:
        """Get IATA airport code for a city"""
        # Major Indian cities airport codes
        airport_codes = {
            "delhi": "DEL",
            "mumbai": "BOM",
            "bangalore": "BLR",
            "bengaluru": "BLR",
            "kolkata": "CCU",
            "chennai": "MAA",
            "hyderabad": "HYD",
            "pune": "PNQ",
            "ahmedabad": "AMD",
            "goa": "GOI",
            "jaipur": "JAI",
            "kochi": "COK",
            "cochin": "COK",
            "trivandrum": "TRV",
            "thiruvananthapuram": "TRV",
            "lucknow": "LKO",
            "chandigarh": "IXC",
            "guwahati": "GAU",
            "bhubaneswar": "BBI",
            "raipur": "RPR",
            "indore": "IDR",
            "nagpur": "NAG",
            "srinagar": "SXR",
            "amritsar": "ATQ",
            "varanasi": "VNS",
            "benaras": "VNS",
            "udaipur": "UDR",
            "jodhpur": "JDH",
            "agra": "AGR",
            "patna": "PAT",
            "ranchi": "IXR",
            "visakhapatnam": "VTZ",
            "vijayawada": "VGA",
            "coimbatore": "CJB",
            "madurai": "IXM",
            "mangalore": "IXE",
            "port blair": "IXZ"
        }
        
        city_lower = city.lower().strip()
        return airport_codes.get(city_lower, city[:3].upper())
    
    def _get_city_code(self, city: str) -> str:
        """Get city code for booking platforms"""
        # Simplified - in production, use proper city code API
        return city[:3].upper()
    
    def _get_station_code(self, station: str) -> str:
        """Get railway station code"""
        # Major Indian railway station codes
        station_codes = {
            "delhi": "NDLS",
            "new delhi": "NDLS",
            "mumbai": "CSTM",
            "bangalore": "SBC",
            "bengaluru": "SBC",
            "chennai": "MAS",
            "kolkata": "HWH",
            "howrah": "HWH",
            "hyderabad": "HYB",
            "pune": "PUNE",
            "ahmedabad": "ADI",
            "jaipur": "JP",
            "lucknow": "LKO",
            "kanpur": "CNB",
            "nagpur": "NGP",
            "indore": "INDB",
            "bhopal": "BPL",
            "patna": "PNBE",
            "agra": "AGC",
            "varanasi": "BSB",
            "allahabad": "ALD",
            "prayagraj": "ALD",
            "amritsar": "ASR",
            "chandigarh": "CDG",
            "dehradun": "DDN",
            "haridwar": "HW",
            "rishikesh": "RKSH",
            "jammu": "JAT",
            "udaipur": "UDZ",
            "jodhpur": "JU",
            "ajmer": "AII",
            "goa": "MAO",
            "kochi": "ERS",
            "trivandrum": "TVC"
        }
        
        station_lower = station.lower().strip()
        return station_codes.get(station_lower, station[:3].upper())
    
    def _cabin_to_makemytrip_class(self, cabin: str) -> str:
        """Convert cabin class to MakeMyTrip format"""
        mapping = {
            "economy": "E",
            "premium economy": "PE",
            "business": "B",
            "first": "F",
            "first class": "F"
        }
        return mapping.get(cabin.lower(), "E")
    
    # =========================================================================
    # Personalized Recommendations (Feature 18.1 - Taste Graph Integration)
    # =========================================================================
    
    def personalize_booking_links(
        self, 
        links: List[BookingLink], 
        taste_graph: Optional[TasteGraph] = None
    ) -> List[BookingLink]:
        """
        Personalize booking link recommendations based on user's taste graph.
        
        - Boost platforms user has booked with before
        - Adjust priorities based on preferences
        - Add personalized descriptions
        """
        if not taste_graph or not links:
            return links
        
        # Extract user preferences
        budget_patterns = taste_graph.budget_patterns or {}
        avg_budget = budget_patterns.get("average_per_trip", 50000)
        preferred_trip_types = taste_graph.preferred_trip_types or []
        
        personalized_links = []
        
        for link in links:
            # Boost priority for budget-friendly platforms if user is budget-conscious
            if avg_budget < 40000:  # Budget traveler
                if link.platform in ["OYO", "RedBus", "AbhiBus", "Goibibo"]:
                    link.priority = max(1, link.priority - 1)  # Boost priority
                    link.description = f"💰 Budget-friendly option • {link.description or ''}"
            
            elif avg_budget > 80000:  # Luxury traveler
                if link.platform in ["Airbnb", "Booking.com", "MakeMyTrip"]:
                    link.priority = max(1, link.priority - 1)
                    link.description = f"✨ Premium option • {link.description or ''}"
            
            # Add personalized notes based on trip types
            if "adventure" in preferred_trip_types and link.category == "activity":
                link.description = f"🏔️ Perfect for adventure lovers! • {link.description or ''}"
            
            if "luxury" in preferred_trip_types and link.category == "hotel":
                link.description = f"👑 Curated for luxury travelers • {link.description or ''}"
            
            personalized_links.append(link)
        
        # Re-sort by priority
        personalized_links.sort(key=lambda x: x.priority)
        
        return personalized_links
    
    # =========================================================================
    # Live Price Estimation (Feature 18.2 - Price Intelligence)
    # =========================================================================
    
    def estimate_prices(
        self,
        links: List[BookingLink],
        trip_details: dict,
        use_ml_model: bool = False
    ) -> List[BookingLink]:
        """
        Add estimated prices to booking links.
        
        For now, uses rule-based estimation. Future: ML model or live API calls.
        
        Args:
            links: Booking links to add prices to
            trip_details: Trip information (origin, destination, dates, passengers)
            use_ml_model: Whether to use ML model (future feature)
        """
        for link in links:
            if link.category == "flight":
                link.estimated_price = self._estimate_flight_price(trip_details)
            
            elif link.category == "hotel":
                link.estimated_price = self._estimate_hotel_price(trip_details)
            
            elif link.category == "train":
                link.estimated_price = self._estimate_train_price(trip_details)
            
            elif link.category == "bus":
                link.estimated_price = self._estimate_bus_price(trip_details)
            
            elif link.category == "activity":
                link.estimated_price = self._estimate_activity_price(trip_details)
        
        return links
    
    def _estimate_flight_price(self, trip_details: dict) -> float:
        """Estimate flight price based on route and passengers"""
        origin = trip_details.get("origin", "").lower()
        destination = trip_details.get("destination", "").lower()
        passengers = trip_details.get("num_people", 1)
        num_days = trip_details.get("num_days", 7)
        
        # Base prices (per person, round trip) for popular routes
        route_prices = {
            ("delhi", "goa"): 8500,
            ("delhi", "mumbai"): 5500,
            ("delhi", "bangalore"): 7500,
            ("mumbai", "goa"): 6000,
            ("mumbai", "bangalore"): 5000,
            ("bangalore", "goa"): 6500,
            ("delhi", "kerala"): 9500,
            ("delhi", "chennai"): 8000,
            ("mumbai", "delhi"): 5500,
            ("kolkata", "goa"): 9000,
        }
        
        # Try exact match
        route_key = (origin, destination)
        base_price = route_prices.get(route_key)
        
        # Try reverse route
        if not base_price:
            reverse_key = (destination, origin)
            base_price = route_prices.get(reverse_key)
        
        # Default if route not found
        if not base_price:
            # Estimate based on distance (rough)
            base_price = 6000 + random.randint(-1000, 2000)
        
        # Adjust for seasonality (Nov-Feb = peak winter season in India)
        current_month = datetime.now().month
        if current_month in [11, 12, 1, 2]:  # Winter peak season
            base_price *= 1.3
        elif current_month in [6, 7, 8, 9]:  # Monsoon off-season
            base_price *= 0.8
        
        # Adjust for advance booking (assume 30 days advance)
        base_price *= 0.95  # 5% discount for advance booking
        
        # Total for all passengers
        total_price = base_price * passengers
        
        return round(total_price, 0)
    
    def _estimate_hotel_price(self, trip_details: dict) -> float:
        """Estimate hotel price based on destination and duration"""
        destination = trip_details.get("destination", "").lower()
        num_days = trip_details.get("num_days", 7)
        num_people = trip_details.get("num_people", 2)
        
        # Per night prices for popular destinations (3-star hotel)
        destination_prices = {
            "goa": 2500,
            "mumbai": 3500,
            "delhi": 3000,
            "bangalore": 3200,
            "jaipur": 2800,
            "udaipur": 3500,
            "kerala": 3000,
            "agra": 2500,
            "varanasi": 2000,
            "rishikesh": 2200,
            "manali": 2800,
            "shimla": 2500,
        }
        
        per_night = destination_prices.get(destination, 2800)
        
        # Adjust for seasonality
        current_month = datetime.now().month
        if current_month in [11, 12, 1, 2]:
            per_night *= 1.4  # Peak winter season
        elif current_month in [6, 7, 8]:
            per_night *= 0.7  # Monsoon discounts
        
        # Calculate rooms needed
        rooms = 1 if num_people <= 2 else (num_people + 1) // 2
        
        total_price = per_night * num_days * rooms
        
        return round(total_price, 0)
    
    def _estimate_train_price(self, trip_details: dict) -> float:
        """Estimate train price based on route"""
        origin = trip_details.get("origin", "").lower()
        destination = trip_details.get("destination", "").lower()
        passengers = trip_details.get("num_people", 1)
        
        # Base prices (3A class, one way)
        route_prices = {
            ("delhi", "goa"): 2500,
            ("delhi", "mumbai"): 1500,
            ("delhi", "bangalore"): 2800,
            ("mumbai", "goa"): 1200,
            ("delhi", "kerala"): 3200,
            ("delhi", "jaipur"): 800,
            ("delhi", "agra"): 400,
        }
        
        route_key = (origin, destination)
        base_price = route_prices.get(route_key, route_prices.get((destination, origin), 2000))
        
        # Round trip
        total_price = base_price * 2 * passengers
        
        return round(total_price, 0)
    
    def _estimate_bus_price(self, trip_details: dict) -> float:
        """Estimate bus price"""
        origin = trip_details.get("origin", "").lower()
        destination = trip_details.get("destination", "").lower()
        passengers = trip_details.get("num_people", 1)
        
        # Per person, one way (sleeper bus)
        base_prices = {
            ("delhi", "agra"): 600,
            ("delhi", "jaipur"): 800,
            ("mumbai", "pune"): 500,
            ("bangalore", "goa"): 1200,
            ("delhi", "manali"): 1500,
        }
        
        route_key = (origin, destination)
        base_price = base_prices.get(route_key, base_prices.get((destination, origin), 800))
        
        # Round trip
        total_price = base_price * 2 * passengers
        
        return round(total_price, 0)
    
    def _estimate_activity_price(self, trip_details: dict) -> float:
        """Estimate activity/experience price"""
        destination = trip_details.get("destination", "").lower()
        num_people = trip_details.get("num_people", 2)
        
        # Per person average for activities in destination
        activity_prices = {
            "goa": 2500,  # Water sports, beach activities
            "manali": 3000,  # Paragliding, skiing
            "rishikesh": 2800,  # Rafting, bungee jumping
            "jaipur": 1500,  # City tours, heritage walks
            "agra": 1000,  # Taj Mahal tours
            "kerala": 2000,  # Backwater cruises
            "ladakh": 4000,  # Adventure activities
        }
        
        per_person = activity_prices.get(destination, 2000)
        total_price = per_person * num_people
        
        return round(total_price, 0)
    
    def get_best_deal(self, links: List[BookingLink]) -> Optional[BookingLink]:
        """
        Find the best deal from a list of booking links.
        Best deal = lowest price with priority <= 3
        """
        if not links:
            return None
        
        # Filter links with prices and good priority
        priced_links = [
            link for link in links 
            if link.estimated_price and link.priority <= 3
        ]
        
        if not priced_links:
            return None
        
        # Sort by price (ascending)
        priced_links.sort(key=lambda x: x.estimated_price)
        
        return priced_links[0]
    
    def get_price_comparison_summary(self, links: List[BookingLink]) -> dict:
        """
        Generate price comparison summary across platforms.
        """
        if not links:
            return {}
        
        priced_links = [link for link in links if link.estimated_price]
        
        if not priced_links:
            return {}
        
        prices = [link.estimated_price for link in priced_links]
        
        return {
            "lowest_price": min(prices),
            "highest_price": max(prices),
            "average_price": sum(prices) / len(prices),
            "price_range": max(prices) - min(prices),
            "savings_potential": max(prices) - min(prices),
            "cheapest_platform": min(priced_links, key=lambda x: x.estimated_price).platform,
            "total_options": len(priced_links)
        }


# Singleton instance
_booking_links_generator = None

def get_booking_links_generator() -> BookingLinksGenerator:
    """Get singleton instance of BookingLinksGenerator"""
    global _booking_links_generator
    if _booking_links_generator is None:
        _booking_links_generator = BookingLinksGenerator()
    return _booking_links_generator
