"""
Pydantic schemas for the Voyage travel planner application.
These schemas define the structure of data flowing through the system.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class TripDetails(BaseModel):
    """
    Schema for extracted trip details from user's natural language prompt.
    This is populated by the Extractor LLM in Step 1 of the orchestrator.
    """
    origin_city: str = Field(
        description="The city where the traveler is starting from. Use 'Not specified' if not mentioned in the prompt."
    )
    destination: str = Field(
        description="The destination city or country the traveler wants to visit. Use 'Not specified' if not mentioned in the prompt."
    )
    num_days: int = Field(
        description="Number of days for the trip. Use 0 if not mentioned. Can infer from 'weekend' (2-3), 'week' (7), etc.",
        ge=0  # Changed from gt=0 to ge=0 to allow 0 (will be validated later)
    )
    num_people: int = Field(
        description="Number of people traveling. Default to 1 if not mentioned. Can infer from 'family' (~4), 'couple' (2), 'solo' (1), etc.",
        ge=0  # Changed from gt=0 to ge=0 to allow 0 (will be validated later)
    )
    budget: float = Field(
        description="Total budget for the trip in Indian Rupees (₹). Use 0 if not mentioned. Can estimate from keywords: 'cheap' (~₹20k-40k), 'budget' (~₹40k-60k), 'comfortable' (~₹60k-80k), 'luxury' (~₹80k+).",
        ge=0  # Changed from gt=0 to ge=0 to allow 0 (will be validated later)
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Trip start date in YYYY-MM-DD format if mentioned (e.g., 'next week', 'December 15', '15th Dec'). Use None if not specified."
    )
    interests: Optional[str] = Field(
        default=None,
        description="Optional: Traveler's interests (e.g., adventure, culture, food)"
    )
    preferred_language: Optional[str] = Field(
        default="English",
        description="Detected language from user's input (English, Hindi, Tamil, Telugu, Bengali, Marathi, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "origin_city": "Delhi",
                "destination": "Kashmir",
                "num_days": 7,
                "num_people": 2,
                "budget": 80000.0,
                "start_date": "2025-12-15",
                "interests": "adventure, culture, food",
                "preferred_language": "English"
            }
        }


class TripRequest(BaseModel):
    """
    Schema for the incoming API request.
    """
    prompt: str = Field(
        description="Natural language travel planning request from the user",
        min_length=1  # Allow short answers for follow-up questions (e.g., "Mumbai", "Delhi")
    )
    previous_extraction: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Previously extracted trip details from incomplete request (for conversation continuity)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "I want to plan a 7-day trip to Paris for 2 people with a budget of $3000",
                "previous_extraction": None
            }
        }


class TripResponse(BaseModel):
    """
    Schema for the API response containing the planned itinerary.
    """
    success: bool
    message: str
    trip_plan: Optional[str] = None
    trip_id: Optional[str] = None  # Firestore document ID
    extracted_details: Optional[dict] = None
    research_data: Optional[dict] = None


class DestinationComparisonRequest(BaseModel):
    """
    Schema for requesting a comparison between two destinations.
    """
    destination_a: str = Field(
        description="First destination to compare",
        min_length=2
    )
    destination_b: str = Field(
        description="Second destination to compare",
        min_length=2
    )
    trip_context: Optional[str] = Field(
        default=None,
        description="Context for the trip (e.g., 'family trip', 'honeymoon', 'adventure travel', 'budget backpacking')"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "destination_a": "Coorg",
                "destination_b": "Ooty",
                "trip_context": "family trip with kids"
            }
        }


class DestinationComparisonResponse(BaseModel):
    """
    Schema for the comparison response.
    """
    success: bool
    message: str
    comparison_analysis: Optional[str] = None


class OptimizeDayRequest(BaseModel):
    """
    Schema for Dynamic Itinerary Optimizer - "Optimize My Day" feature.
    User's plan is disrupted, need to generate a new plan for rest of the day.
    """
    trip_id: str = Field(description="ID of the active trip")
    current_latitude: float = Field(description="User's current GPS latitude", ge=-90, le=90)
    current_longitude: float = Field(description="User's current GPS longitude", ge=-180, le=180)
    current_location_name: Optional[str] = Field(default=None, description="Human-readable location name if available")
    disruption_reason: Optional[str] = Field(default=None, description="Optional: Why the plan changed (e.g., 'attraction closed', 'weather', 'running late')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trip_id": "abc123",
                "current_latitude": 13.0827,
                "current_longitude": 80.2707,
                "current_location_name": "Marina Beach, Chennai",
                "disruption_reason": "Attraction closed unexpectedly"
            }
        }


class OptimizeDayResponse(BaseModel):
    """
    Schema for the optimized day plan response.
    """
    success: bool
    message: str
    optimized_plan: Optional[str] = None
    context_used: Optional[dict] = None  # Shows what data was used (time, location, budget, etc.)


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class UpcomingTrip(BaseModel):
    """
    Schema for an upcoming trip on the dashboard
    """
    id: str
    destination: str
    origin_city: str
    start_date: Optional[str] = None  # Future enhancement for date tracking
    num_days: int
    num_people: int
    budget: float
    countdown_days: Optional[int] = None  # Days until trip (if date available)
    quick_preview: Optional[str] = None  # Short preview of the itinerary


class TripSummary(BaseModel):
    """
    Schema for past trip summary
    """
    id: str
    destination: str
    num_days: int
    created_at: Optional[datetime] = None
    thumbnail_note: Optional[str] = None  # Short note about the trip


class PersonalizedSuggestion(BaseModel):
    """
    Schema for AI-generated personalized 'For You' travel suggestions
    """
    title: str  # Personal, compelling title using "you/your"
    description: str  # 2-3 sentences about the destination
    destination: str  # Destination name
    reason: str  # Specific personalization explaining why it's perfect for them
    estimated_budget: Optional[str] = None  # Budget range
    best_time: Optional[str] = None  # When to visit with current relevance
    category: Optional[str] = None  # "perfect_match" | "trending_now" | "hidden_gem" | "wishlist_inspiration"
    urgency: Optional[str] = None  # Time-sensitive info like "Festival Dec 15-20"
    image_url: Optional[str] = None  # Unsplash image URL for the destination


class DashboardStats(BaseModel):
    """
    Schema for user travel statistics
    """
    total_trips_planned: int
    total_destinations: int
    saved_destinations: int
    total_budget_spent: Optional[float] = None


class UserDashboardResponse(BaseModel):
    """
    Comprehensive dashboard response with all user data
    """
    success: bool
    message: str
    user_info: Optional[dict] = None  # Email, display name
    upcoming_trip: Optional[UpcomingTrip] = None  # Most recent/next trip
    past_trips: list[TripSummary] = []
    saved_destinations: list[dict] = []
    personalized_suggestions: list[PersonalizedSuggestion] = []
    stats: Optional[DashboardStats] = None
    quick_actions: list[dict] = []  # Quick action buttons for the UI


# ============================================================================
# TRENDING SUGGESTIONS SCHEMAS (Public, Cached)
# ============================================================================

class TrendingDestination(BaseModel):
    """
    Schema for a trending destination (public, cached)
    """
    destination: str
    title: str  # Catchy title
    description: str  # Why it's trending
    trending_reason: str  # What makes it hot right now
    estimated_budget: str  # Budget range
    best_time: str  # When to visit
    image_url: Optional[str] = None  # Placeholder for future image integration
    trending_score: Optional[int] = None  # 1-100 popularity score
    tags: list[str] = []  # e.g., ["beach", "winter", "festival"]


class UpcomingEvent(BaseModel):
    """
    Schema for upcoming events/festivals
    """
    event_name: str
    destination: str
    description: str  # What happens at this event
    date_range: str  # e.g., "December 15-20, 2025"
    event_type: str  # "festival" | "season" | "special_event"
    why_attend: str  # Key highlights
    estimated_budget: str  # Budget to attend
    booking_urgency: Optional[str] = None  # "Book by Dec 1" or None
    tags: list[str] = []
    image_url: Optional[str] = None  # Unsplash image URL for the event


class TrendingSuggestionsResponse(BaseModel):
    """
    Response for trending destinations and events (public endpoint)
    """
    success: bool
    message: str
    trending_destinations: list[TrendingDestination] = []
    upcoming_events: list[UpcomingEvent] = []
    cache_timestamp: Optional[datetime] = None  # When cache was last updated
    valid_until: Optional[datetime] = None  # Cache expiry time


# ============================================================================
# FIREBASE AUTH SCHEMAS
# ============================================================================

class TravelPreferences(BaseModel):
    """
    Detailed travel preferences for personalization
    """
    # Budget Preferences
    budget_tier: Optional[str] = Field(
        default=None,
        description="Preferred budget tier: budget-friendly, moderate, luxury"
    )
    typical_budget_range: Optional[str] = Field(
        default=None,
        description="e.g., '₹30,000 - ₹50,000 per trip'"
    )
    
    # Travel Style
    travel_style: Optional[list[str]] = Field(
        default=None,
        description="e.g., ['adventure', 'relaxation', 'cultural', 'luxury', 'backpacking']"
    )
    pace: Optional[str] = Field(
        default=None,
        description="slow (relaxed), moderate, fast (packed itinerary)"
    )
    
    # Interests & Activities
    interests: Optional[list[str]] = Field(
        default=None,
        description="e.g., ['history', 'food', 'photography', 'trekking', 'wildlife']"
    )
    must_have_activities: Optional[list[str]] = Field(
        default=None,
        description="Activities they always want: e.g., ['local food tours', 'sunrise views']"
    )
    
    # Accommodation Preferences
    accommodation_type: Optional[list[str]] = Field(
        default=None,
        description="e.g., ['hotels', 'homestays', 'hostels', 'resorts', 'camps']"
    )
    
    # Food Preferences
    food_preferences: Optional[dict] = Field(
        default=None,
        description="e.g., {'dietary': 'vegetarian', 'priorities': ['street food', 'local cuisine']}"
    )
    
    # Transport Preferences
    transport_modes: Optional[list[str]] = Field(
        default=None,
        description="e.g., ['flights', 'trains', 'buses', 'self-drive']"
    )
    
    # Destination Types
    preferred_destinations: Optional[list[str]] = Field(
        default=None,
        description="e.g., ['mountains', 'beaches', 'cities', 'countryside', 'deserts']"
    )
    avoided_destinations: Optional[list[str]] = Field(
        default=None,
        description="Places to avoid or already visited too much"
    )
    
    # Social Preferences
    typical_group_size: Optional[int] = Field(
        default=None,
        description="Usual number of travelers"
    )
    travel_companions: Optional[str] = Field(
        default=None,
        description="e.g., 'solo', 'partner', 'family', 'friends'"
    )
    
    # Timing Preferences
    preferred_seasons: Optional[list[str]] = Field(
        default=None,
        description="e.g., ['winter', 'monsoon', 'summer']"
    )
    typical_trip_duration: Optional[str] = Field(
        default=None,
        description="e.g., 'weekend (2-3 days)', 'week (5-7 days)', 'extended (10+ days)'"
    )
    
    # Special Requirements
    accessibility_needs: Optional[str] = None
    other_requirements: Optional[str] = None


class LearnedPreferences(BaseModel):
    """
    AI-learned preferences from user behavior (auto-generated)
    """
    most_visited_destinations: Optional[list[str]] = None
    favorite_budget_range: Optional[str] = None
    average_trip_duration: Optional[int] = None
    preferred_travel_months: Optional[list[str]] = None
    recurring_interests: Optional[list[str]] = None
    spending_pattern: Optional[str] = None  # "conservative", "moderate", "generous"
    last_analyzed: Optional[datetime] = None


class UserProfile(BaseModel):
    """
    Comprehensive user profile with preferences
    """
    email: EmailStr
    display_name: Optional[str] = None
    
    # User-defined preferences
    preferences: Optional[TravelPreferences] = None
    
    # AI-learned preferences (auto-updated)
    learned_preferences: Optional[LearnedPreferences] = None
    
    # Profile metadata
    profile_completeness: Optional[int] = Field(
        default=0,
        description="Percentage of profile filled (0-100)"
    )
    onboarding_completed: Optional[bool] = Field(
        default=False,
        description="Whether user completed preference questionnaire"
    )


class UpdatePreferencesRequest(BaseModel):
    """
    Request to update user travel preferences
    """
    preferences: TravelPreferences


class PreferenceQuestionnaireResponse(BaseModel):
    """
    Response for preference questionnaire
    """
    budget_tier: str = Field(description="budget-friendly, moderate, or luxury")
    travel_style: list[str] = Field(description="List of travel styles")
    interests: list[str] = Field(description="List of interests")
    accommodation_type: list[str] = Field(description="Preferred accommodation types")
    food_preferences: dict = Field(description="Dietary and food priorities")
    preferred_destinations: list[str] = Field(description="Types of destinations")
    travel_companions: str = Field(description="Who they travel with")
    typical_trip_duration: str = Field(description="Usual trip length")


class SavedTripPlan(BaseModel):
    """
    Schema for a saved trip plan from Firestore
    """
    id: str
    user_id: str
    title: str
    origin_city: str
    destination: str
    num_days: int
    num_people: int
    budget: float
    interests: Optional[str] = None
    itinerary: str
    is_budget_sufficient: bool = True
    estimated_cost: Optional[float] = None
    trip_status: Optional[str] = "planned"  # "planned", "started", "completed"
    started_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class SaveDestinationRequest(BaseModel):
    """
    Schema for saving a destination to favorites
    """
    destination_name: str = Field(min_length=2)
    notes: Optional[str] = None


# ============================================================================
# VOYAGE VERIFIED REVIEWS & TASTE GRAPH SCHEMAS
# ============================================================================

class ReviewRating(BaseModel):
    """
    Detailed rating breakdown for a trip review
    """
    overall: int = Field(ge=1, le=5, description="Overall trip rating (1-5 stars)")
    itinerary_accuracy: int = Field(ge=1, le=5, description="How accurate was the itinerary?")
    budget_accuracy: int = Field(ge=1, le=5, description="How accurate was the budget estimate?")
    recommendations_quality: int = Field(ge=1, le=5, description="Quality of recommendations")
    destinations: int = Field(ge=1, le=5, description="Rating for destinations visited")
    accommodations: int = Field(ge=1, le=5, description="Rating for accommodations")
    food: int = Field(ge=1, le=5, description="Rating for food experiences")
    activities: int = Field(ge=1, le=5, description="Rating for activities")


class ReviewHighlight(BaseModel):
    """
    A specific highlight or low-light from the trip
    """
    type: str = Field(description="highlight or lowlight")
    category: str = Field(description="destination, food, activity, accommodation, transport, people, etc.")
    item_name: str = Field(description="Name of the place/activity/experience")
    description: str = Field(description="User's description")
    rating: int = Field(ge=1, le=5, description="Individual rating for this item")
    location: Optional[str] = Field(default=None, description="Specific location if applicable")
    would_recommend: bool = Field(description="Would recommend to others?")
    tags: Optional[list[str]] = Field(default=None, description="User-added or auto-generated tags")


class TripReview(BaseModel):
    """
    Comprehensive post-trip review (Voyage Verified)
    """
    # Trip Reference
    trip_id: str = Field(description="ID of the original trip plan")
    
    # Ratings
    ratings: ReviewRating
    
    # Open-ended Feedback
    overall_experience: str = Field(description="Overall trip experience in user's words")
    what_worked_well: str = Field(description="What aspects worked particularly well")
    what_could_improve: str = Field(description="What could have been better")
    
    # Highlights & Lowlights (structured data)
    highlights: list[ReviewHighlight] = Field(description="Top experiences")
    lowlights: Optional[list[ReviewHighlight]] = Field(default=None, description="Disappointing experiences")
    
    # Discovery & Surprises
    unexpected_discoveries: Optional[str] = Field(default=None, description="Unexpected positive discoveries")
    hidden_gems: Optional[list[str]] = Field(default=None, description="Hidden gems found")
    
    # Budget Reality
    actual_spent: Optional[float] = Field(default=None, description="Actual amount spent in ₹")
    budget_breakdown: Optional[dict] = Field(
        default=None,
        description="Actual spending: {accommodation: X, food: Y, activities: Z, transport: W}"
    )
    cost_surprises: Optional[str] = Field(default=None, description="Any cost surprises (higher/lower than expected)")
    
    # Photos & Media
    photo_urls: Optional[list[str]] = Field(default=None, description="URLs to uploaded photos")
    
    # Verification
    verified_visited: bool = Field(default=False, description="Verified through location data/photos")
    
    # Metadata
    travel_dates: Optional[dict] = Field(
        default=None,
        description="Actual travel dates: {start: YYYY-MM-DD, end: YYYY-MM-DD}"
    )
    travel_companions: Optional[str] = Field(default=None, description="solo, couple, family, friends")


class CreateReviewRequest(BaseModel):
    """
    Request to create a new review
    """
    trip_id: str
    ratings: ReviewRating
    overall_experience: str
    what_worked_well: str
    what_could_improve: str
    highlights: list[ReviewHighlight]
    lowlights: Optional[list[ReviewHighlight]] = None
    unexpected_discoveries: Optional[str] = None
    hidden_gems: Optional[list[str]] = None
    actual_spent: Optional[float] = None
    budget_breakdown: Optional[dict] = None
    cost_surprises: Optional[str] = None
    photo_urls: Optional[list[str]] = None
    travel_dates: Optional[dict] = None
    travel_companions: Optional[str] = None


class VoyageVerifiedReview(BaseModel):
    """
    A complete Voyage Verified review with metadata
    """
    id: str
    user_id: str
    trip_id: str
    review: TripReview
    taste_graph_updated: bool = Field(default=False, description="Has this been processed into taste graph")
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_public: bool = Field(default=True, description="Can other users see this review?")
    helpful_count: int = Field(default=0, description="Number of users who found this helpful")


class TasteGraphNode(BaseModel):
    """
    A single node in the user's taste graph
    """
    category: str = Field(description="destination, food, activity, accommodation, etc.")
    item_id: str = Field(description="Unique identifier for the item")
    item_name: str = Field(description="Name of the item")
    
    # Sentiment & Preference
    preference_score: float = Field(ge=0, le=1, description="0-1 score, higher = stronger preference")
    sentiment: str = Field(description="positive, neutral, negative")
    
    # Evidence
    interaction_count: int = Field(default=1, description="Number of interactions/reviews mentioning this")
    average_rating: float = Field(description="Average rating across all interactions")
    
    # Context
    tags: list[str] = Field(description="Associated tags for matching")
    related_items: Optional[list[str]] = Field(default=None, description="IDs of related items often paired")
    
    # Temporal
    last_interaction: datetime
    first_interaction: datetime
    
    # Rich Data
    notes: Optional[str] = Field(default=None, description="Aggregated user feedback about this item")


class TasteGraph(BaseModel):
    """
    User's complete taste graph built from reviews
    """
    user_id: str
    
    # Nodes organized by category
    destinations: list[TasteGraphNode] = Field(default_factory=list)
    foods: list[TasteGraphNode] = Field(default_factory=list)
    activities: list[TasteGraphNode] = Field(default_factory=list)
    accommodations: list[TasteGraphNode] = Field(default_factory=list)
    experiences: list[TasteGraphNode] = Field(default_factory=list)
    
    # High-level insights
    top_preferences: list[str] = Field(default_factory=list, description="Top 10 things user loves")
    avoid_list: list[str] = Field(default_factory=list, description="Things user dislikes")
    
    # Travel Patterns
    preferred_trip_types: list[str] = Field(default_factory=list, description="adventure, relaxation, cultural, etc.")
    budget_patterns: dict = Field(default_factory=dict, description="Spending patterns by category")
    seasonality: dict = Field(default_factory=dict, description="Preferred months/seasons for travel")
    
    # Statistics
    total_reviews: int = Field(default=0)
    total_trips: int = Field(default=0)
    average_rating: float = Field(default=0)
    
    # Metadata
    last_updated: datetime
    confidence_score: float = Field(ge=0, le=1, description="Confidence in taste graph (based on data volume)")


class ReviewSummary(BaseModel):
    """
    Summary of a user's review for display
    """
    id: str
    trip_id: str
    destination: str
    overall_rating: int
    overall_experience: str
    highlights_count: int
    created_at: datetime
    verified_visited: bool


class TasteGraphInsight(BaseModel):
    """
    AI-generated insight from taste graph
    """
    insight_type: str = Field(description="preference, pattern, recommendation, warning")
    category: str
    message: str
    confidence: float = Field(ge=0, le=1)
    supporting_evidence: list[str] = Field(description="Review IDs or data points supporting this")


class ReviewsResponse(BaseModel):
    """
    Response containing user's reviews
    """
    success: bool
    message: str
    reviews: list[ReviewSummary]
    total_reviews: int
    average_overall_rating: float


class TasteGraphResponse(BaseModel):
    """
    Response containing user's taste graph
    """
    success: bool
    message: str
    taste_graph: TasteGraph
    insights: list[TasteGraphInsight]
    recommendations: list[str] = Field(description="Personalized recommendations based on taste graph")


# =============================================================================
# Feature 18: Direct Booking Links
# =============================================================================

class BookingLink(BaseModel):
    """
    A deep link to a booking platform with pre-filled details
    """
    platform: str = Field(description="Booking platform name (e.g., MakeMyTrip, Booking.com, Airbnb)")
    category: str = Field(description="Type of booking (flight, hotel, train, bus, activity)")
    url: str = Field(description="Deep link URL with pre-filled parameters")
    display_text: str = Field(description="User-friendly text to display (e.g., 'Book Flight to Goa')")
    item_name: Optional[str] = Field(default=None, description="Name of the specific item (hotel name, airline, etc.)")
    estimated_price: Optional[float] = Field(default=None, description="Estimated price in INR")
    description: Optional[str] = Field(default=None, description="Additional details about the booking option")
    affiliate_code: Optional[str] = Field(default=None, description="Affiliate tracking code")
    priority: int = Field(default=5, description="Display priority (1=highest, 10=lowest)")


class FlightBookingParams(BaseModel):
    """
    Parameters for flight booking deep links
    """
    origin: str = Field(description="Departure city or airport code")
    destination: str = Field(description="Arrival city or airport code")
    departure_date: str = Field(description="Departure date (YYYY-MM-DD)")
    return_date: Optional[str] = Field(default=None, description="Return date for round trip (YYYY-MM-DD)")
    adults: int = Field(default=1, description="Number of adult passengers")
    children: int = Field(default=0, description="Number of child passengers")
    cabin_class: str = Field(default="economy", description="Cabin class (economy, business, first)")
    preferred_airlines: Optional[list[str]] = Field(default=None, description="Preferred airline codes")


class HotelBookingParams(BaseModel):
    """
    Parameters for hotel booking deep links
    """
    destination: str = Field(description="City or location name")
    checkin_date: str = Field(description="Check-in date (YYYY-MM-DD)")
    checkout_date: str = Field(description="Check-out date (YYYY-MM-DD)")
    adults: int = Field(default=2, description="Number of adults")
    children: int = Field(default=0, description="Number of children")
    rooms: int = Field(default=1, description="Number of rooms")
    hotel_name: Optional[str] = Field(default=None, description="Specific hotel name")
    hotel_id: Optional[str] = Field(default=None, description="Platform-specific hotel ID")
    min_price: Optional[float] = Field(default=None, description="Minimum price filter")
    max_price: Optional[float] = Field(default=None, description="Maximum price filter")
    star_rating: Optional[int] = Field(default=None, description="Minimum star rating (1-5)")
    amenities: Optional[list[str]] = Field(default=None, description="Required amenities (wifi, pool, etc.)")


class TrainBookingParams(BaseModel):
    """
    Parameters for train booking deep links
    """
    origin: str = Field(description="Departure station name or code")
    destination: str = Field(description="Arrival station name or code")
    journey_date: str = Field(description="Journey date (YYYY-MM-DD)")
    quota: str = Field(default="GN", description="Quota code (GN=General, TQ=Tatkal, etc.)")
    class_type: str = Field(default="3A", description="Class (SL, 3A, 2A, 1A, CC, etc.)")
    passengers: int = Field(default=1, description="Number of passengers")


class ActivityBookingParams(BaseModel):
    """
    Parameters for activity/experience booking deep links
    """
    destination: str = Field(description="City or location name")
    activity_name: Optional[str] = Field(default=None, description="Specific activity name")
    activity_type: Optional[str] = Field(default=None, description="Type (tour, adventure, cultural, etc.)")
    date: Optional[str] = Field(default=None, description="Activity date (YYYY-MM-DD)")
    participants: int = Field(default=1, description="Number of participants")


class BookingLinksRequest(BaseModel):
    """
    Request to generate booking links for a trip
    """
    trip_id: str = Field(description="Trip plan ID")
    categories: Optional[list[str]] = Field(
        default=None,
        description="Specific categories to generate links for (flight, hotel, train, bus, activity). If None, generate all."
    )
    platforms: Optional[list[str]] = Field(
        default=None,
        description="Specific platforms to generate links for. If None, use default popular platforms."
    )


class BookingLinksResponse(BaseModel):
    """
    Response containing booking deep links for a trip
    """
    success: bool
    message: str
    trip_id: str
    booking_links: dict[str, list[BookingLink]] = Field(
        description="Booking links organized by category (flight, hotel, train, activity, etc.)"
    )
    total_links: int = Field(description="Total number of booking links generated")
    generated_at: datetime = Field(description="Timestamp when links were generated")


# ============================================================================
# Feature 20: Collaborative Planning ("Voyage Board")
# ============================================================================

class VoyageBoardMember(BaseModel):
    """
    A member of a collaborative Voyage Board
    """
    user_id: str = Field(description="User ID (Firebase UID)")
    email: str = Field(description="Member's email")
    name: Optional[str] = Field(default=None, description="Display name")
    role: str = Field(description="Member role: owner, editor, viewer")
    joined_at: datetime = Field(description="When they joined the board")
    avatar_url: Optional[str] = Field(default=None, description="Profile picture URL")
    is_online: bool = Field(default=False, description="Currently viewing the board")
    last_seen: Optional[datetime] = Field(default=None, description="Last activity timestamp")


class VoyageBoardComment(BaseModel):
    """
    A comment on a Voyage Board itinerary
    """
    comment_id: str = Field(description="Unique comment ID")
    user_id: str = Field(description="User who posted the comment")
    user_name: str = Field(description="Display name of commenter")
    user_avatar: Optional[str] = Field(default=None, description="Commenter's avatar")
    content: str = Field(description="Comment text", min_length=1, max_length=1000)
    day_number: Optional[int] = Field(default=None, description="Which day this comment is about (None = general)")
    activity_index: Optional[int] = Field(default=None, description="Which activity in the day (None = day-level)")
    created_at: datetime = Field(description="When comment was posted")
    updated_at: Optional[datetime] = Field(default=None, description="When comment was last edited")
    likes: list[str] = Field(default_factory=list, description="User IDs who liked this comment")
    replies: list[str] = Field(default_factory=list, description="Comment IDs of replies")


class VoyageBoardSuggestion(BaseModel):
    """
    A suggestion for the itinerary (can be voted on)
    """
    suggestion_id: str = Field(description="Unique suggestion ID")
    user_id: str = Field(description="User who made the suggestion")
    user_name: str = Field(description="Display name")
    suggestion_type: str = Field(description="Type: add_activity, remove_activity, change_time, change_order, add_day, change_hotel")
    day_number: Optional[int] = Field(default=None, description="Which day (if applicable)")
    activity_index: Optional[int] = Field(default=None, description="Which activity (if applicable)")
    current_value: Optional[str] = Field(default=None, description="Current itinerary value")
    suggested_value: str = Field(description="Proposed change")
    reason: Optional[str] = Field(default=None, description="Why this change is suggested")
    created_at: datetime = Field(description="When suggested")
    votes: dict[str, str] = Field(default_factory=dict, description="User ID -> vote ('up', 'down', 'neutral')")
    status: str = Field(default="pending", description="Status: pending, accepted, rejected")
    resolved_by: Optional[str] = Field(default=None, description="User ID who resolved it")
    resolved_at: Optional[datetime] = Field(default=None, description="When resolved")


class VoyageBoardPollOption(BaseModel):
    """
    A single option in a poll
    """
    option_id: str = Field(description="Unique option ID")
    option_text: str = Field(description="Option text", min_length=1, max_length=200)
    votes: list[str] = Field(default_factory=list, description="List of user IDs who voted for this option")


class VoyageBoardPoll(BaseModel):
    """
    A poll on a Voyage Board
    """
    poll_id: str = Field(description="Unique poll ID")
    question: str = Field(description="Poll question", min_length=1, max_length=500)
    options: list[VoyageBoardPollOption] = Field(description="Poll options")
    created_by: str = Field(description="User ID of creator")
    created_by_name: str = Field(description="Display name of creator")
    created_at: datetime = Field(description="When poll was created")
    allow_multiple: bool = Field(default=False, description="Allow voting for multiple options")
    is_closed: bool = Field(default=False, description="Whether poll is closed for voting")


class VoyageBoard(BaseModel):
    """
    A collaborative planning board for a trip itinerary
    """
    board_id: str = Field(description="Unique board ID (shareable)")
    trip_id: str = Field(description="Associated trip plan ID")
    owner_id: str = Field(description="User who created the board")
    board_name: str = Field(description="Display name for the board")
    description: Optional[str] = Field(default=None, description="Board description")
    
    # Access control
    share_link: str = Field(description="Unique shareable link")
    is_public: bool = Field(default=False, description="Public vs. private board")
    access_code: Optional[str] = Field(default=None, description="Optional access code for private boards")
    
    # Members
    members: list[VoyageBoardMember] = Field(default_factory=list, description="Board members")
    
    # Collaboration data
    comments: list[VoyageBoardComment] = Field(default_factory=list, description="All comments")
    suggestions: list[VoyageBoardSuggestion] = Field(default_factory=list, description="All suggestions")
    polls: list[VoyageBoardPoll] = Field(default_factory=list, description="All polls")
    
    # Activity tracking
    activity_log: list[dict] = Field(default_factory=list, description="Activity history")
    
    # Settings
    allow_suggestions: bool = Field(default=True, description="Allow members to make suggestions")
    allow_comments: bool = Field(default=True, description="Allow comments")
    require_approval: bool = Field(default=True, description="Owner must approve suggestions")
    
    # Metadata
    created_at: datetime = Field(description="When board was created")
    updated_at: datetime = Field(description="Last activity on board")
    view_count: int = Field(default=0, description="Total views")


class CreateVoyageBoardRequest(BaseModel):
    """
    Request to create a new Voyage Board
    """
    trip_id: str = Field(description="Trip plan to collaborate on")
    board_name: str = Field(description="Name for the board", min_length=3, max_length=100)
    description: Optional[str] = Field(default=None, description="Board description", max_length=500)
    is_public: bool = Field(default=False, description="Make board publicly viewable")
    access_code: Optional[str] = Field(default=None, description="Optional access code (4-6 digits)")
    initial_members: Optional[list[EmailStr]] = Field(default=None, description="Initial members to invite")


class CreateVoyageBoardResponse(BaseModel):
    """
    Response after creating a Voyage Board
    """
    success: bool
    message: str
    board: Optional[VoyageBoard] = None
    share_link: Optional[str] = None


class AddCommentRequest(BaseModel):
    """
    Request to add a comment to a Voyage Board
    """
    board_id: str = Field(description="Board ID")
    content: str = Field(description="Comment text", min_length=1, max_length=1000)
    day_number: Optional[int] = Field(default=None, description="Day number (None = general)")
    activity_index: Optional[int] = Field(default=None, description="Activity index (None = day-level)")
    reply_to: Optional[str] = Field(default=None, description="Comment ID if this is a reply")


class AddSuggestionRequest(BaseModel):
    """
    Request to add a suggestion to a Voyage Board
    """
    suggestion_type: str = Field(description="Type: add_activity, remove_activity, change_time, etc.")
    day_number: Optional[int] = Field(default=None)
    activity_index: Optional[int] = Field(default=None)
    current_value: Optional[str] = Field(default=None, description="Current value")
    suggested_value: str = Field(description="Proposed change")
    reason: Optional[str] = Field(default=None, description="Why this change")


class VoteOnSuggestionRequest(BaseModel):
    """
    Request to vote on a suggestion
    """
    suggestion_id: str = Field(description="Suggestion to vote on")
    vote: str = Field(description="Vote: up, down, or neutral")


class ResolveSuggestionRequest(BaseModel):
    """
    Request to accept/reject a suggestion (owner only)
    """
    board_id: str = Field(description="Board ID")
    suggestion_id: str = Field(description="Suggestion to resolve")
    action: str = Field(description="Action: accept or reject")
    apply_to_itinerary: bool = Field(default=True, description="Apply change to actual trip plan")


class CreatePollRequest(BaseModel):
    """
    Request to create a poll on a Voyage Board
    """
    question: str = Field(description="Poll question", min_length=1, max_length=500)
    options: list[str] = Field(description="List of poll options (2-10 options)", min_length=2, max_length=10)
    allow_multiple: bool = Field(default=False, description="Allow voting for multiple options")


class VoteOnPollRequest(BaseModel):
    """
    Request to vote on a poll
    """
    poll_id: str = Field(description="Poll ID")
    option_id: str = Field(description="Option ID to vote for")


class VoyageBoardResponse(BaseModel):
    """
    Generic response for Voyage Board operations
    """
    success: bool
    message: str
    board: Optional[VoyageBoard] = None


class VoyageBoardActivityUpdate(BaseModel):
    """
    Real-time activity update for WebSocket
    """
    board_id: str
    activity_type: str = Field(description="Type: comment, suggestion, vote, join, leave, edit")
    user_id: str
    user_name: str
    timestamp: datetime
    data: Optional[dict] = Field(default=None, description="Activity-specific data")


# ============================================================================
# GOOGLE CALENDAR EXPORT SCHEMAS (Feature 21)
# ============================================================================

class CalendarEvent(BaseModel):
    """
    Single calendar event for export
    """
    title: str = Field(description="Event title")
    description: str = Field(description="Event description")
    location: str = Field(description="Event location")
    start_time: datetime = Field(description="Event start time")
    end_time: datetime = Field(description="Event end time")
    event_type: str = Field(description="Type: flight, hotel, activity, transport, trip_day")
    day_number: Optional[int] = Field(default=None, description="Day number in itinerary")
    is_all_day: bool = Field(default=False, description="Whether this is an all-day event")


class GoogleCalendarExportRequest(BaseModel):
    """
    Request to export trip to Google Calendar
    """
    trip_id: str = Field(description="Trip ID to export")
    trip_start_date: Optional[datetime] = Field(default=None, description="Trip start date (YYYY-MM-DD)")
    timezone: str = Field(default="Asia/Kolkata", description="User's timezone")
    include_flights: bool = Field(default=True, description="Include flight bookings")
    include_hotels: bool = Field(default=True, description="Include hotel check-ins/outs")
    include_activities: bool = Field(default=True, description="Include activities")
    include_transport: bool = Field(default=True, description="Include transport")


class GoogleCalendarExportResponse(BaseModel):
    """
    Response with Google Calendar export data
    """
    success: bool
    message: str
    calendar_url: str = Field(description="Google Calendar URL to add events")
    ics_file_url: Optional[str] = Field(default=None, description="ICS file download URL")
    events_count: int = Field(description="Number of events exported")
    events: List[CalendarEvent] = Field(description="List of calendar events")


# ============================================================================
# GOOGLE CALENDAR IMPORT & SMART SCHEDULING SCHEMAS (Feature 22)
# ============================================================================

class UserCalendarEvent(BaseModel):
    """
    Event from user's Google Calendar
    """
    event_id: str = Field(description="Event ID from Google Calendar")
    title: str = Field(description="Event title")
    description: Optional[str] = Field(default=None, description="Event description")
    location: Optional[str] = Field(default=None, description="Event location")
    start_time: datetime = Field(description="Event start time")
    end_time: datetime = Field(description="Event end time")
    is_all_day: bool = Field(default=False, description="Is this an all-day event")
    is_recurring: bool = Field(default=False, description="Is this a recurring event")
    attendees: Optional[List[str]] = Field(default=None, description="List of attendee emails")


class FreeTimeSlot(BaseModel):
    """
    A free time slot in user's calendar
    """
    start_time: datetime = Field(description="Slot start time")
    end_time: datetime = Field(description="Slot end time")
    duration_hours: float = Field(description="Duration in hours")
    date: str = Field(description="Date (YYYY-MM-DD)")
    is_weekend: bool = Field(description="Is this a weekend day")
    is_full_day: bool = Field(description="Is this a full free day")


class FindFreeWeekendRequest(BaseModel):
    """
    Request to find free weekends
    """
    calendar_access_token: str = Field(description="Google OAuth access token")
    trip_duration_days: int = Field(description="How many days needed (e.g., 2 for weekend, 3 for long weekend)")
    months_ahead: int = Field(default=3, description="How many months to look ahead")
    include_long_weekends: bool = Field(default=True, description="Include 3-4 day weekends")
    working_hours_only: bool = Field(default=False, description="Only check working hours (9 AM - 6 PM)")


class FindFreeWeekendResponse(BaseModel):
    """
    Response with free weekends
    """
    success: bool
    message: str
    free_weekends: List[Dict] = Field(description="List of free weekend slots")
    recommendations: List[str] = Field(description="AI recommendations for when to travel")
    total_free_weekends: int = Field(description="Total number of free weekends found")


class SmartScheduleRequest(BaseModel):
    """
    Request to schedule trip around existing meetings
    """
    calendar_access_token: str = Field(description="Google OAuth access token")
    trip_id: str = Field(description="Trip ID to schedule")
    preferred_dates: Optional[List[str]] = Field(default=None, description="Preferred dates (YYYY-MM-DD)")
    avoid_work_hours: bool = Field(default=True, description="Avoid scheduling activities during work hours")
    buffer_hours: int = Field(default=2, description="Buffer hours before/after meetings")


class SmartScheduleResponse(BaseModel):
    """
    Response with smart-scheduled trip
    """
    success: bool
    message: str
    suggested_start_date: datetime = Field(description="AI-suggested trip start date")
    conflicts: List[Dict] = Field(description="List of calendar conflicts found")
    adjusted_itinerary: Optional[str] = Field(default=None, description="Itinerary adjusted for calendar")
    warnings: List[str] = Field(description="Warnings about scheduling conflicts")


# ============================================================================
# FEATURE 23: ON-TRIP EXPENSE TRACKER
# Live expense tracking during the trip with budget management
# ============================================================================

class ExpenseCategory(BaseModel):
    """Expense category with budget allocation"""
    name: str = Field(description="Category name (e.g., Food, Transport, Accommodation)")
    budgeted_amount: float = Field(description="Originally budgeted amount for this category")
    spent_amount: float = Field(default=0.0, description="Amount spent so far")
    remaining_amount: float = Field(description="Remaining budget")
    percentage_used: float = Field(description="Percentage of budget used")
    expense_count: int = Field(default=0, description="Number of expenses in this category")


class Expense(BaseModel):
    """Individual expense entry"""
    expense_id: str = Field(description="Unique expense identifier")
    trip_id: str = Field(description="Trip this expense belongs to")
    user_id: str = Field(description="User who logged the expense")
    category: str = Field(description="Expense category (Food, Transport, etc.)")
    amount: float = Field(description="Expense amount in INR")
    currency: str = Field(default="INR", description="Currency code")
    description: str = Field(description="Description of the expense")
    date: datetime = Field(description="Date and time of expense")
    location: Optional[str] = Field(default=None, description="Where expense occurred")
    payment_method: Optional[str] = Field(default=None, description="Payment method (Cash, Card, UPI)")
    receipt_url: Optional[str] = Field(default=None, description="URL to receipt image")
    notes: Optional[str] = Field(default=None, description="Additional notes")
    is_shared: bool = Field(default=False, description="Is this a shared expense?")
    split_with: List[str] = Field(default=[], description="User IDs to split expense with")
    created_at: datetime = Field(description="When expense was logged")


class AddExpenseRequest(BaseModel):
    """Request to add a new expense"""
    category: str = Field(description="Expense category")
    amount: float = Field(description="Expense amount", gt=0)
    description: str = Field(description="Description of expense")
    date: Optional[str] = Field(default=None, description="Expense date (ISO format)")
    split_among: int = Field(default=1, description="Number of people to split expense with")


class UpdateExpenseRequest(BaseModel):
    """Request to update an existing expense"""
    expense_id: str = Field(description="Expense ID to update")
    category: Optional[str] = Field(default=None, description="New category")
    amount: Optional[float] = Field(default=None, description="New amount", gt=0)
    description: Optional[str] = Field(default=None, description="New description")
    date: Optional[datetime] = Field(default=None, description="New date")
    location: Optional[str] = Field(default=None, description="New location")
    payment_method: Optional[str] = Field(default=None, description="New payment method")
    notes: Optional[str] = Field(default=None, description="New notes")


class ExpenseTrackerSummary(BaseModel):
    """Overall expense tracking summary for a trip"""
    trip_id: str = Field(description="Trip ID")
    total_budget: float = Field(description="Total trip budget")
    total_spent: float = Field(description="Total amount spent so far")
    total_remaining: float = Field(description="Total remaining budget")
    percentage_used: float = Field(description="Percentage of budget used")
    daily_average: float = Field(description="Average spending per day")
    projected_total: float = Field(description="Projected total spend at current rate")
    budget_status: str = Field(description="Status: on-track, over-budget, under-budget")
    categories: List[ExpenseCategory] = Field(description="Breakdown by category")
    recent_expenses: List[Expense] = Field(description="Recent expenses")
    total_expenses_count: int = Field(description="Total number of expenses logged")
    days_elapsed: int = Field(description="Days since trip started")
    days_remaining: int = Field(description="Days remaining in trip")
    warnings: List[str] = Field(default=[], description="Budget warnings and alerts")
    recommendations: List[str] = Field(default=[], description="AI spending recommendations")


class BudgetAlert(BaseModel):
    """Budget alert/notification"""
    alert_id: str = Field(description="Alert identifier")
    trip_id: str = Field(description="Trip ID")
    alert_type: str = Field(description="Type: warning, critical, info")
    category: Optional[str] = Field(default=None, description="Category related to alert")
    message: str = Field(description="Alert message")
    threshold: float = Field(description="Budget threshold that triggered alert")
    current_value: float = Field(description="Current value")
    created_at: datetime = Field(description="When alert was created")
    is_read: bool = Field(default=False, description="Has user seen this alert?")


class GetExpenseTrackerRequest(BaseModel):
    """Request to get expense tracker data"""
    trip_id: str = Field(description="Trip ID")
    include_deleted: bool = Field(default=False, description="Include deleted expenses?")


class ExpenseAnalyticsRequest(BaseModel):
    """Request for expense analytics"""
    trip_id: str = Field(description="Trip ID")
    group_by: str = Field(default="category", description="Group by: category, day, location, payment_method")
    start_date: Optional[datetime] = Field(default=None, description="Filter start date")
    end_date: Optional[datetime] = Field(default=None, description="Filter end date")


class ExpenseAnalyticsResponse(BaseModel):
    """Expense analytics data"""
    trip_id: str = Field(description="Trip ID")
    analytics_type: str = Field(description="Type of analytics")
    data: List[Dict] = Field(description="Analytics data grouped as requested")
    insights: List[str] = Field(description="AI-generated insights")
    top_expenses: List[Expense] = Field(description="Top 5 expenses")
    spending_trend: str = Field(description="Spending trend: increasing, decreasing, stable")


class SplitExpenseRequest(BaseModel):
    """Request to split an expense among multiple people"""
    expense_id: str = Field(description="Expense to split")
    split_type: str = Field(default="equal", description="Split type: equal, custom, percentage")
    split_details: List[Dict] = Field(description="Split details per user")


class BudgetAdjustmentRequest(BaseModel):
    """Request to adjust budget during trip"""
    trip_id: str = Field(description="Trip ID")
    category: str = Field(description="Category to adjust")
    new_amount: float = Field(description="New budgeted amount", gt=0)
    reason: str = Field(description="Reason for adjustment")


class ExportExpensesRequest(BaseModel):
    """Request to export expenses"""
    trip_id: str = Field(description="Trip ID")
    format: str = Field(default="csv", description="Export format: csv, pdf, excel")
    include_receipts: bool = Field(default=False, description="Include receipt images?")


# ============================================================================
# USER DASHBOARD SCHEMAS
# ============================================================================

class DashboardStats(BaseModel):
    """Dashboard statistics for quick overview"""
    total_trips: int = Field(description="Total number of trips")
    active_trips: int = Field(description="Number of ongoing trips")
    completed_trips: int = Field(description="Number of completed trips")
    upcoming_trips: int = Field(description="Number of upcoming trips")
    total_expenses_logged: int = Field(description="Total expenses across all trips")
    total_amount_spent: float = Field(description="Total money spent across all trips")
    average_trip_cost: float = Field(description="Average cost per trip")
    budget_adherence_rate: float = Field(description="Percentage of trips within budget")
    most_expensive_category: str = Field(description="Category with highest spending")
    favorite_destination: Optional[str] = Field(default=None, description="Most visited destination")


class TripSummaryCard(BaseModel):
    """Compact trip summary for dashboard list"""
    trip_id: str = Field(description="Trip ID")
    destination: str = Field(description="Trip destination")
    start_date: datetime = Field(description="Trip start date")
    end_date: datetime = Field(description="Trip end date")
    status: str = Field(description="Trip status: upcoming, ongoing, completed")
    total_budget: float = Field(description="Total trip budget")
    total_spent: float = Field(description="Amount spent so far")
    percentage_used: float = Field(description="Percentage of budget used")
    budget_status: str = Field(description="on-track, warning, critical, over-budget")
    days_remaining: int = Field(description="Days remaining in trip")
    expense_count: int = Field(description="Number of expenses logged")
    last_expense_date: Optional[datetime] = Field(default=None, description="When last expense was logged")
    alerts_count: int = Field(default=0, description="Number of unread budget alerts")


class RecentActivity(BaseModel):
    """Recent activity item for dashboard feed"""
    activity_id: str = Field(description="Activity ID")
    activity_type: str = Field(description="Type: expense_added, budget_alert, trip_created, etc.")
    trip_id: str = Field(description="Related trip ID")
    trip_name: str = Field(description="Trip destination name")
    title: str = Field(description="Activity title")
    description: str = Field(description="Activity description")
    amount: Optional[float] = Field(default=None, description="Amount if expense-related")
    category: Optional[str] = Field(default=None, description="Category if expense-related")
    timestamp: datetime = Field(description="When activity occurred")
    icon: str = Field(description="Icon identifier for UI")
    color: str = Field(description="Color for UI badge")


class BudgetInsight(BaseModel):
    """AI-generated budget insight"""
    insight_id: str = Field(description="Insight ID")
    type: str = Field(description="Type: tip, warning, achievement, recommendation")
    title: str = Field(description="Insight title")
    message: str = Field(description="Insight message")
    action: Optional[str] = Field(default=None, description="Suggested action")
    priority: str = Field(description="Priority: high, medium, low")
    trip_id: Optional[str] = Field(default=None, description="Related trip if applicable")
    created_at: datetime = Field(description="When insight was generated")


class UserDashboard(BaseModel):
    """Complete unified dashboard data - combines expense tracking and trip planning"""
    user_id: str = Field(description="User ID")
    
    # Expense Tracking Section
    stats: DashboardStats = Field(description="Overall statistics")
    active_trips: List[TripSummaryCard] = Field(description="Currently active trips")
    upcoming_trips: List[TripSummaryCard] = Field(description="Upcoming trips")
    recent_activity: List[RecentActivity] = Field(description="Recent activity feed")
    budget_insights: List[BudgetInsight] = Field(description="AI-generated insights")
    unread_alerts: int = Field(description="Number of unread budget alerts")
    spending_trend: str = Field(description="Overall spending trend: increasing, stable, decreasing")
    top_categories: List[Dict[str, Any]] = Field(description="Top spending categories")
    
    # Trip Planning Section (from old dashboard)
    user_info: Optional[dict] = Field(default=None, description="User email and display name")
    past_trips: List[TripSummary] = Field(default_factory=list, description="Completed trips summary")
    saved_destinations: List[dict] = Field(default_factory=list, description="User's saved destinations")
    personalized_suggestions: List[PersonalizedSuggestion] = Field(default_factory=list, description="AI-powered trip suggestions")
    quick_actions: List[dict] = Field(default_factory=list, description="Quick action buttons for UI")


# ===========================
# OTP Verification Schemas
# ===========================

class OTPRequest(BaseModel):
    """Request to send OTP to phone number"""
    phone_number: str = Field(description="Phone number in E.164 format (e.g., +919876543210)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+919876543210"
            }
        }


class OTPVerifyRequest(BaseModel):
    """Request to verify OTP code"""
    phone_number: str = Field(description="Phone number in E.164 format")
    otp: str = Field(description="6-digit OTP code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+919876543210",
                "otp": "123456"
            }
        }


class OTPResponse(BaseModel):
    """Response for OTP operations"""
    success: bool = Field(description="Whether operation was successful")
    message: str = Field(description="Result message")
    expires_in: Optional[int] = Field(default=None, description="OTP expiry time in seconds")
    
    last_updated: datetime = Field(description="When dashboard was last updated")


