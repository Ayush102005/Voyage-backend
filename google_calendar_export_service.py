"""
Google Calendar Export Service for Voyage Travel Planner
Exports trip itineraries to Google Calendar with one click
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import re
import json
from urllib.parse import quote
from schemas import CalendarEvent, SavedTripPlan


class GoogleCalendarExportService:
    """
    Service to export trip itineraries to Google Calendar.
    Generates calendar events and provides Google Calendar URLs.
    """
    
    def __init__(self, firestore_db):
        """Initialize with Firestore database reference"""
        self.db = firestore_db
    
    def export_trip_to_calendar(
        self,
        trip_id: str,
        trip_start_date: datetime,
        timezone: str = "Asia/Kolkata",
        include_flights: bool = True,
        include_hotels: bool = True,
        include_activities: bool = True,
        include_transport: bool = True
    ) -> Tuple[List[CalendarEvent], str]:
        """
        Export trip to Google Calendar format
        
        Args:
            trip_id: Firestore trip document ID
            trip_start_date: When the trip starts
            timezone: User's timezone
            include_flights: Include flight bookings
            include_hotels: Include hotel check-ins/outs
            include_activities: Include activities
            include_transport: Include transport
        
        Returns:
            Tuple of (events list, Google Calendar URL)
        """
        # Get trip from Firestore
        trip_doc = self.db.collection('trip_plans').document(trip_id).get()
        
        if not trip_doc.exists:
            raise ValueError(f"Trip {trip_id} not found")
        
        trip_data = trip_doc.to_dict()
        
        # Parse itinerary
        events = self._parse_itinerary_to_events(
            trip_data=trip_data,
            trip_start_date=trip_start_date,
            include_flights=include_flights,
            include_hotels=include_hotels,
            include_activities=include_activities,
            include_transport=include_transport
        )
        
        # Generate Google Calendar URL
        calendar_url = self._generate_google_calendar_url(events, timezone)
        
        return events, calendar_url
    
    def _parse_itinerary_to_events(
        self,
        trip_data: Dict,
        trip_start_date: datetime,
        include_flights: bool,
        include_hotels: bool,
        include_activities: bool,
        include_transport: bool
    ) -> List[CalendarEvent]:
        """
        Parse trip itinerary text into calendar events
        """
        events = []
        # Support both 'itinerary' and 'trip_plan' field names
        itinerary = trip_data.get('trip_plan') or trip_data.get('itinerary', '')
        destination = trip_data.get('destination', 'Trip')
        
        # Add flight events (if available and included)
        if include_flights:
            flight_events = self._extract_flight_events(itinerary, trip_start_date, destination)
            events.extend(flight_events)
        
        # Add hotel check-in/out events
        if include_hotels:
            hotel_events = self._extract_hotel_events(itinerary, trip_start_date, destination)
            events.extend(hotel_events)
        
        # Parse day-by-day itinerary
        if include_activities or include_transport:
            day_events = self._parse_daily_activities(
                itinerary, 
                trip_start_date, 
                destination,
                include_activities,
                include_transport
            )
            events.extend(day_events)
        
        # Add full-day overview events for each day
        num_days = self._extract_num_days(itinerary)
        for day_num in range(1, num_days + 1):
            current_date = trip_start_date + timedelta(days=day_num - 1)
            
            # Extract day summary from itinerary
            day_pattern = rf'Day\s+{day_num}:?\s*(.*?)(?=Day\s+\d+:|$)'
            day_match = re.search(day_pattern, itinerary, re.IGNORECASE | re.DOTALL)
            
            if day_match:
                day_content = day_match.group(1).strip()
                # Get first line or first 100 chars as summary
                first_line = day_content.split('\n')[0] if day_content else f"Day {day_num} in {destination}"
                summary = first_line[:100] if len(first_line) > 100 else first_line
            else:
                summary = f"Day {day_num} in {destination}"
            
            # Create all-day event
            events.append(CalendarEvent(
                title=f"🌍 Trip Day {day_num}: {summary}",
                description=day_content[:500] if day_match else f"Day {day_num} of your trip to {destination}",
                location=destination,
                start_time=current_date.replace(hour=0, minute=0, second=0),
                end_time=(current_date + timedelta(days=1)).replace(hour=0, minute=0, second=0),
                event_type="trip_day",
                day_number=day_num,
                is_all_day=True
            ))
        
        return events
    
    def _extract_flight_events(
        self, 
        itinerary: str, 
        trip_start_date: datetime,
        destination: str
    ) -> List[CalendarEvent]:
        """Extract flight information from itinerary"""
        events = []
        
        # Look for outbound flight patterns
        outbound_patterns = [
            r'(?:Departure|Outbound|Flight to).{0,50}?(\d{1,2}:\d{2}\s*(?:AM|PM))',
            r'(?:Depart|Leave).{0,50}?(?:at\s+)?(\d{1,2}:\d{2}\s*(?:AM|PM))',
        ]
        
        for pattern in outbound_patterns:
            match = re.search(pattern, itinerary, re.IGNORECASE)
            if match:
                time_str = match.group(1)
                flight_time = self._parse_time_string(time_str)
                
                start_time = trip_start_date.replace(
                    hour=flight_time.hour,
                    minute=flight_time.minute
                )
                
                events.append(CalendarEvent(
                    title=f"✈️ Flight to {destination}",
                    description=f"Departure flight to {destination}. Check-in 2 hours early.",
                    location="Airport",
                    start_time=start_time - timedelta(hours=2),  # 2 hours before flight
                    end_time=start_time,
                    event_type="flight",
                    day_number=0
                ))
                break
        
        # Look for return flight patterns
        return_patterns = [
            r'(?:Return|Flight back|Departure from).{0,50}?(\d{1,2}:\d{2}\s*(?:AM|PM))',
            r'Day\s+(\d+).{0,200}?(?:Return|Flight back).{0,50}?(\d{1,2}:\d{2}\s*(?:AM|PM))',
        ]
        
        num_days = self._extract_num_days(itinerary)
        
        for pattern in return_patterns:
            match = re.search(pattern, itinerary, re.IGNORECASE)
            if match:
                groups = match.groups()
                time_str = groups[-1]  # Last group is always the time
                
                if len(groups) > 1 and groups[0].isdigit():
                    day_num = int(groups[0])
                else:
                    day_num = num_days
                
                flight_time = self._parse_time_string(time_str)
                return_date = trip_start_date + timedelta(days=day_num - 1)
                
                start_time = return_date.replace(
                    hour=flight_time.hour,
                    minute=flight_time.minute
                )
                
                events.append(CalendarEvent(
                    title=f"✈️ Return Flight",
                    description=f"Return flight from {destination}. Check-in 2 hours early.",
                    location="Airport",
                    start_time=start_time - timedelta(hours=2),
                    end_time=start_time,
                    event_type="flight",
                    day_number=day_num
                ))
                break
        
        return events
    
    def _extract_hotel_events(
        self,
        itinerary: str,
        trip_start_date: datetime,
        destination: str
    ) -> List[CalendarEvent]:
        """Extract hotel check-in/out information"""
        events = []
        
        # Look for hotel mentions
        hotel_pattern = r'(?:Hotel|Stay at|Accommodation|Check-in).{0,100}?([A-Z][a-zA-Z\s&]+(?:Hotel|Resort|Lodge|Inn|Guest House|Homestay))'
        hotel_matches = re.finditer(hotel_pattern, itinerary, re.IGNORECASE)
        
        hotel_names = []
        for match in hotel_matches:
            hotel_name = match.group(1).strip()
            if hotel_name not in hotel_names:
                hotel_names.append(hotel_name)
        
        # If no specific hotel found, use generic
        if not hotel_names:
            hotel_names = [f"Hotel in {destination}"]
        
        # Add check-in event (Day 1, 2:00 PM)
        check_in_time = trip_start_date.replace(hour=14, minute=0)
        events.append(CalendarEvent(
            title=f"🏨 Hotel Check-in: {hotel_names[0]}",
            description=f"Check-in at {hotel_names[0]}. Standard check-in time: 2:00 PM",
            location=f"{hotel_names[0]}, {destination}",
            start_time=check_in_time,
            end_time=check_in_time + timedelta(hours=1),
            event_type="hotel",
            day_number=1
        ))
        
        # Add check-out event (Last day, 11:00 AM)
        num_days = self._extract_num_days(itinerary)
        check_out_time = trip_start_date + timedelta(days=num_days - 1)
        check_out_time = check_out_time.replace(hour=11, minute=0)
        
        events.append(CalendarEvent(
            title=f"🏨 Hotel Check-out: {hotel_names[0]}",
            description=f"Check-out from {hotel_names[0]}. Standard check-out time: 11:00 AM",
            location=f"{hotel_names[0]}, {destination}",
            start_time=check_out_time,
            end_time=check_out_time + timedelta(hours=1),
            event_type="hotel",
            day_number=num_days
        ))
        
        return events
    
    def _parse_daily_activities(
        self,
        itinerary: str,
        trip_start_date: datetime,
        destination: str,
        include_activities: bool,
        include_transport: bool
    ) -> List[CalendarEvent]:
        """Parse day-by-day activities from itinerary"""
        events = []
        
        # Split itinerary by days
        day_pattern = r'Day\s+(\d+):?\s*(.*?)(?=Day\s+\d+:|$)'
        day_matches = re.finditer(day_pattern, itinerary, re.IGNORECASE | re.DOTALL)
        
        for match in day_matches:
            day_num = int(match.group(1))
            day_content = match.group(2).strip()
            
            current_date = trip_start_date + timedelta(days=day_num - 1)
            
            # Extract activities for this day
            activity_events = self._extract_activities_from_day(
                day_content,
                current_date,
                day_num,
                destination,
                include_activities,
                include_transport
            )
            events.extend(activity_events)
        
        return events
    
    def _extract_activities_from_day(
        self,
        day_content: str,
        date: datetime,
        day_num: int,
        destination: str,
        include_activities: bool,
        include_transport: bool
    ) -> List[CalendarEvent]:
        """Extract activities from a single day's content"""
        events = []
        
        # Time-based activity patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s*[-–—:]\s*([^\n.]+)',
            r'(\d{1,2}\s*(?:AM|PM))\s*[-–—:]\s*([^\n.]+)',
            r'(\d{1,2}:\d{2})\s*[-–—:]\s*([^\n.]+)',
        ]
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, day_content, re.IGNORECASE)
            
            for match in matches:
                time_str = match.group(1)
                activity_desc = match.group(2).strip()
                
                # Determine if transport or activity
                is_transport = any(word in activity_desc.lower() for word in [
                    'drive', 'taxi', 'bus', 'train', 'transfer', 'depart', 'arrive', 'travel'
                ])
                
                if (is_transport and not include_transport) or (not is_transport and not include_activities):
                    continue
                
                event_type = "transport" if is_transport else "activity"
                icon = "🚗" if is_transport else "📍"
                
                try:
                    start_time_obj = self._parse_time_string(time_str)
                    start_time = date.replace(
                        hour=start_time_obj.hour,
                        minute=start_time_obj.minute
                    )
                    
                    # Estimate duration (1-2 hours for activities, 30 min for transport)
                    duration = timedelta(minutes=30) if is_transport else timedelta(hours=1.5)
                    end_time = start_time + duration
                    
                    events.append(CalendarEvent(
                        title=f"{icon} {activity_desc[:50]}",
                        description=activity_desc,
                        location=destination,
                        start_time=start_time,
                        end_time=end_time,
                        event_type=event_type,
                        day_number=day_num
                    ))
                except Exception as e:
                    print(f"Error parsing time '{time_str}': {e}")
                    continue
        
        # If no timed activities found, create generic day event
        if not events and include_activities:
            # Extract main activities (bullet points or numbered list)
            activity_lines = []
            for line in day_content.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or 
                           re.match(r'^\d+\.', line) or re.match(r'^[A-Z]', line)):
                    activity_lines.append(line.lstrip('-•0123456789. ').strip())
            
            if activity_lines:
                main_activity = activity_lines[0] if activity_lines else f"Explore {destination}"
                
                # Morning activity (9:00 AM - 12:00 PM)
                morning_start = date.replace(hour=9, minute=0)
                events.append(CalendarEvent(
                    title=f"📍 {main_activity[:50]}",
                    description="\n".join(activity_lines),
                    location=destination,
                    start_time=morning_start,
                    end_time=morning_start + timedelta(hours=3),
                    event_type="activity",
                    day_number=day_num
                ))
        
        return events
    
    def _parse_time_string(self, time_str: str) -> datetime:
        """Parse time string to datetime object"""
        time_str = time_str.strip().upper()
        
        # Try different time formats
        formats = [
            '%I:%M %p',  # 2:30 PM
            '%I:%M%p',   # 2:30PM
            '%I %p',     # 2 PM
            '%I%p',      # 2PM
            '%H:%M',     # 14:30
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        # Default to 9:00 AM if parsing fails
        return datetime.strptime('9:00 AM', '%I:%M %p')
    
    def _extract_num_days(self, itinerary: str) -> int:
        """Extract number of days from itinerary"""
        # Look for highest day number
        day_matches = re.findall(r'Day\s+(\d+)', itinerary, re.IGNORECASE)
        if day_matches:
            return max(int(day) for day in day_matches)
        return 7  # Default
    
    def _generate_google_calendar_url(
        self,
        events: List[CalendarEvent],
        timezone: str = "Asia/Kolkata"
    ) -> str:
        """
        Generate Google Calendar URL to add the first event.
        Note: Google Calendar URL scheme only supports adding ONE event at a time.
        For multiple events, users should download and import the ICS file instead.
        """
        if not events:
            return ""
        
        # IMPORTANT: Google Calendar URL only adds ONE event
        # For multiple events, the ICS file must be used
        first_event = events[0]
        
        # Format dates for Google Calendar (YYYYMMDDTHHMMSS)
        start_str = first_event.start_time.strftime('%Y%m%dT%H%M%S')
        end_str = first_event.end_time.strftime('%Y%m%dT%H%M%S')
        
        # Build URL parameters
        params = {
            'action': 'TEMPLATE',
            'text': first_event.title,
            'dates': f"{start_str}/{end_str}",
            'details': f"{first_event.description}\n\nNote: This is event 1 of {len(events)}. To add all events, please download and import the ICS file.",
            'location': first_event.location,
            'ctz': timezone
        }
        
        # Build URL
        base_url = 'https://calendar.google.com/calendar/render'
        url_params = '&'.join(f"{k}={quote(str(v))}" for k, v in params.items())
        
        return f"{base_url}?{url_params}"
    
    def generate_ics_file(self, events: List[CalendarEvent], trip_title: str) -> str:
        """
        Generate ICS (iCalendar) file content for download.
        Users can import this file into any calendar app (Google Calendar, Outlook, Apple Calendar).
        """
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Voyage Travel Planner//EN",
            f"X-WR-CALNAME:{trip_title}",
            "X-WR-TIMEZONE:Asia/Kolkata",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]
        
        for i, event in enumerate(events):
            # Format times in UTC
            start_utc = event.start_time.strftime('%Y%m%dT%H%M%SZ')
            end_utc = event.end_time.strftime('%Y%m%dT%H%M%SZ')
            created = datetime.now().strftime('%Y%m%dT%H%M%SZ')
            
            # Clean description (remove newlines, escape special chars)
            description = event.description.replace('\n', '\\n').replace(',', '\\,')
            
            ics_lines.extend([
                "BEGIN:VEVENT",
                f"UID:voyage-event-{i}@voyage.in",
                f"DTSTAMP:{created}",
                f"DTSTART:{start_utc}",
                f"DTEND:{end_utc}",
                f"SUMMARY:{event.title}",
                f"DESCRIPTION:{description}",
                f"LOCATION:{event.location}",
                "STATUS:CONFIRMED",
                "SEQUENCE:0",
                "END:VEVENT",
            ])
        
        ics_lines.append("END:VCALENDAR")
        
        return '\n'.join(ics_lines)


# Global service instance
_calendar_export_service = None

def get_calendar_export_service(firestore_db):
    """Get or create the global calendar export service instance"""
    global _calendar_export_service
    if _calendar_export_service is None:
        _calendar_export_service = GoogleCalendarExportService(firestore_db)
    return _calendar_export_service
