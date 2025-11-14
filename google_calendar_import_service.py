"""
Google Calendar Import & Smart Scheduling Service for Voyage Travel Planner
Reads user's Google Calendar to find free weekends and avoid scheduling conflicts
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
import requests
from schemas import UserCalendarEvent, FreeTimeSlot


class GoogleCalendarImportService:
    """
    Service to read user's Google Calendar and perform smart scheduling.
    Uses Google Calendar API with OAuth to access private calendars.
    """
    
    GOOGLE_CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
    
    def __init__(self):
        """Initialize the service"""
        pass
    
    def fetch_user_calendar_events(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
        calendar_id: str = "primary"
    ) -> List[UserCalendarEvent]:
        """
        Fetch events from user's Google Calendar using OAuth access token.
        
        Args:
            access_token: Google OAuth access token
            start_date: Start date for fetching events
            end_date: End date for fetching events
            calendar_id: Calendar ID (default: 'primary')
        
        Returns:
            List of UserCalendarEvent objects
        """
        events = []
        
        try:
            # Format dates for Google Calendar API
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            # Call Google Calendar API
            url = f"{self.GOOGLE_CALENDAR_API_BASE}/calendars/{calendar_id}/events"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            params = {
                'timeMin': time_min,
                'timeMax': time_max,
                'singleEvents': True,
                'orderBy': 'startTime',
                'maxResults': 250
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('items', []):
                    event = self._parse_calendar_event(item)
                    if event:
                        events.append(event)
            else:
                error_msg = f"Google Calendar API error: {response.status_code}"
                if response.status_code == 401:
                    error_msg = "Invalid or expired access token. Please re-authenticate."
                elif response.status_code == 403:
                    error_msg = "Calendar access forbidden. Please grant calendar permissions."
                raise Exception(error_msg)
        
        except Exception as e:
            print(f"❌ Error fetching calendar events: {str(e)}")
            raise
        
        return events
    
    def _parse_calendar_event(self, item: Dict) -> Optional[UserCalendarEvent]:
        """Parse Google Calendar event into UserCalendarEvent"""
        try:
            event_id = item.get('id', '')
            title = item.get('summary', 'No Title')
            description = item.get('description')
            location = item.get('location')
            
            # Parse start/end times
            start = item.get('start', {})
            end = item.get('end', {})
            
            # Check if all-day event
            is_all_day = 'date' in start
            
            if is_all_day:
                # All-day event (only date, no time)
                start_time = datetime.fromisoformat(start['date']).replace(tzinfo=timezone.utc)
                end_time = datetime.fromisoformat(end['date']).replace(tzinfo=timezone.utc)
            else:
                # Timed event
                start_time_str = start.get('dateTime', '')
                end_time_str = end.get('dateTime', '')
                
                # Parse with timezone info
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            
            # Check if recurring
            is_recurring = 'recurrence' in item or 'recurringEventId' in item
            
            # Get attendees
            attendees = []
            for attendee in item.get('attendees', []):
                email = attendee.get('email')
                if email:
                    attendees.append(email)
            
            return UserCalendarEvent(
                event_id=event_id,
                title=title,
                description=description,
                location=location,
                start_time=start_time,
                end_time=end_time,
                is_all_day=is_all_day,
                is_recurring=is_recurring,
                attendees=attendees if attendees else None
            )
        
        except Exception as e:
            print(f"Error parsing event: {str(e)}")
            return None
    
    def find_free_weekends(
        self,
        access_token: str,
        trip_duration_days: int = 2,
        months_ahead: int = 3,
        include_long_weekends: bool = True,
        working_hours_only: bool = False
    ) -> Tuple[List[Dict], List[str]]:
        """
        Find free weekends in user's calendar.
        
        Args:
            access_token: Google OAuth access token
            trip_duration_days: How many consecutive free days needed
            months_ahead: How many months to look ahead
            include_long_weekends: Include 3-4 day weekends
            working_hours_only: Only check working hours (9 AM - 6 PM)
        
        Returns:
            Tuple of (free_weekends list, recommendations list)
        """
        # Define date range
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=30 * months_ahead)
        
        # Fetch calendar events
        events = self.fetch_user_calendar_events(access_token, start_date, end_date)
        
        # Find free slots
        free_weekends = self._find_free_weekend_slots(
            events,
            start_date,
            end_date,
            trip_duration_days,
            include_long_weekends,
            working_hours_only
        )
        
        # Generate AI recommendations
        recommendations = self._generate_recommendations(free_weekends, trip_duration_days)
        
        return free_weekends, recommendations
    
    def _find_free_weekend_slots(
        self,
        events: List[UserCalendarEvent],
        start_date: datetime,
        end_date: datetime,
        trip_duration_days: int,
        include_long_weekends: bool,
        working_hours_only: bool
    ) -> List[Dict]:
        """Find free weekend slots from calendar events"""
        free_weekends = []
        
        # Iterate through dates
        current_date = start_date
        
        while current_date < end_date:
            # Check if this is a Friday (for weekend checks)
            if current_date.weekday() == 4:  # Friday
                # Check standard weekend (Sat-Sun)
                weekend_dates = [
                    current_date + timedelta(days=1),  # Saturday
                    current_date + timedelta(days=2)   # Sunday
                ]
                
                # Check for long weekends if enabled
                if include_long_weekends:
                    # Check if Friday is free (3-day weekend)
                    if trip_duration_days >= 3:
                        weekend_dates.insert(0, current_date)  # Friday
                    
                    # Check if Monday is free (3-4 day weekend)
                    if trip_duration_days >= 3:
                        weekend_dates.append(current_date + timedelta(days=3))  # Monday
                
                # Check if enough consecutive days are free
                if self._are_dates_free(weekend_dates[:trip_duration_days], events, working_hours_only):
                    weekend_slot = {
                        "start_date": weekend_dates[0].strftime('%Y-%m-%d'),
                        "end_date": weekend_dates[trip_duration_days - 1].strftime('%Y-%m-%d'),
                        "duration_days": trip_duration_days,
                        "dates": [d.strftime('%Y-%m-%d') for d in weekend_dates[:trip_duration_days]],
                        "is_long_weekend": trip_duration_days > 2,
                        "day_names": [d.strftime('%A') for d in weekend_dates[:trip_duration_days]],
                        "conflicts": 0,
                        "score": self._calculate_weekend_score(weekend_dates[:trip_duration_days], events)
                    }
                    free_weekends.append(weekend_slot)
            
            current_date += timedelta(days=1)
        
        # Sort by score (best first)
        free_weekends.sort(key=lambda x: x['score'], reverse=True)
        
        return free_weekends
    
    def _are_dates_free(
        self,
        dates: List[datetime],
        events: List[UserCalendarEvent],
        working_hours_only: bool
    ) -> bool:
        """Check if given dates are free of events"""
        for date in dates:
            # Ensure date has timezone info
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            
            day_start = date.replace(hour=0, minute=0, second=0)
            day_end = date.replace(hour=23, minute=59, second=59)
            
            if working_hours_only:
                # Only check working hours (9 AM - 6 PM)
                day_start = date.replace(hour=9, minute=0)
                day_end = date.replace(hour=18, minute=0)
            
            # Check for conflicts
            for event in events:
                # Skip declined events
                if event.is_all_day:
                    event_start = event.start_time.replace(hour=0, minute=0)
                    event_end = event.end_time.replace(hour=23, minute=59)
                else:
                    event_start = event.start_time
                    event_end = event.end_time
                
                # Check for overlap
                if self._events_overlap(day_start, day_end, event_start, event_end):
                    # If event is during the day, consider it a conflict
                    return False
        
        return True
    
    def _events_overlap(
        self,
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime
    ) -> bool:
        """Check if two time ranges overlap"""
        return start1 < end2 and end1 > start2
    
    def _calculate_weekend_score(
        self,
        dates: List[datetime],
        events: List[UserCalendarEvent]
    ) -> float:
        """Calculate score for a weekend (0-100)"""
        score = 100.0
        
        # Penalize for proximity (sooner is better)
        now = datetime.now(timezone.utc)
        days_from_now = (dates[0] - now).days
        if days_from_now < 14:
            score += 20  # Bonus for near-term availability
        elif days_from_now > 60:
            score -= 10  # Small penalty for far future
        
        # Bonus for longer weekends
        if len(dates) > 2:
            score += 15  # Long weekend bonus
        
        # Check for partial conflicts (events before/after weekend)
        for date in dates:
            day_before = date - timedelta(days=1)
            day_after = date + timedelta(days=1)
            
            # Bonus if days before/after are also free
            if self._are_dates_free([day_before], events, False):
                score += 5
            if self._are_dates_free([day_after], events, False):
                score += 5
        
        return min(score, 100.0)
    
    def _generate_recommendations(
        self,
        free_weekends: List[Dict],
        trip_duration_days: int
    ) -> List[str]:
        """Generate AI recommendations for when to travel"""
        recommendations = []
        
        if not free_weekends:
            recommendations.append("❌ No completely free weekends found. Consider:")
            recommendations.append("   • Taking time off from work")
            recommendations.append("   • Shorter day trips instead")
            recommendations.append("   • Rescheduling some meetings")
            return recommendations
        
        # Best weekend
        best = free_weekends[0]
        best_date = datetime.strptime(best['start_date'], '%Y-%m-%d')
        recommendations.append(
            f"🌟 Best option: {best_date.strftime('%B %d, %Y')} "
            f"({', '.join(best['day_names'])})"
        )
        
        # Near-term options
        near_term = [w for w in free_weekends if 
                    (datetime.strptime(w['start_date'], '%Y-%m-%d') - datetime.now()).days < 30]
        if near_term and len(near_term) > 1:
            recommendations.append(
                f"📅 {len(near_term)} free weekends in the next month"
            )
        
        # Long weekends
        long_weekends = [w for w in free_weekends if w['is_long_weekend']]
        if long_weekends:
            recommendations.append(
                f"🎉 {len(long_weekends)} long weekends available (3+ days)"
            )
        
        # Specific suggestions
        if len(free_weekends) >= 3:
            recommendations.append("💡 Tip: Book soon! You have several options available.")
        else:
            recommendations.append("⚠️  Limited free weekends. Consider booking early.")
        
        return recommendations
    
    def smart_schedule_trip(
        self,
        access_token: str,
        trip_start_date: datetime,
        trip_duration_days: int,
        avoid_work_hours: bool = True,
        buffer_hours: int = 2
    ) -> Tuple[datetime, List[Dict], List[str]]:
        """
        Analyze calendar and suggest best trip start date, considering conflicts.
        
        Args:
            access_token: Google OAuth access token
            trip_start_date: Proposed trip start date
            trip_duration_days: Trip duration in days
            avoid_work_hours: Avoid scheduling during work hours
            buffer_hours: Buffer hours before/after meetings
        
        Returns:
            Tuple of (suggested_start_date, conflicts, warnings)
        """
        # Fetch events for trip duration
        trip_end_date = trip_start_date + timedelta(days=trip_duration_days)
        buffer_start = trip_start_date - timedelta(days=7)  # Check week before
        buffer_end = trip_end_date + timedelta(days=7)  # Check week after
        
        events = self.fetch_user_calendar_events(access_token, buffer_start, buffer_end)
        
        # Check for conflicts during trip
        conflicts = self._find_trip_conflicts(
            events,
            trip_start_date,
            trip_end_date,
            avoid_work_hours
        )
        
        # Generate warnings
        warnings = self._generate_conflict_warnings(
            conflicts,
            trip_start_date,
            trip_duration_days
        )
        
        # Suggest alternative date if conflicts exist
        suggested_date = trip_start_date
        if conflicts:
            suggested_date = self._suggest_alternative_date(
                events,
                trip_start_date,
                trip_duration_days,
                buffer_hours
            )
        
        return suggested_date, conflicts, warnings
    
    def _find_trip_conflicts(
        self,
        events: List[UserCalendarEvent],
        trip_start: datetime,
        trip_end: datetime,
        avoid_work_hours: bool
    ) -> List[Dict]:
        """Find calendar conflicts during trip dates"""
        conflicts = []
        
        for event in events:
            # Check if event overlaps with trip
            if self._events_overlap(trip_start, trip_end, event.start_time, event.end_time):
                # Determine conflict severity
                severity = self._assess_conflict_severity(event, avoid_work_hours)
                
                conflict = {
                    "event_title": event.title,
                    "event_start": event.start_time.isoformat(),
                    "event_end": event.end_time.isoformat(),
                    "severity": severity,  # "high", "medium", "low"
                    "is_all_day": event.is_all_day,
                    "is_work_hours": self._is_work_hours(event.start_time),
                    "attendee_count": len(event.attendees) if event.attendees else 0,
                    "description": event.description[:100] if event.description else None
                }
                conflicts.append(conflict)
        
        # Sort by severity (high first)
        conflicts.sort(key=lambda x: {"high": 3, "medium": 2, "low": 1}.get(x["severity"], 0), reverse=True)
        
        return conflicts
    
    def _assess_conflict_severity(
        self,
        event: UserCalendarEvent,
        avoid_work_hours: bool
    ) -> str:
        """Assess how severe a calendar conflict is"""
        # High severity: All-day events, events with many attendees
        if event.is_all_day:
            return "high"
        
        if event.attendees and len(event.attendees) > 5:
            return "high"
        
        # Check for keywords indicating important meetings
        important_keywords = ['interview', 'presentation', 'meeting', 'conference', 'deadline']
        if any(keyword in event.title.lower() for keyword in important_keywords):
            return "high"
        
        # Medium severity: Work hours events
        if avoid_work_hours and self._is_work_hours(event.start_time):
            return "medium"
        
        # Low severity: Personal events, short events
        return "low"
    
    def _is_work_hours(self, dt: datetime) -> bool:
        """Check if datetime is during work hours (9 AM - 6 PM, Mon-Fri)"""
        if dt.weekday() >= 5:  # Weekend
            return False
        return 9 <= dt.hour < 18
    
    def _generate_conflict_warnings(
        self,
        conflicts: List[Dict],
        trip_start: datetime,
        trip_duration_days: int
    ) -> List[str]:
        """Generate human-readable warnings about conflicts"""
        warnings = []
        
        if not conflicts:
            warnings.append("✅ No calendar conflicts found! You're free to travel.")
            return warnings
        
        # Count by severity
        high_conflicts = [c for c in conflicts if c['severity'] == 'high']
        medium_conflicts = [c for c in conflicts if c['severity'] == 'medium']
        low_conflicts = [c for c in conflicts if c['severity'] == 'low']
        
        if high_conflicts:
            warnings.append(
                f"⚠️  {len(high_conflicts)} important event(s) during your trip:"
            )
            for conflict in high_conflicts[:3]:  # Show top 3
                date_str = datetime.fromisoformat(conflict['event_start']).strftime('%B %d')
                warnings.append(f"   • {date_str}: {conflict['event_title']}")
        
        if medium_conflicts:
            warnings.append(
                f"📅 {len(medium_conflicts)} work event(s) during trip (consider rescheduling)"
            )
        
        if low_conflicts:
            warnings.append(
                f"ℹ️  {len(low_conflicts)} minor event(s) (likely won't be an issue)"
            )
        
        # Suggestion
        if high_conflicts:
            warnings.append("💡 Recommendation: Reschedule these important events or choose different dates")
        
        return warnings
    
    def _suggest_alternative_date(
        self,
        events: List[UserCalendarEvent],
        original_date: datetime,
        trip_duration_days: int,
        buffer_hours: int
    ) -> datetime:
        """Suggest alternative trip start date if conflicts exist"""
        # Try dates around original (±2 weeks)
        search_range = 14
        
        for days_offset in range(-search_range, search_range + 1):
            if days_offset == 0:
                continue
            
            candidate_date = original_date + timedelta(days=days_offset)
            candidate_end = candidate_date + timedelta(days=trip_duration_days)
            
            # Check if this date is conflict-free
            conflicts = self._find_trip_conflicts(events, candidate_date, candidate_end, True)
            
            if not conflicts or all(c['severity'] == 'low' for c in conflicts):
                return candidate_date
        
        # No better date found, return original
        return original_date
    
    def get_busy_free_hours_by_day(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Dict]:
        """
        Get busy/free hours breakdown for each day.
        Useful for planning activities around existing schedule.
        """
        events = self.fetch_user_calendar_events(access_token, start_date, end_date)
        
        daily_schedule = {}
        current_date = start_date
        
        while current_date < end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            
            day_start = current_date.replace(hour=0, minute=0, second=0)
            day_end = current_date.replace(hour=23, minute=59, second=59)
            
            # Find events for this day
            day_events = [
                e for e in events
                if self._events_overlap(day_start, day_end, e.start_time, e.end_time)
            ]
            
            # Calculate busy hours
            busy_slots = []
            for event in day_events:
                if not event.is_all_day:
                    busy_slots.append({
                        "start": event.start_time.strftime('%I:%M %p'),
                        "end": event.end_time.strftime('%I:%M %p'),
                        "title": event.title
                    })
            
            # Calculate free hours
            free_hours = self._calculate_free_hours(day_events, current_date)
            
            daily_schedule[date_key] = {
                "date": current_date.strftime('%A, %B %d, %Y'),
                "is_weekend": current_date.weekday() >= 5,
                "total_events": len(day_events),
                "busy_slots": busy_slots,
                "free_hours": free_hours,
                "is_mostly_free": free_hours > 10,
                "recommendation": self._get_day_recommendation(free_hours, day_events)
            }
            
            current_date += timedelta(days=1)
        
        return daily_schedule
    
    def _calculate_free_hours(
        self,
        day_events: List[UserCalendarEvent],
        date: datetime
    ) -> float:
        """Calculate total free hours in a day"""
        # Working hours: 9 AM to 9 PM (12 hours)
        work_start = date.replace(hour=9, minute=0, second=0)
        work_end = date.replace(hour=21, minute=0, second=0)
        
        total_minutes = (work_end - work_start).total_seconds() / 60
        busy_minutes = 0
        
        for event in day_events:
            if not event.is_all_day:
                event_start = max(event.start_time, work_start)
                event_end = min(event.end_time, work_end)
                
                if event_start < event_end:
                    busy_minutes += (event_end - event_start).total_seconds() / 60
        
        free_minutes = total_minutes - busy_minutes
        return round(free_minutes / 60, 1)
    
    def _get_day_recommendation(
        self,
        free_hours: float,
        day_events: List[UserCalendarEvent]
    ) -> str:
        """Get recommendation for planning activities on this day"""
        if len(day_events) == 0:
            return "Perfect for full-day activities or day trips"
        elif free_hours >= 8:
            return "Good for half-day activities in morning or evening"
        elif free_hours >= 4:
            return "Best for short activities or local experiences"
        else:
            return "Very busy day - rest or light activities recommended"


# Global service instance
_calendar_import_service = None

def get_calendar_import_service():
    """Get or create the global calendar import service instance"""
    global _calendar_import_service
    if _calendar_import_service is None:
        _calendar_import_service = GoogleCalendarImportService()
    return _calendar_import_service
