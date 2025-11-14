"""
Public Event Discovery Engine - Google Calendar Integration
Automatically fetches real events from public Google Calendars for trending suggestions.
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from urllib.parse import quote


class PublicEventDiscoveryEngine:
    """
    Discovers public events from Google Calendar APIs without authentication.
    Focuses on holidays, festivals, cultural events, and sporting events.
    """
    
    # Public calendar IDs (these are publicly accessible)
    PUBLIC_CALENDARS = {
        "indian_holidays": "en.indian#holiday@group.v.calendar.google.com",
        "hindu_holidays": "en.hinduism#holiday@group.v.calendar.google.com",
        "islamic_holidays": "en.islamic#holiday@group.v.calendar.google.com",
        "christian_holidays": "en.christian#holiday@group.v.calendar.google.com",
        # Add more as needed
    }
    
    def __init__(self, google_api_key: str):
        """Initialize with Google API key"""
        self.api_key = google_api_key
        self.base_url = "https://www.googleapis.com/calendar/v3"
        
        # Known Indian festivals and events database
        self.indian_events_db = self._initialize_indian_events_db()
    
    def _initialize_indian_events_db(self) -> List[Dict]:
        """
        Initialize a comprehensive database of Indian festivals and events.
        This serves as a fallback and enhancement to Google Calendar data.
        """
        return [
            # November 2025
            {
                "name": "Diwali (Deepavali)",
                "start_date": "2025-11-01",
                "end_date": "2025-11-01",
                "type": "festival",
                "description": "Festival of Lights - Hindu celebration of good over evil",
                "destinations": ["Varanasi", "Jaipur", "Amritsar", "Ayodhya", "Mumbai"],
                "tags": ["religious", "cultural", "lights", "family"],
                "season": "winter",
                "estimated_budget": "₹30,000 - ₹60,000 for 5 days",
                "why_attend": "Experience millions of diyas, fireworks, traditional sweets, and spiritual ceremonies across India",
                "booking_urgency": "Book NOW - Most popular festival season"
            },
            {
                "name": "Guru Nanak Jayanti",
                "start_date": "2025-11-05",
                "end_date": "2025-11-05",
                "type": "festival",
                "description": "Birth anniversary of Guru Nanak Dev Ji, founder of Sikhism",
                "destinations": ["Amritsar", "Delhi", "Anandpur Sahib"],
                "tags": ["religious", "sikh", "spiritual"],
                "season": "winter",
                "estimated_budget": "₹20,000 - ₹40,000 for 3 days",
                "why_attend": "Witness grand processions, kirtan at Golden Temple, langar seva",
                "booking_urgency": "Book hotels in Amritsar 2 weeks in advance"
            },
            {
                "name": "Pushkar Camel Fair",
                "start_date": "2025-11-05",
                "end_date": "2025-11-12",
                "type": "festival",
                "description": "World's largest camel fair with cultural performances and trading",
                "destinations": ["Pushkar"],
                "tags": ["cultural", "unique", "desert", "photography"],
                "season": "winter",
                "estimated_budget": "₹25,000 - ₹45,000 for 5 days",
                "why_attend": "50,000+ camels, folk dances, mustache competitions, desert camping",
                "booking_urgency": "URGENT - Book camps NOW, very limited availability"
            },
            
            # December 2025
            {
                "name": "Hornbill Festival",
                "start_date": "2025-12-01",
                "end_date": "2025-12-10",
                "type": "festival",
                "description": "Festival of Festivals showcasing Naga tribal culture",
                "destinations": ["Kohima"],
                "tags": ["tribal", "northeast", "cultural", "food", "unique"],
                "season": "winter",
                "estimated_budget": "₹35,000 - ₹55,000 for 7 days",
                "why_attend": "16+ Naga tribes, traditional warrior dances, authentic cuisine, handicrafts",
                "booking_urgency": "Book by November 15 - Very limited accommodations"
            },
            {
                "name": "Rann Utsav",
                "start_date": "2025-11-15",
                "end_date": "2026-02-28",
                "type": "festival",
                "description": "Cultural festival on the white salt desert of Kutch",
                "destinations": ["Kutch"],
                "tags": ["cultural", "desert", "unique", "photography", "camping"],
                "season": "winter",
                "estimated_budget": "₹25,000 - ₹50,000 for 4 days",
                "why_attend": "White desert, full moon nights, folk performances, tent city experience",
                "booking_urgency": "Book tent accommodations in advance"
            },
            {
                "name": "Christmas Celebrations",
                "start_date": "2025-12-24",
                "end_date": "2025-12-25",
                "type": "festival",
                "description": "Christian celebration with midnight mass and festivities",
                "destinations": ["Goa", "Pondicherry", "Mumbai", "Shillong"],
                "tags": ["religious", "christian", "beaches", "party"],
                "season": "winter",
                "estimated_budget": "₹40,000 - ₹70,000 for 5 days",
                "why_attend": "Beach parties in Goa, midnight mass, carols, Portuguese heritage",
                "booking_urgency": "URGENT - Christmas week peak season, book NOW"
            },
            {
                "name": "New Year Celebrations",
                "start_date": "2025-12-31",
                "end_date": "2026-01-01",
                "type": "special_event",
                "description": "New Year's Eve parties and celebrations across India",
                "destinations": ["Goa", "Mumbai", "Delhi", "Bangalore", "Rishikesh"],
                "tags": ["party", "nightlife", "beach", "celebration"],
                "season": "winter",
                "estimated_budget": "₹50,000 - ₹100,000 for 5 days",
                "why_attend": "Beach parties, EDM festivals, yacht parties, temple visits for spiritual new year",
                "booking_urgency": "CRITICAL - Book by mid-November, prices double by December"
            },
            
            # January 2026
            {
                "name": "Pongal",
                "start_date": "2026-01-14",
                "end_date": "2026-01-17",
                "type": "festival",
                "description": "Tamil harvest festival celebrating the Sun God",
                "destinations": ["Chennai", "Madurai", "Thanjavur", "Pondicherry"],
                "tags": ["harvest", "cultural", "south-india", "traditional"],
                "season": "winter",
                "estimated_budget": "₹30,000 - ₹50,000 for 5 days",
                "why_attend": "Traditional kolam art, jallikattu bull taming, authentic Tamil cuisine",
                "booking_urgency": "Book by end of December"
            },
            {
                "name": "Makar Sankranti / Kite Festival",
                "start_date": "2026-01-14",
                "end_date": "2026-01-14",
                "type": "festival",
                "description": "Harvest festival with massive kite flying celebrations",
                "destinations": ["Ahmedabad", "Jaipur", "Delhi", "Varanasi"],
                "tags": ["cultural", "kites", "harvest", "family"],
                "season": "winter",
                "estimated_budget": "₹25,000 - ₹45,000 for 4 days",
                "why_attend": "Sky filled with colorful kites, rooftop parties, traditional sweets",
                "booking_urgency": "Book hotels in Ahmedabad early"
            },
            {
                "name": "Republic Day",
                "start_date": "2026-01-26",
                "end_date": "2026-01-26",
                "type": "festival",
                "description": "National holiday celebrating India's Constitution with grand parade",
                "destinations": ["Delhi"],
                "tags": ["national", "patriotic", "parade", "cultural"],
                "season": "winter",
                "estimated_budget": "₹20,000 - ₹40,000 for 3 days",
                "why_attend": "Grand parade at Rajpath, military display, cultural performances, long weekend",
                "booking_urgency": "Book Delhi hotels 1 month in advance"
            },
            
            # February 2026
            {
                "name": "Holi",
                "start_date": "2026-03-14",
                "end_date": "2026-03-14",
                "type": "festival",
                "description": "Festival of Colors celebrating spring and love",
                "destinations": ["Mathura", "Vrindavan", "Jaipur", "Delhi", "Mumbai"],
                "tags": ["colors", "spring", "party", "cultural"],
                "season": "spring",
                "estimated_budget": "₹30,000 - ₹55,000 for 5 days",
                "why_attend": "Color throwing, bhang, music, traditional celebrations in Krishna's birthplace",
                "booking_urgency": "Book by mid-February"
            },
            
            # Seasonal Events (no fixed dates)
            {
                "name": "Goa Sunburn Festival",
                "start_date": "2025-12-27",
                "end_date": "2025-12-29",
                "type": "special_event",
                "description": "Asia's biggest EDM music festival on Goa beaches",
                "destinations": ["Goa"],
                "tags": ["music", "edm", "party", "beach", "international"],
                "season": "winter",
                "estimated_budget": "₹60,000 - ₹120,000 including tickets",
                "why_attend": "World-class DJs, beach parties, 3-day music marathon",
                "booking_urgency": "CRITICAL - Tickets sell out months in advance"
            },
            {
                "name": "Jaipur Literature Festival",
                "start_date": "2026-01-22",
                "end_date": "2026-01-26",
                "type": "special_event",
                "description": "World's largest free literary festival",
                "destinations": ["Jaipur"],
                "tags": ["literature", "culture", "intellectual", "free"],
                "season": "winter",
                "estimated_budget": "₹25,000 - ₹45,000 for 5 days",
                "why_attend": "Free entry, 500+ speakers, book launches, author interactions",
                "booking_urgency": "Book hotels early - very popular event"
            },
            {
                "name": "Kashmir Tulip Festival",
                "start_date": "2026-03-25",
                "end_date": "2026-04-15",
                "type": "season",
                "description": "Asia's largest tulip garden in bloom",
                "destinations": ["Srinagar"],
                "tags": ["nature", "flowers", "photography", "spring"],
                "season": "spring",
                "estimated_budget": "₹40,000 - ₹70,000 for 5 days",
                "why_attend": "1.5 million tulips in 70+ varieties, stunning Himalayan backdrop",
                "booking_urgency": "Book by February end"
            },
            {
                "name": "Valley of Flowers Blooming",
                "start_date": "2026-07-15",
                "end_date": "2026-09-15",
                "type": "season",
                "description": "UNESCO World Heritage site with 300+ flower species",
                "destinations": ["Uttarakhand"],
                "tags": ["nature", "trek", "flowers", "unesco", "photography"],
                "season": "monsoon",
                "estimated_budget": "₹35,000 - ₹60,000 for 7 days",
                "why_attend": "Rare Himalayan flowers, blue poppies, pristine alpine meadows",
                "booking_urgency": "Book trekking permits 2 months in advance"
            }
        ]
    
    def get_events_for_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Get events from both Google Calendar API and internal database.
        Combines real-time data with curated Indian events.
        """
        events = []
        
        # Get events from internal database
        db_events = self._get_events_from_db(start_date, end_date)
        events.extend(db_events)
        
        # Try to fetch from Google Calendar (optional - may fail without proper setup)
        try:
            calendar_events = self._fetch_google_calendar_events(start_date, end_date)
            events.extend(calendar_events)
        except Exception as e:
            print(f"ℹ️ Google Calendar API not available (using curated database): {str(e)}")
        
        # Remove duplicates and sort by date
        events = self._deduplicate_events(events)
        events.sort(key=lambda x: x.get('start_date', ''))
        
        return events
    
    def _get_events_from_db(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Filter events from internal database by date range"""
        filtered_events = []
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        for event in self.indian_events_db:
            event_start = event.get('start_date', '')
            event_end = event.get('end_date', event_start)
            
            # Check if event falls within date range
            if event_start <= end_str and event_end >= start_str:
                filtered_events.append(event.copy())
        
        return filtered_events
    
    def _fetch_google_calendar_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Fetch events from Google Calendar API (public calendars).
        This requires proper API setup but provides real-time holiday data.
        """
        events = []
        
        # Format dates for Google Calendar API
        time_min = start_date.isoformat() + 'Z'
        time_max = end_date.isoformat() + 'Z'
        
        # Fetch from Indian holidays calendar
        for calendar_name, calendar_id in self.PUBLIC_CALENDARS.items():
            try:
                url = f"{self.base_url}/calendars/{quote(calendar_id)}/events"
                params = {
                    'key': self.api_key,
                    'timeMin': time_min,
                    'timeMax': time_max,
                    'singleEvents': True,
                    'orderBy': 'startTime',
                    'maxResults': 50
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data.get('items', []):
                        event = self._parse_google_event(item, calendar_name)
                        if event:
                            events.append(event)
                else:
                    print(f"⚠️ Calendar API error for {calendar_name}: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ Error fetching {calendar_name}: {str(e)}")
                continue
        
        return events
    
    def _parse_google_event(self, item: Dict, calendar_type: str) -> Optional[Dict]:
        """Parse Google Calendar event into our format"""
        try:
            summary = item.get('summary', '')
            
            # Get start date
            start = item.get('start', {})
            start_date = start.get('date') or start.get('dateTime', '').split('T')[0]
            
            # Get end date
            end = item.get('end', {})
            end_date = end.get('date') or end.get('dateTime', '').split('T')[0]
            
            if not start_date:
                return None
            
            # Determine destination based on event type
            destinations = self._guess_destinations_for_holiday(summary, calendar_type)
            
            return {
                "name": summary,
                "start_date": start_date,
                "end_date": end_date or start_date,
                "type": "festival",
                "description": item.get('description', f'{summary} - Public holiday in India'),
                "destinations": destinations,
                "tags": self._generate_tags_for_holiday(summary, calendar_type),
                "season": self._determine_season(start_date),
                "estimated_budget": "₹20,000 - ₹40,000 for 3-4 days",
                "why_attend": f"Experience {summary} celebrations across India",
                "booking_urgency": None,
                "source": "google_calendar"
            }
        except Exception as e:
            print(f"Error parsing event: {str(e)}")
            return None
    
    def _guess_destinations_for_holiday(self, holiday_name: str, calendar_type: str) -> List[str]:
        """Guess best destinations for a holiday"""
        holiday_lower = holiday_name.lower()
        
        # Diwali
        if 'diwali' in holiday_lower or 'deepavali' in holiday_lower:
            return ["Varanasi", "Jaipur", "Amritsar", "Ayodhya"]
        
        # Holi
        if 'holi' in holiday_lower:
            return ["Mathura", "Vrindavan", "Jaipur", "Delhi"]
        
        # Christmas
        if 'christmas' in holiday_lower:
            return ["Goa", "Pondicherry", "Mumbai", "Shillong"]
        
        # Eid
        if 'eid' in holiday_lower:
            return ["Hyderabad", "Lucknow", "Delhi", "Mumbai"]
        
        # Guru Nanak / Sikh
        if 'guru nanak' in holiday_lower or 'gurpurab' in holiday_lower:
            return ["Amritsar", "Delhi", "Anandpur Sahib"]
        
        # Republic Day / Independence Day
        if 'republic' in holiday_lower or 'independence' in holiday_lower:
            return ["Delhi"]
        
        # Pongal
        if 'pongal' in holiday_lower:
            return ["Chennai", "Madurai", "Thanjavur"]
        
        # Default
        return ["Delhi", "Mumbai", "Bangalore"]
    
    def _generate_tags_for_holiday(self, holiday_name: str, calendar_type: str) -> List[str]:
        """Generate relevant tags for a holiday"""
        tags = ["festival", "cultural"]
        
        if 'hindu' in calendar_type.lower():
            tags.append("hindu")
            tags.append("religious")
        elif 'islamic' in calendar_type.lower():
            tags.append("islamic")
            tags.append("religious")
        elif 'christian' in calendar_type.lower():
            tags.append("christian")
            tags.append("religious")
        elif 'sikh' in calendar_type.lower() or 'guru' in holiday_name.lower():
            tags.append("sikh")
            tags.append("religious")
        
        holiday_lower = holiday_name.lower()
        if any(word in holiday_lower for word in ['diwali', 'lights']):
            tags.extend(["lights", "family"])
        if any(word in holiday_lower for word in ['holi', 'color']):
            tags.extend(["colors", "spring", "party"])
        if any(word in holiday_lower for word in ['christmas', 'new year']):
            tags.extend(["party", "celebration"])
        
        return list(set(tags))  # Remove duplicates
    
    def _determine_season(self, date_str: str) -> str:
        """Determine season from date"""
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            month = date.month
            
            if month in [11, 12, 1, 2]:
                return "winter"
            elif month in [3, 4, 5]:
                return "spring"
            elif month in [6, 7, 8, 9]:
                return "monsoon"
            else:  # 10
                return "autumn"
        except:
            return "winter"
    
    def _deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """Remove duplicate events (prefer curated DB over API)"""
        seen = set()
        unique_events = []
        
        # Sort so DB events come first (they have better details)
        events.sort(key=lambda x: 0 if x.get('source') != 'google_calendar' else 1)
        
        for event in events:
            # Create unique key from name and date
            key = f"{event.get('name', '').lower()}_{event.get('start_date', '')}"
            
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        return unique_events
    
    def get_trending_events(self, months_ahead: int = 3) -> List[Dict]:
        """
        Get trending events for next N months.
        Perfect for the trending suggestions endpoint.
        """
        start_date = datetime.now()
        end_date = start_date + timedelta(days=months_ahead * 30)
        
        events = self.get_events_for_date_range(start_date, end_date)
        
        # Filter and rank by popularity/urgency
        trending = []
        current_date = datetime.now()
        
        for event in events:
            event_start = datetime.strptime(event['start_date'], "%Y-%m-%d")
            days_until = (event_start - current_date).days
            
            # Calculate trending score based on timing
            if days_until < 0:
                continue  # Skip past events
            elif days_until <= 7:
                trending_score = 100  # Happening this week!
            elif days_until <= 14:
                trending_score = 95   # Next 2 weeks
            elif days_until <= 30:
                trending_score = 85   # This month
            elif days_until <= 60:
                trending_score = 70   # Next month
            else:
                trending_score = 60   # Future
            
            event['trending_score'] = trending_score
            event['days_until'] = days_until
            trending.append(event)
        
        # Sort by trending score
        trending.sort(key=lambda x: x['trending_score'], reverse=True)
        
        return trending
    
    def get_seasonal_destinations(self, current_month: int) -> List[Dict]:
        """
        Get destinations that are perfect for the current season.
        Used to generate trending destination suggestions.
        """
        seasonal_data = {
            # November - December (Winter starts)
            11: [
                {
                    "destination": "Goa",
                    "season": "winter",
                    "weather": "Perfect beach weather (25-32°C)",
                    "why_now": "Peak season starts, beach parties, water sports, pleasant weather",
                    "trending_score": 95,
                    "tags": ["beach", "nightlife", "water-sports", "party"]
                },
                {
                    "destination": "Rajasthan",
                    "season": "winter",
                    "weather": "Cool and comfortable (15-30°C)",
                    "why_now": "Perfect for desert exploration, camel safaris, palace visits",
                    "trending_score": 92,
                    "tags": ["heritage", "desert", "palaces", "culture"]
                },
                {
                    "destination": "Kerala",
                    "season": "winter",
                    "weather": "Post-monsoon lush greenery (22-32°C)",
                    "why_now": "Backwaters at their best, Ayurvedic treatments, waterfalls",
                    "trending_score": 88,
                    "tags": ["backwaters", "nature", "ayurveda", "beaches"]
                },
                {
                    "destination": "Varanasi",
                    "season": "winter",
                    "weather": "Cool mornings (12-28°C)",
                    "why_now": "Diwali aftermath, Dev Deepavali, pleasant Ganga ghats",
                    "trending_score": 90,
                    "tags": ["spiritual", "cultural", "religious", "photography"]
                }
            ],
            # December
            12: [
                {
                    "destination": "Kashmir",
                    "season": "winter",
                    "weather": "Snowfall begins (-2 to 10°C)",
                    "why_now": "First snow, Gulmarg skiing, frozen Dal Lake, winter wonderland",
                    "trending_score": 93,
                    "tags": ["snow", "skiing", "mountains", "adventure"]
                },
                {
                    "destination": "Goa",
                    "season": "winter",
                    "weather": "Perfect (25-32°C)",
                    "why_now": "Christmas & New Year peak, Sunburn Festival, beach parties",
                    "trending_score": 98,
                    "tags": ["beach", "party", "nightlife", "christmas"]
                },
                {
                    "destination": "Rann of Kutch",
                    "season": "winter",
                    "weather": "Cool nights (10-25°C)",
                    "why_now": "Rann Utsav in full swing, white desert, full moon magic",
                    "trending_score": 90,
                    "tags": ["desert", "unique", "festival", "photography"]
                }
            ],
            # January
            1: [
                {
                    "destination": "Jaipur",
                    "season": "winter",
                    "weather": "Pleasant days (8-22°C)",
                    "why_now": "Jaipur Literature Festival, kite festival, comfortable sightseeing",
                    "trending_score": 88,
                    "tags": ["heritage", "culture", "literature", "palaces"]
                },
                {
                    "destination": "Andaman",
                    "season": "winter",
                    "weather": "Perfect beach weather (23-30°C)",
                    "why_now": "Peak diving season, crystal clear waters, best visibility",
                    "trending_score": 92,
                    "tags": ["beach", "diving", "islands", "adventure"]
                }
            ],
            # Add more months as needed...
        }
        
        return seasonal_data.get(current_month, seasonal_data[11])  # Default to November


# Global instance
_event_engine = None

def get_event_discovery_engine(google_api_key: str) -> PublicEventDiscoveryEngine:
    """Get or create the global event discovery engine instance"""
    global _event_engine
    if _event_engine is None:
        _event_engine = PublicEventDiscoveryEngine(google_api_key)
    return _event_engine
