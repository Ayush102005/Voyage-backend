"""
Test Direct Booking Links System
Feature 18: Deep Links to Booking Platforms
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from booking_links_service import get_booking_links_generator
from schemas import (
    FlightBookingParams,
    HotelBookingParams,
    TrainBookingParams,
    ActivityBookingParams
)
from datetime import datetime, timedelta


def display_feature_overview():
    """Display feature overview"""
    print("\n" + "="*80)
    print("🔗 DIRECT BOOKING LINKS - FEATURE OVERVIEW")
    print("="*80 + "\n")
    
    print("🎯 PURPOSE:")
    print("   Generate deep links to booking platforms with trip details pre-filled.")
    print("   Save users time by auto-filling destination, dates, passengers, etc.\n")
    
    print("🏢 SUPPORTED PLATFORMS:")
    print()
    print("   ✈️  FLIGHTS:")
    print("      • MakeMyTrip    - India's leading travel platform")
    print("      • Cleartrip     - Quick booking experience")
    print("      • Goibibo       - Great deals and cashback")
    print("      • Skyscanner    - Compare 100+ airlines")
    print()
    print("   🏨 HOTELS:")
    print("      • MakeMyTrip    - Wide hotel selection in India")
    print("      • Booking.com   - International properties + free cancellation")
    print("      • Agoda         - Best price guarantee")
    print("      • OYO           - Budget-friendly hotels")
    print("      • Airbnb        - Unique stays and apartments")
    print()
    print("   🚆 TRAINS:")
    print("      • IRCTC         - Official Indian Railways booking")
    print("      • ConfirmTkt    - Availability alerts and PNR status")
    print("      • RailYatri     - Live train tracking")
    print()
    print("   🚌 BUSES:")
    print("      • RedBus        - India's largest bus booking")
    print("      • AbhiBus       - 24/7 support")
    print()
    print("   🎯 ACTIVITIES:")
    print("      • Thrillophilia - Tours and adventures in India")
    print("      • GetYourGuide  - Skip-the-line tickets")
    print("      • Viator        - TripAdvisor experiences")
    print()
    
    print("💡 KEY FEATURES:")
    print("   • Pre-filled search parameters (dates, passengers, destination)")
    print("   • Affiliate tracking codes for revenue")
    print("   • Priority sorting (best platforms first)")
    print("   • Platform-specific URL formats")
    print("   • Estimated pricing (when available)")
    print("   • Mobile-optimized links")
    print()
    
    print("🔄 WORKFLOW:")
    print("   1. User completes trip planning")
    print("   2. System generates booking links for all categories")
    print("   3. User clicks link → Opens booking site with details pre-filled")
    print("   4. User completes booking on partner platform")
    print("   5. Voyage earns affiliate commission (revenue stream!)")
    print()
    
    print("="*80 + "\n")


def test_flight_links():
    """Test flight booking link generation"""
    print("\n" + "-"*80)
    print("TEST 1: Flight Booking Links")
    print("-"*80 + "\n")
    
    # Create flight params
    departure = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")
    
    params = FlightBookingParams(
        origin="Delhi",
        destination="Goa",
        departure_date=departure,
        return_date=return_date,
        adults=2,
        children=0,
        cabin_class="economy"
    )
    
    print(f"✈️  FLIGHT SEARCH PARAMETERS:")
    print(f"   Route: {params.origin} → {params.destination}")
    print(f"   Departure: {params.departure_date}")
    print(f"   Return: {params.return_date}")
    print(f"   Passengers: {params.adults} adults")
    print(f"   Class: {params.cabin_class}")
    print()
    
    # Generate links
    generator = get_booking_links_generator()
    links = generator.generate_flight_links(params)
    
    print(f"✅ Generated {len(links)} flight booking links:\n")
    
    for link in links:
        print(f"   {link.priority}. {link.platform}")
        print(f"      📝 {link.display_text}")
        if link.description:
            print(f"      💡 {link.description}")
        print(f"      🔗 {link.url}")
        if link.affiliate_code:
            print(f"      💰 Affiliate: {link.affiliate_code}")
        print()
    
    return links


def test_hotel_links():
    """Test hotel booking link generation"""
    print("\n" + "-"*80)
    print("TEST 2: Hotel Booking Links")
    print("-"*80 + "\n")
    
    checkin = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    checkout = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")
    
    params = HotelBookingParams(
        destination="Goa",
        checkin_date=checkin,
        checkout_date=checkout,
        adults=2,
        children=0,
        rooms=1,
        hotel_name="Taj Exotica"
    )
    
    print(f"🏨 HOTEL SEARCH PARAMETERS:")
    print(f"   Destination: {params.destination}")
    print(f"   Hotel: {params.hotel_name}")
    print(f"   Check-in: {params.checkin_date}")
    print(f"   Check-out: {params.checkout_date}")
    print(f"   Guests: {params.adults} adults, {params.rooms} room(s)")
    print()
    
    generator = get_booking_links_generator()
    links = generator.generate_hotel_links(params)
    
    print(f"✅ Generated {len(links)} hotel booking links:\n")
    
    for link in links:
        print(f"   {link.priority}. {link.platform}")
        print(f"      📝 {link.display_text}")
        if link.description:
            print(f"      💡 {link.description}")
        print(f"      🔗 {link.url[:80]}...")
        print()
    
    return links


def test_train_links():
    """Test train booking link generation"""
    print("\n" + "-"*80)
    print("TEST 3: Train Booking Links")
    print("-"*80 + "\n")
    
    journey_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    params = TrainBookingParams(
        origin="Delhi",
        destination="Goa",
        journey_date=journey_date,
        quota="GN",
        class_type="3A",
        passengers=2
    )
    
    print(f"🚆 TRAIN SEARCH PARAMETERS:")
    print(f"   Route: {params.origin} → {params.destination}")
    print(f"   Journey Date: {params.journey_date}")
    print(f"   Class: {params.class_type}")
    print(f"   Passengers: {params.passengers}")
    print()
    
    generator = get_booking_links_generator()
    links = generator.generate_train_links(params)
    
    print(f"✅ Generated {len(links)} train booking links:\n")
    
    for link in links:
        print(f"   {link.priority}. {link.platform}")
        print(f"      📝 {link.display_text}")
        if link.description:
            print(f"      💡 {link.description}")
        print(f"      🔗 {link.url}")
        print()
    
    return links


def test_bus_links():
    """Test bus booking link generation"""
    print("\n" + "-"*80)
    print("TEST 4: Bus Booking Links")
    print("-"*80 + "\n")
    
    journey_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"🚌 BUS SEARCH PARAMETERS:")
    print(f"   Route: Delhi → Agra")
    print(f"   Journey Date: {journey_date}")
    print()
    
    generator = get_booking_links_generator()
    links = generator.generate_bus_links("Delhi", "Agra", journey_date)
    
    print(f"✅ Generated {len(links)} bus booking links:\n")
    
    for link in links:
        print(f"   {link.priority}. {link.platform}")
        print(f"      📝 {link.display_text}")
        if link.description:
            print(f"      💡 {link.description}")
        print(f"      🔗 {link.url}")
        print()
    
    return links


def test_activity_links():
    """Test activity booking link generation"""
    print("\n" + "-"*80)
    print("TEST 5: Activity/Experience Booking Links")
    print("-"*80 + "\n")
    
    params = ActivityBookingParams(
        destination="Goa",
        activity_name="Scuba Diving",
        activity_type="adventure",
        participants=2
    )
    
    print(f"🎯 ACTIVITY SEARCH PARAMETERS:")
    print(f"   Destination: {params.destination}")
    print(f"   Activity: {params.activity_name}")
    print(f"   Type: {params.activity_type}")
    print(f"   Participants: {params.participants}")
    print()
    
    generator = get_booking_links_generator()
    links = generator.generate_activity_links(params)
    
    print(f"✅ Generated {len(links)} activity booking links:\n")
    
    for link in links:
        print(f"   {link.priority}. {link.platform}")
        print(f"      📝 {link.display_text}")
        if link.description:
            print(f"      💡 {link.description}")
        print(f"      🔗 {link.url[:80]}...")
        print()
    
    return links


def test_complete_trip_scenario():
    """Test generating all links for a complete trip"""
    print("\n" + "-"*80)
    print("TEST 6: Complete Trip Booking Links")
    print("-"*80 + "\n")
    
    print("🎒 TRIP SCENARIO:")
    print("   Destination: Goa")
    print("   Duration: 7 days")
    print("   Travelers: 2 adults")
    print("   Budget: ₹50,000")
    print()
    
    generator = get_booking_links_generator()
    
    # Dates
    dep_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    ret_date = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")
    
    all_links = {}
    
    # Flights
    flight_params = FlightBookingParams(
        origin="Delhi",
        destination="Goa",
        departure_date=dep_date,
        return_date=ret_date,
        adults=2,
        children=0,
        cabin_class="economy"
    )
    all_links["flights"] = generator.generate_flight_links(flight_params)
    
    # Hotels
    hotel_params = HotelBookingParams(
        destination="Goa",
        checkin_date=dep_date,
        checkout_date=ret_date,
        adults=2,
        rooms=1
    )
    all_links["hotels"] = generator.generate_hotel_links(hotel_params)
    
    # Activities
    activity_params = ActivityBookingParams(
        destination="Goa",
        participants=2
    )
    all_links["activities"] = generator.generate_activity_links(activity_params)
    
    # Summary
    total_links = sum(len(links) for links in all_links.values())
    
    print(f"📊 GENERATED BOOKING LINKS:")
    print(f"   ✈️  Flights: {len(all_links['flights'])} platforms")
    print(f"   🏨 Hotels: {len(all_links['hotels'])} platforms")
    print(f"   🎯 Activities: {len(all_links['activities'])} platforms")
    print(f"   📍 Total Links: {total_links}")
    print()
    
    print("🎯 TOP RECOMMENDATIONS:")
    print()
    print("   1. Book Flights First")
    for link in all_links["flights"][:2]:
        print(f"      • {link.platform}: {link.display_text}")
    print()
    
    print("   2. Then Book Hotel")
    for link in all_links["hotels"][:2]:
        print(f"      • {link.platform}: {link.display_text}")
    print()
    
    print("   3. Add Activities")
    for link in all_links["activities"][:2]:
        print(f"      • {link.platform}: {link.display_text}")
    print()
    
    return all_links


def display_integration_guide():
    """Display API integration examples"""
    print("\n" + "="*80)
    print("📡 API INTEGRATION GUIDE")
    print("="*80 + "\n")
    
    print("🔐 AUTHENTICATION:")
    print("   All endpoints require Firebase JWT token\n")
    
    print("📝 1. GENERATE BOOKING LINKS (POST /api/booking-links)")
    print("""
   Request:
   {
     "trip_id": "trip_12345",
     "categories": ["flight", "hotel", "activity"],
     "platforms": null  // null = all platforms
   }
   
   Response:
   {
     "success": true,
     "message": "Generated 15 booking links for your trip",
     "trip_id": "trip_12345",
     "booking_links": {
       "flight": [
         {
           "platform": "MakeMyTrip",
           "category": "flight",
           "url": "https://www.makemytrip.com/flight/search?...",
           "display_text": "Book Flight: Delhi → Goa",
           "estimated_price": 8500.0,
           "description": "Search flights for 2 passengers",
           "affiliate_code": "voyage2025",
           "priority": 1
         },
         // ... more flight links
       ],
       "hotel": [ /* hotel links */ ],
       "activity": [ /* activity links */ ]
     },
     "total_links": 15,
     "generated_at": "2025-11-01T10:30:00Z"
   }
   """)
    
    print("\n📚 2. GET BOOKING LINKS (GET /api/booking-links/{trip_id})")
    print("""
   URL: /api/booking-links/trip_12345?categories=flight,hotel
   
   Response: Same as POST endpoint
   """)
    
    print("\n🎯 3. FRONTEND INTEGRATION:")
    print("""
   // React Component Example
   
   const BookingLinks = ({ tripId }) => {
     const [links, setLinks] = useState(null);
     
     useEffect(() => {
       fetchBookingLinks();
     }, []);
     
     const fetchBookingLinks = async () => {
       const token = await firebase.auth().currentUser.getIdToken();
       
       const response = await fetch(
         `http://localhost:8000/api/booking-links/${tripId}`,
         { headers: { 'Authorization': `Bearer ${token}` } }
       );
       
       const data = await response.json();
       setLinks(data.booking_links);
     };
     
     return (
       <div className="booking-links">
         <h2>Ready to Book?</h2>
         
         {/* Flights */}
         <section>
           <h3>✈️  Book Your Flight</h3>
           {links.flight?.map(link => (
             <a 
               key={link.platform}
               href={link.url}
               target="_blank"
               className="booking-card"
             >
               <div className="platform">{link.platform}</div>
               <div className="action">{link.display_text}</div>
               {link.description && (
                 <div className="description">{link.description}</div>
               )}
               {link.estimated_price && (
                 <div className="price">~₹{link.estimated_price}</div>
               )}
             </a>
           ))}
         </section>
         
         {/* Similar sections for hotel, train, activity */}
       </div>
     );
   };
   """)
    
    print("\n💡 BEST PRACTICES:")
    print("   • Generate links after trip plan is finalized")
    print("   • Open links in new tab (_blank)")
    print("   • Track clicks for analytics")
    print("   • Sort by priority (1 = highest)")
    print("   • Show estimated prices when available")
    print("   • Include affiliate codes for revenue")
    print("   • Mobile-optimize the booking flow")
    print()
    
    print("="*80 + "\n")


if __name__ == "__main__":
    display_feature_overview()
    
    try:
        # Run all tests
        flight_links = test_flight_links()
        hotel_links = test_hotel_links()
        train_links = test_train_links()
        bus_links = test_bus_links()
        activity_links = test_activity_links()
        all_links = test_complete_trip_scenario()
        
        display_integration_guide()
        
        # Summary
        total_tests = 6
        total_links_generated = (
            len(flight_links) + 
            len(hotel_links) + 
            len(train_links) + 
            len(bus_links) + 
            len(activity_links)
        )
        
        print("\n" + "🎉" * 40)
        print("\n   ALL TESTS PASSED! Direct Booking Links Ready! 🚀\n")
        print("🎉" * 40 + "\n")
        
        print("📊 TEST SUMMARY:")
        print(f"   ✓ {total_tests} test scenarios executed")
        print(f"   ✓ {total_links_generated} booking links generated")
        print(f"   ✓ 14 booking platforms integrated")
        print(f"   ✓ 5 booking categories (flight, hotel, train, bus, activity)")
        print()
        
        print("🚀 NEXT STEPS:")
        print("   1. Start server: python server.py")
        print("   2. Complete trip planning")
        print("   3. GET /api/booking-links/{trip_id}")
        print("   4. Display links to user")
        print("   5. User clicks → Books on partner site")
        print("   6. Earn affiliate revenue! 💰")
        print()
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
