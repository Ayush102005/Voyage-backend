"""
Agent Tools for the Voyage Travel Planner.
Contains all research and planning tools used by the orchestrator and the main agent.
"""

from langchain_core.tools import tool
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Tavily client
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


# ============================================================================
# RESEARCH TOOLS (Used by Orchestrator in Step 2)
# ============================================================================

@tool
def get_minimum_daily_budget(city: str) -> str:
    """
    Searches for realistic minimum daily cost of living in a given city.
    Used to determine if the user's budget is sufficient.
    
    Uses Tavily to search + a simple LLM call to parse the numerical value.
    
    Args:
        city: The destination city name
        
    Returns:
        str: Research findings with a clear numerical minimum budget extracted
    """
    try:
        query = f"Minimum daily budget cost for tourist in {city} India per person including budget accommodation food transport 2024 2025 rupees"
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=4
        )
        
        # Extract and format results, focusing on content with numbers
        results = []
        raw_content = []
        for result in response.get('results', []):
            content = result.get('content', '')
            raw_content.append(content)
            # Prioritize results that contain currency symbols or numbers
            if any(symbol in content for symbol in ['₹', 'Rs', 'INR', 'rupee', '$']):
                results.append(f"• {content[:400]}")
        
        if not results:
            # Fallback to all results if no currency found
            for result in response.get('results', [])[:3]:
                results.append(f"• {result.get('content', '')[:400]}")
        
        # Use a simple LLM call to parse the numerical value
        extracted_amount = extract_minimum_budget_from_text("\n".join(raw_content[:3]), city)
        
        formatted_results = "\n\n".join(results)
        return f"💰 Minimum Daily Budget for {city}, India:\n\n**EXTRACTED MINIMUM: ₹{extracted_amount} per person per day**\n\n{formatted_results}"
    except Exception as e:
        return f"Error researching minimum budget for {city}: {str(e)}\n\n**EXTRACTED MINIMUM: ₹2500 per person per day** (fallback)"


def extract_minimum_budget_from_text(search_results: str, city: str) -> int:
    """
    Uses a simple LLM call to parse only the numerical minimum daily budget value from search results.
    
    Args:
        search_results: Raw text from Tavily search
        city: City name for context
        
    Returns:
        int: Minimum daily budget in INR per person
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        import os
        
        # Simple, fast model for extraction
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        extraction_prompt = f"""Extract the MINIMUM daily budget for a solo budget traveler in {city}, India from this text.

Search Results:
{search_results[:1500]}

Instructions:
1. Look for the LOWEST reasonable daily budget mentioned (for budget/backpacker travelers)
2. Consider: budget accommodation + street food/cheap meals + public transport + basic activities
3. If amounts are in USD, convert to INR (multiply by 83)
4. Return ONLY a single number in INR (no currency symbols, no explanations)
5. If you can't find a specific amount, estimate based on context or return 2500

Examples:
- "Budget travelers can manage on ₹1500-2000 per day" → Return: 1500
- "Minimum $40 per day" → Return: 3320
- "₹2500 is a comfortable budget" → Return: 2500

Return ONLY the number (integer)."""

        response = llm.invoke(extraction_prompt)
        
        # Extract number from response
        import re
        numbers = re.findall(r'\d+', str(response.content))
        if numbers:
            amount = int(numbers[0])
            # Sanity check: should be between 1000 and 20000 INR
            if 1000 <= amount <= 20000:
                return amount
        
        # Fallback
        return 2500
        
    except Exception as e:
        print(f"⚠️ Budget extraction error: {e}")
        return 2500


def estimate_transport_cost(origin: str, destination: str, num_people: int) -> float:
    """
    Estimates round-trip transportation cost from origin to destination using Tavily search.
    Returns total cost for all people (not per person).
    
    Args:
        origin: Origin city name
        destination: Destination city name
        num_people: Number of travelers
        
    Returns:
        float: Estimated total round-trip cost in INR for all people
    """
    try:
        query = f"cost of travel from {origin} to {destination} India round trip flight train bus fare rupees 2024 2025"
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=3
        )
        
        # Extract content and look for prices
        import re
        all_prices = []
        for result in response.get('results', []):
            content = result.get('content', '')
            # Find rupee amounts
            rupee_matches = re.findall(r'[₹Rs\.]\s*(\d{1,6})', content)
            all_prices.extend([int(m) for m in rupee_matches if 500 <= int(m) <= 50000])
        
        if all_prices:
            # Use median of found prices as estimate
            all_prices.sort()
            median_price = all_prices[len(all_prices) // 2]
            # Multiply by 2 for round trip (if not already round trip) and by number of people
            per_person_round_trip = median_price if median_price > 3000 else median_price * 2
            total_cost = per_person_round_trip * num_people
            return total_cost
        else:
            # Fallback to category-based estimate
            raise Exception("No prices found in search results")
            
    except Exception as e:
        # Fallback to category-based estimate
        raise e


def estimate_transport_fallback(origin: str, destination: str, num_people: int) -> float:
    """
    Fallback function to estimate transportation cost based on destination categories.
    Returns total cost for all people.
    
    Args:
        origin: Origin city name
        destination: Destination city name  
        num_people: Number of travelers
        
    Returns:
        float: Estimated total round-trip cost in INR for all people
    """
    destination_lower = destination.lower()
    origin_lower = origin.lower()
    
    # Define major city hubs
    major_metros = ['mumbai', 'delhi', 'bangalore', 'bengaluru', 'chennai', 'kolkata', 'hyderabad', 'pune', 'ahmedabad']
    
    # Hill stations and northern destinations (typically more expensive from south)
    hill_stations = ['manali', 'shimla', 'mussoorie', 'nainital', 'dharamshala', 'mcleodganj', 'kasol', 'leh', 'ladakh', 'darjeeling', 'gangtok']
    
    # Coastal and southern destinations
    coastal = ['goa', 'kochi', 'cochin', 'pondicherry', 'puducherry', 'varkala', 'kovalam', 'andaman', 'lakshadweep']
    
    # Northeast destinations (most expensive)
    northeast = ['shillong', 'kaziranga', 'tawang', 'aizawl', 'imphal', 'kohima']
    
    # Estimate per person round-trip cost
    if any(dest in destination_lower for dest in northeast):
        per_person = 12000  # Very expensive - limited connectivity
    elif any(dest in destination_lower for dest in hill_stations):
        per_person = 8000   # Expensive - usually requires flight + taxi
    elif any(dest in destination_lower for dest in coastal):
        per_person = 6000   # Moderate - good train/flight connectivity
    elif any(dest in destination_lower for dest in major_metros):
        per_person = 4000   # Cheaper - excellent connectivity
    else:
        per_person = 5000   # Default moderate estimate
    
    # Adjust based on origin city
    if any(city in origin_lower for city in major_metros):
        # Better connectivity from metros
        per_person = per_person * 0.9
    
    total_cost = per_person * num_people
    return total_cost


@tool
def get_travel_advisory(city: str) -> str:
    """
    Gets comprehensive travel safety advisories, alerts, and current conditions for a destination.
    Includes: safety warnings, weather alerts, natural disasters, travel restrictions, health advisories.
    Provides clear SAFETY VERDICT (Safe/Caution/Avoid).
    
    Args:
        city: The destination city name
        
    Returns:
        str: Safety verdict + real-time advisories, weather alerts, and travel warnings
    """
    try:
        # Get multiple types of advisories
        queries = [
            f"Current travel safety advisory warnings alerts for {city} India today",
            f"Weather alerts storms flooding for {city} India current",
            f"Travel restrictions health advisories {city} India latest"
        ]
        
        all_results = []
        for query in queries:
            response = tavily_client.search(
                query=query,
                search_depth="basic",
                max_results=2
            )
            
            for result in response.get('results', []):
                content = result.get('content', '')[:400]
                if content and content not in all_results:
                    all_results.append(content)
        
        # Analyze severity and determine safety verdict
        if not all_results:
            return f"✅ SAFETY VERDICT: SAFE TO TRAVEL\n\n🛡️ No major travel advisories, alerts, or safety concerns found for {city}. Destination is considered safe for travel."
        
        # Check for severe warnings
        combined_text = " ".join(all_results).lower()
        severe_keywords = ['avoid', 'danger', 'unsafe', 'critical', 'emergency', 'disaster', 'severe', 'extreme', 'prohibited', 'restricted']
        caution_keywords = ['warning', 'alert', 'caution', 'advisory', 'storm', 'flood', 'rain', 'monitor', 'check']
        
        has_severe = any(keyword in combined_text for keyword in severe_keywords)
        has_caution = any(keyword in combined_text for keyword in caution_keywords)
        
        if has_severe:
            verdict = "⚠️ SAFETY VERDICT: EXERCISE EXTREME CAUTION / CONSIDER POSTPONING"
            icon = "🚨"
        elif has_caution:
            verdict = "⚠️ SAFETY VERDICT: SAFE WITH PRECAUTIONS"
            icon = "⚠️"
        else:
            verdict = "✅ SAFETY VERDICT: GENERALLY SAFE"
            icon = "ℹ️"
        
        alerts_text = "\n\n".join([f"• {r}" for r in all_results])
        return f"{verdict}\n\n{icon} CURRENT ADVISORIES for {city}:\n\n{alerts_text}"
            
    except Exception as e:
        return f"⚠️ Could not fetch travel advisories for {city}: {str(e)}\nPlease check official travel advisory websites."


@tool
def get_realtime_weather(city: str) -> str:
    """
    Gets REAL-TIME current weather conditions and 7-day forecast for a destination.
    Essential for packing and activity planning.
    
    Args:
        city: The destination city name
        
    Returns:
        str: Current weather, temperature, forecast, best time to visit
    """
    try:
        query = f"Current weather forecast temperature {city} India today 7 day forecast"
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=3
        )
        
        results = []
        for result in response.get('results', []):
            content = result.get('content', '')[:350]
            if any(keyword in content.lower() for keyword in ['temperature', 'weather', 'forecast', 'rain', 'sunny', 'cloud']):
                results.append(content)
        
        if results:
            return f"🌤️ REAL-TIME WEATHER for {city}:\n\n" + "\n\n".join([f"• {r}" for r in results[:2]])
        else:
            return f"Weather data temporarily unavailable for {city}. Check local forecasts."
            
    except Exception as e:
        return f"⚠️ Could not fetch weather data for {city}: {str(e)}"


@tool
def get_travel_document_info(destination: str) -> str:
    """
    Searches for visa requirements, permits, and travel document information.
    Critical for international travel planning.
    
    Args:
        destination: The destination country or city
        
    Returns:
        str: Visa and travel document requirements
    """
    try:
        query = f"Visa requirements and travel documents needed for tourists visiting {destination}"
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=3
        )
        
        results = []
        for result in response.get('results', []):
            results.append(f"- {result.get('content', '')[:300]}...")
        
        return f"Travel Document Requirements for {destination}:\n" + "\n".join(results)
    except Exception as e:
        return f"Error getting travel document info for {destination}: {str(e)}"


# ============================================================================
# PLANNING TOOLS (Used by Main ReAct Agent in Step 5)
# ============================================================================

@tool
def find_travel_and_lodging_options(destination: str, budget_style: str) -> str:
    """
    Searches for travel options (flights, trains) and lodging accommodations
    based on the budget style (budget, mid-range, luxury).
    
    Args:
        destination: The destination city
        budget_style: One of 'budget', 'mid-range', or 'luxury'
        
    Returns:
        str: Available travel and lodging options
    """
    try:
        query = f"Best {budget_style} hotels and accommodations in {destination} with prices"
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5
        )
        
        results = []
        for result in response.get('results', []):
            results.append(f"- {result.get('content', '')[:400]}...")
        
        return f"Travel & Lodging Options ({budget_style}) for {destination}:\n" + "\n".join(results)
    except Exception as e:
        return f"Error finding travel/lodging options: {str(e)}"


@tool
def get_estimated_price(item_name: str) -> str:
    """
    Gets estimated price for a specific item, activity, or service.
    Useful for detailed budget planning.
    
    Args:
        item_name: Name of the item/activity/service to price
        
    Returns:
        str: Estimated price information
    """
    try:
        query = f"What is the typical price for {item_name}? Include price range."
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=3
        )
        
        results = []
        for result in response.get('results', []):
            results.append(f"- {result.get('content', '')[:250]}...")
        
        return f"Price Estimate for '{item_name}':\n" + "\n".join(results)
    except Exception as e:
        return f"Error estimating price for {item_name}: {str(e)}"


@tool
def get_booking_link(hotel_name: str, city: str) -> str:
    """
    Searches for booking links and contact information for a specific hotel.
    
    Args:
        hotel_name: Name of the hotel
        city: City where the hotel is located
        
    Returns:
        str: Booking links and contact information
    """
    try:
        query = f"{hotel_name} {city} booking website official contact"
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=3
        )
        
        results = []
        for result in response.get('results', []):
            url = result.get('url', '')
            content = result.get('content', '')[:200]
            # Skip image links
            if url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp')):
                continue
            results.append(f"- {url}\n  {content}...")
        
        return f"Booking Information for {hotel_name} in {city}:\n" + "\n".join(results)
    except Exception as e:
        return f"Error finding booking link: {str(e)}"


@tool
def find_authentic_local_food(city: str, cuisine_type: str = "local specialties") -> str:
    """
    Finds authentic, iconic local food experiences including specific street food stalls,
    local eateries, and hidden gems that locals actually eat at.
    Goes beyond generic tourist restaurants to discover real culinary experiences.
    
    Args:
        city: The city to search for food in
        cuisine_type: Type of food (e.g., "street food", "local specialties", "breakfast", "regional cuisine")
        
    Returns:
        str: Specific recommendations for authentic local food spots with locations and specialties
    """
    try:
        # Search for authentic local food experiences
        query = f"Best authentic local {cuisine_type} in {city} India - specific street food stalls, local favorites, hidden gems where locals eat, not tourist restaurants"
        response = tavily_client.search(
            query=query,
            search_depth="advanced",  # Deep search for quality recommendations
            max_results=5
        )
        
        results = []
        for result in response.get('results', []):
            content = result.get('content', '')
            if content:
                results.append(f"- {content[:350]}...")
        
        return f"Authentic Local Food Recommendations in {city} ({cuisine_type}):\n" + "\n".join(results)
    except Exception as e:
        return f"Error finding authentic food recommendations: {str(e)}"


@tool
def find_nearby_attractions(latitude: float, longitude: float, city: str, interests: str = "general") -> str:
    """
    Finds attractions, activities, and experiences near a specific GPS location.
    Perfect for on-the-go replanning when user's plan is disrupted.
    
    Args:
        latitude: Current GPS latitude
        longitude: Current GPS longitude  
        city: City name for context
        interests: User's interests (e.g., "history, food, culture")
        
    Returns:
        str: Nearby attractions with distances, timings, and recommendations
    """
    try:
        # Search for nearby attractions based on coordinates
        query = f"Top attractions activities near coordinates {latitude},{longitude} in {city} India - places to visit, things to do, {interests} related experiences, timings, entry fees"
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5
        )
        
        results = []
        for result in response.get('results', []):
            content = result.get('content', '')
            if content and any(keyword in content.lower() for keyword in ['attraction', 'visit', 'museum', 'park', 'temple', 'beach', 'fort', 'palace', 'market', 'restaurant']):
                results.append(f"• {content[:400]}")
        
        if results:
            return f"📍 NEARBY ATTRACTIONS at {latitude},{longitude} in {city}:\n\n" + "\n\n".join(results[:4])
        else:
            return f"Searching general attractions in {city}..."
            
    except Exception as e:
        return f"⚠️ Could not fetch nearby attractions: {str(e)}"


@tool
def get_quick_transport_options(from_location: str, to_location: str, city: str) -> str:
    """
    Gets immediate transportation options between two locations.
    Useful for replanning when user needs to move quickly.
    
    Args:
        from_location: Current location description
        to_location: Destination location
        city: City name
        
    Returns:
        str: Available transport options, costs, and time estimates
    """
    try:
        query = f"How to reach from {from_location} to {to_location} in {city} India - public transport, auto rickshaw, taxi, metro, bus options, cost, time, distance"
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=3
        )
        
        results = []
        for result in response.get('results', []):
            content = result.get('content', '')
            if content and any(keyword in content.lower() for keyword in ['transport', 'taxi', 'bus', 'metro', 'auto', 'rickshaw', 'uber', 'ola', 'minutes', 'km']):
                results.append(f"• {content[:300]}")
        
        if results:
            return f"🚗 TRANSPORT OPTIONS ({from_location} → {to_location}):\n\n" + "\n\n".join(results)
        else:
            return f"Consider using local taxis, auto-rickshaws, or ride-sharing apps like Uber/Ola in {city}."
            
    except Exception as e:
        return f"⚠️ Could not fetch transport options: {str(e)}"


# ============================================================================
# TOOL COLLECTIONS
# ============================================================================

# Research tools for the orchestrator
RESEARCH_TOOLS = [
    get_minimum_daily_budget,
    get_travel_advisory,
    get_travel_document_info,
    get_realtime_weather
]

# Planning tools for the main agent
PLANNING_TOOLS = [
    find_travel_and_lodging_options,
    get_estimated_price,
    get_booking_link,
    find_authentic_local_food,
    get_realtime_weather,
    get_travel_advisory
]

# Optimization tools for dynamic replanning
OPTIMIZATION_TOOLS = [
    find_nearby_attractions,
    get_quick_transport_options,
    get_realtime_weather,
    find_authentic_local_food,
    get_estimated_price
]

# All tools combined
ALL_TOOLS = RESEARCH_TOOLS + PLANNING_TOOLS + OPTIMIZATION_TOOLS
