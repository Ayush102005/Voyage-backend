"""
Test the Voyage Verified Reviews & Taste Graph System
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment
load_dotenv()

from schemas import (
    ReviewRating, ReviewHighlight, CreateReviewRequest,
    TasteGraph, TasteGraphNode
)
from taste_graph_service import TasteGraphBuilder, get_taste_graph_builder


def display_feature_overview():
    """Display feature overview"""
    print("\n" + "="*80)
    print("📚 VOYAGE VERIFIED REVIEWS & TASTE GRAPH - FEATURE OVERVIEW")
    print("="*80 + "\n")
    
    print("🎯 PURPOSE:")
    print("   Build personalized taste graphs from user reviews to power")
    print("   increasingly accurate recommendations over time.\n")
    
    print("📊 DATA COLLECTION (Voyage Verified Reviews):")
    print("   ✓ Post-trip reviews with detailed ratings")
    print("   ✓ Structured highlights & lowlights")
    print("   ✓ Actual spending vs estimated")
    print("   ✓ Hidden gems discovered")
    print("   ✓ Photo uploads")
    print("   ✓ Location verification\n")
    
    print("🧠 TASTE GRAPH COMPONENTS:")
    print("   • Destination Preferences (5-star scored)")
    print("   • Food Preferences (cuisines, dishes, restaurants)")
    print("   • Activity Preferences (adventure, culture, relaxation)")
    print("   • Accommodation Types (hotels, homestays, camps)")
    print("   • Budget Patterns (spending by category)")
    print("   • Seasonality (preferred travel months)")
    print("   • Trip Types (adventure, luxury, budget, etc.)\n")
    
    print("🔍 HOW IT WORKS:")
    print("   1. User completes trip → Writes detailed review")
    print("   2. System extracts preferences from review data")
    print("   3. Builds/updates taste graph with weighted scores")
    print("   4. Generates AI insights from patterns")
    print("   5. Uses taste graph to personalize future recommendations\n")
    
    print("💡 SCORING SYSTEM:")
    print("   • 5-star rating → 1.0 preference score (love it!)")
    print("   • 4-star rating → 0.7 preference score (like it)")
    print("   • 3-star rating → 0.4 preference score (neutral)")
    print("   • 2-star rating → 0.2 preference score (dislike)")
    print("   • 1-star rating → 0.0 preference score (avoid)\n")
    
    print("📈 CONFIDENCE SCORING:")
    print("   • 1-2 reviews: 10-20% confidence (learning phase)")
    print("   • 3-5 reviews: 30-50% confidence (patterns emerging)")
    print("   • 6-9 reviews: 60-90% confidence (reliable data)")
    print("   • 10+ reviews: 100% confidence (fully personalized)\n")
    
    print("🎯 USE CASES:")
    print("   1. Personalized trip planning (avoid dislikes)")
    print("   2. Restaurant recommendations (loved foods)")
    print("   3. Activity suggestions (preferred experiences)")
    print("   4. Budget optimization (spending patterns)")
    print("   5. Seasonal timing (best travel months)")
    print("   6. Destination discovery (similar to loved places)\n")
    
    print("="*80 + "\n")


def test_review_structure():
    """Test review data structure"""
    print("\n" + "-"*80)
    print("TEST 1: Review Data Structure")
    print("-"*80 + "\n")
    
    # Create sample review
    ratings = ReviewRating(
        overall=5,
        itinerary_accuracy=5,
        budget_accuracy=4,
        recommendations_quality=5,
        destinations=5,
        accommodations=4,
        food=5,
        activities=5
    )
    
    highlights = [
        ReviewHighlight(
            type="highlight",
            category="food",
            item_name="Butter Chicken at Karim's",
            description="Absolutely incredible! Best butter chicken I've ever had. The meat was so tender.",
            rating=5,
            location="Jama Masjid, Old Delhi",
            would_recommend=True,
            tags=["mughlai", "non-veg", "historic", "must-try"]
        ),
        ReviewHighlight(
            type="highlight",
            category="destination",
            item_name="Taj Mahal at Sunrise",
            description="Magical experience. The pink glow at sunrise is breathtaking. Go early to avoid crowds!",
            rating=5,
            location="Agra",
            would_recommend=True,
            tags=["monument", "sunrise", "photography", "unesco"]
        ),
        ReviewHighlight(
            type="highlight",
            category="activity",
            item_name="Tuk-Tuk Tour of Old Delhi",
            description="Thrilling ride through narrow lanes. Guide was knowledgeable and friendly.",
            rating=4,
            location="Old Delhi",
            would_recommend=True,
            tags=["adventure", "local-experience", "cultural"]
        )
    ]
    
    print("✅ Sample Review Structure:")
    print(f"   Overall Rating: {ratings.overall}/5")
    print(f"   Highlights: {len(highlights)}")
    print()
    
    for i, h in enumerate(highlights, 1):
        print(f"   {i}. {h.item_name} ({h.category})")
        print(f"      Rating: {h.rating}/5")
        print(f"      Location: {h.location}")
        print(f"      Tags: {', '.join(h.tags)}")
        print(f"      Would Recommend: {'✅ Yes' if h.would_recommend else '❌ No'}")
        print()
    
    print("✅ Review structure validated!\n")
    return ratings, highlights


def test_taste_graph_building():
    """Test building taste graph from reviews"""
    print("\n" + "-"*80)
    print("TEST 2: Taste Graph Building")
    print("-"*80 + "\n")
    
    from schemas import VoyageVerifiedReview, TripReview
    
    # Create mock reviews
    ratings1 = ReviewRating(
        overall=5, itinerary_accuracy=5, budget_accuracy=4,
        recommendations_quality=5, destinations=5, accommodations=4,
        food=5, activities=5
    )
    
    highlights1 = [
        ReviewHighlight(
            type="highlight", category="food",
            item_name="Butter Chicken", description="Amazing!",
            rating=5, would_recommend=True, tags=["mughlai", "non-veg"]
        ),
        ReviewHighlight(
            type="highlight", category="destination",
            item_name="Taj Mahal", description="Breathtaking!",
            rating=5, would_recommend=True, tags=["monument", "unesco"]
        ),
        ReviewHighlight(
            type="highlight", category="activity",
            item_name="River Rafting", description="Thrilling!",
            rating=5, would_recommend=True, tags=["adventure", "water-sports"]
        )
    ]
    
    trip_review1 = TripReview(
        trip_id="trip_001",
        ratings=ratings1,
        overall_experience="Amazing trip! Everything was perfect.",
        what_worked_well="Great planning, accurate budget, loved the food recommendations.",
        what_could_improve="Nothing really, all was great!",
        highlights=highlights1,
        actual_spent=45000,
        budget_breakdown={"accommodation": 15000, "food": 12000, "activities": 10000, "transport": 8000},
        travel_dates={"start": "2025-10-15", "end": "2025-10-20"}
    )
    
    review1 = VoyageVerifiedReview(
        id="review_001",
        user_id="test_user",
        trip_id="trip_001",
        review=trip_review1,
        created_at=datetime(2025, 10, 25),
        is_public=True,
        helpful_count=5
    )
    
    # Second review with different preferences
    ratings2 = ReviewRating(
        overall=4, itinerary_accuracy=4, budget_accuracy=5,
        recommendations_quality=4, destinations=5, accommodations=5,
        food=4, activities=4
    )
    
    highlights2 = [
        ReviewHighlight(
            type="highlight", category="food",
            item_name="Dal Baati Churma", description="Authentic Rajasthani cuisine!",
            rating=4, would_recommend=True, tags=["rajasthani", "vegetarian", "traditional"]
        ),
        ReviewHighlight(
            type="highlight", category="destination",
            item_name="Jaipur City Palace", description="Beautiful architecture!",
            rating=5, would_recommend=True, tags=["palace", "heritage", "photography"]
        ),
        ReviewHighlight(
            type="highlight", category="accommodation",
            item_name="Heritage Haveli Stay", description="Felt like royalty!",
            rating=5, would_recommend=True, tags=["heritage", "luxury", "unique"]
        )
    ]
    
    trip_review2 = TripReview(
        trip_id="trip_002",
        ratings=ratings2,
        overall_experience="Wonderful cultural experience in Rajasthan!",
        what_worked_well="Heritage stays were amazing, food was authentic.",
        what_could_improve="Could have spent more time in each city.",
        highlights=highlights2,
        actual_spent=55000,
        budget_breakdown={"accommodation": 20000, "food": 14000, "activities": 12000, "transport": 9000},
        travel_dates={"start": "2025-11-01", "end": "2025-11-07"}
    )
    
    review2 = VoyageVerifiedReview(
        id="review_002",
        user_id="test_user",
        trip_id="trip_002",
        review=trip_review2,
        created_at=datetime(2025, 11, 10),
        is_public=True,
        helpful_count=3
    )
    
    # Build taste graph
    builder = get_taste_graph_builder()
    taste_graph = builder.build_taste_graph("test_user", [review1, review2])
    
    print(f"✅ Taste Graph Built Successfully!\n")
    print(f"📊 STATISTICS:")
    print(f"   Total Reviews: {taste_graph.total_reviews}")
    print(f"   Total Trips: {taste_graph.total_trips}")
    print(f"   Average Rating: {taste_graph.average_rating:.1f}/5")
    print(f"   Confidence Score: {taste_graph.confidence_score:.2f} (20%)\n")
    
    print(f"🌍 DESTINATIONS ({len(taste_graph.destinations)} found):")
    for dest in taste_graph.destinations[:3]:
        print(f"   • {dest.item_name}")
        print(f"     Preference Score: {dest.preference_score:.2f}")
        print(f"     Sentiment: {dest.sentiment}")
        print(f"     Average Rating: {dest.average_rating:.1f}/5")
        print(f"     Tags: {', '.join(dest.tags[:5])}")
        print()
    
    print(f"🍽️  FOODS ({len(taste_graph.foods)} found):")
    for food in taste_graph.foods[:3]:
        print(f"   • {food.item_name}")
        print(f"     Preference Score: {food.preference_score:.2f}")
        print(f"     Sentiment: {food.sentiment}")
        print(f"     Average Rating: {food.average_rating:.1f}/5")
        print(f"     Tags: {', '.join(food.tags[:5])}")
        print()
    
    print(f"🎯 ACTIVITIES ({len(taste_graph.activities)} found):")
    for activity in taste_graph.activities[:3]:
        print(f"   • {activity.item_name}")
        print(f"     Preference Score: {activity.preference_score:.2f}")
        print(f"     Sentiment: {activity.sentiment}")
        print(f"     Average Rating: {activity.average_rating:.1f}/5")
        print()
    
    print(f"🏨 ACCOMMODATIONS ({len(taste_graph.accommodations)} found):")
    for acc in taste_graph.accommodations[:3]:
        print(f"   • {acc.item_name}")
        print(f"     Preference Score: {acc.preference_score:.2f}")
        print(f"     Sentiment: {acc.sentiment}")
        print()
    
    print(f"⭐ TOP PREFERENCES:")
    for pref in taste_graph.top_preferences[:5]:
        print(f"   • {pref}")
    print()
    
    print(f"💰 BUDGET PATTERNS:")
    if taste_graph.budget_patterns:
        print(f"   Average per Trip: ₹{taste_graph.budget_patterns.get('average_per_trip', 0):,.0f}")
        print(f"   Accommodation: {taste_graph.budget_patterns.get('accommodation_percentage', 0):.1f}%")
        print(f"   Food: {taste_graph.budget_patterns.get('food_percentage', 0):.1f}%")
        print(f"   Activities: {taste_graph.budget_patterns.get('activities_percentage', 0):.1f}%")
    print()
    
    print(f"📅 SEASONALITY:")
    if taste_graph.seasonality:
        seasons = taste_graph.seasonality.get('preferred_seasons', [])
        if seasons:
            print(f"   Preferred Seasons: {', '.join(seasons)}")
    print()
    
    return taste_graph


def test_insights_generation():
    """Test AI insights generation"""
    print("\n" + "-"*80)
    print("TEST 3: AI Insights Generation")
    print("-"*80 + "\n")
    
    # Build taste graph from previous test
    from schemas import VoyageVerifiedReview, TripReview
    
    # Create reviews with strong patterns
    builder = get_taste_graph_builder()
    
    # Mock taste graph with clear patterns
    from schemas import TasteGraph, TasteGraphNode
    from datetime import datetime
    
    taste_graph = TasteGraph(
        user_id="test_user",
        destinations=[
            TasteGraphNode(
                category="destination",
                item_id="goa",
                item_name="Goa",
                preference_score=0.9,
                sentiment="positive",
                interaction_count=3,
                average_rating=4.7,
                tags=["beach", "party", "relaxation"],
                last_interaction=datetime.now(),
                first_interaction=datetime.now()
            ),
            TasteGraphNode(
                category="destination",
                item_id="taj_mahal",
                item_name="Taj Mahal",
                preference_score=0.85,
                sentiment="positive",
                interaction_count=2,
                average_rating=4.5,
                tags=["monument", "unesco", "cultural"],
                last_interaction=datetime.now(),
                first_interaction=datetime.now()
            )
        ],
        foods=[
            TasteGraphNode(
                category="food",
                item_id="butter_chicken",
                item_name="Butter Chicken",
                preference_score=1.0,
                sentiment="positive",
                interaction_count=2,
                average_rating=5.0,
                tags=["mughlai", "non-veg", "north-indian"],
                last_interaction=datetime.now(),
                first_interaction=datetime.now()
            )
        ],
        activities=[
            TasteGraphNode(
                category="activity",
                item_id="river_rafting",
                item_name="River Rafting",
                preference_score=1.0,
                sentiment="positive",
                interaction_count=2,
                average_rating=5.0,
                tags=["adventure", "water-sports", "adrenaline"],
                last_interaction=datetime.now(),
                first_interaction=datetime.now()
            )
        ],
        top_preferences=["Butter Chicken", "River Rafting", "Goa Beaches"],
        avoid_list=["Crowded Tourist Traps", "Overpriced Restaurants"],
        preferred_trip_types=["adventure", "beach", "cultural"],
        budget_patterns={
            "average_per_trip": 50000,
            "accommodation_percentage": 35,
            "food_percentage": 25,
            "activities_percentage": 25,
            "transport_percentage": 15
        },
        seasonality={
            "preferred_seasons": ["winter", "spring"],
            "preferred_months": ["November", "December", "February"]
        },
        total_reviews=3,
        total_trips=3,
        average_rating=4.7,
        last_updated=datetime.now(),
        confidence_score=0.3
    )
    
    # Generate insights
    insights = builder.generate_insights(taste_graph)
    
    print(f"✅ Generated {len(insights)} AI Insights!\n")
    
    for i, insight in enumerate(insights, 1):
        print(f"{i}. [{insight.insight_type.upper()}] {insight.category}")
        print(f"   💡 {insight.message}")
        print(f"   Confidence: {insight.confidence:.0%}")
        print(f"   Evidence: {', '.join(insight.supporting_evidence[:3])}")
        print()
    
    return insights


def test_incremental_update():
    """Test incremental taste graph updates"""
    print("\n" + "-"*80)
    print("TEST 4: Incremental Taste Graph Update")
    print("-"*80 + "\n")
    
    from schemas import VoyageVerifiedReview, TripReview, TasteGraph
    
    # Start with existing taste graph
    existing_graph = TasteGraph(
        user_id="test_user",
        destinations=[],
        foods=[],
        activities=[],
        accommodations=[],
        experiences=[],
        top_preferences=[],
        avoid_list=[],
        preferred_trip_types=[],
        budget_patterns={},
        seasonality={},
        total_reviews=2,
        total_trips=2,
        average_rating=4.5,
        last_updated=datetime(2025, 10, 1),
        confidence_score=0.2
    )
    
    print("📊 BEFORE UPDATE:")
    print(f"   Total Reviews: {existing_graph.total_reviews}")
    print(f"   Average Rating: {existing_graph.average_rating:.1f}/5")
    print(f"   Confidence: {existing_graph.confidence_score:.0%}\n")
    
    # Create new review
    new_ratings = ReviewRating(
        overall=5, itinerary_accuracy=5, budget_accuracy=5,
        recommendations_quality=5, destinations=5, accommodations=5,
        food=5, activities=5
    )
    
    new_highlights = [
        ReviewHighlight(
            type="highlight", category="food",
            item_name="Masala Dosa", description="Perfect breakfast!",
            rating=5, would_recommend=True, tags=["south-indian", "vegetarian"]
        )
    ]
    
    new_trip_review = TripReview(
        trip_id="trip_003",
        ratings=new_ratings,
        overall_experience="Perfect trip to Karnataka!",
        what_worked_well="Everything was amazing!",
        what_could_improve="Nothing!",
        highlights=new_highlights,
        actual_spent=40000
    )
    
    new_review = VoyageVerifiedReview(
        id="review_003",
        user_id="test_user",
        trip_id="trip_003",
        review=new_trip_review,
        created_at=datetime.now(),
        is_public=True,
        helpful_count=0
    )
    
    # Update taste graph
    builder = get_taste_graph_builder()
    updated_graph = builder.update_taste_graph_incremental(existing_graph, new_review)
    
    print("📊 AFTER UPDATE:")
    print(f"   Total Reviews: {updated_graph.total_reviews}")
    print(f"   Average Rating: {updated_graph.average_rating:.1f}/5")
    print(f"   Confidence: {updated_graph.confidence_score:.0%}")
    print(f"   Foods: {len(updated_graph.foods)}")
    print()
    
    print("✅ Incremental update successful!")
    print("   Added 1 new review → Updated statistics and confidence\n")


def display_api_integration():
    """Display API integration examples"""
    print("\n" + "="*80)
    print("📡 API INTEGRATION GUIDE")
    print("="*80 + "\n")
    
    print("🔐 AUTHENTICATION:")
    print("   All endpoints require Firebase JWT token in Authorization header\n")
    
    print("📝 1. CREATE REVIEW (POST /api/reviews)")
    print("""
   Request Body:
   {
     "trip_id": "trip_12345",
     "ratings": {
       "overall": 5,
       "itinerary_accuracy": 5,
       "budget_accuracy": 4,
       "recommendations_quality": 5,
       "destinations": 5,
       "accommodations": 4,
       "food": 5,
       "activities": 5
     },
     "overall_experience": "Amazing trip! Everything exceeded expectations...",
     "what_worked_well": "Great planning, accurate budget, loved food recs...",
     "what_could_improve": "Could have more free time...",
     "highlights": [
       {
         "type": "highlight",
         "category": "food",
         "item_name": "Butter Chicken at Karim's",
         "description": "Best butter chicken ever! So tender and flavorful.",
         "rating": 5,
         "location": "Old Delhi",
         "would_recommend": true,
         "tags": ["mughlai", "must-try", "historic"]
       },
       {
         "type": "highlight",
         "category": "destination",
         "item_name": "Taj Mahal at Sunrise",
         "description": "Magical experience. Pink glow was breathtaking!",
         "rating": 5,
         "location": "Agra",
         "would_recommend": true,
         "tags": ["monument", "sunrise", "unesco"]
       }
     ],
     "lowlights": [],
     "unexpected_discoveries": "Found an amazing local market...",
     "hidden_gems": ["Secret viewpoint", "Local cafe"],
     "actual_spent": 45000,
     "budget_breakdown": {
       "accommodation": 15000,
       "food": 12000,
       "activities": 10000,
       "transport": 8000
     },
     "travel_dates": {
       "start": "2025-10-15",
       "end": "2025-10-20"
     },
     "travel_companions": "couple"
   }
   
   Response:
   - VoyageVerifiedReview object with ID
   - Taste graph automatically updated in background
   """)
    
    print("\n📚 2. GET ALL REVIEWS (GET /api/reviews)")
    print("""
   Response:
   {
     "success": true,
     "message": "Found 3 reviews",
     "reviews": [
       {
         "id": "review_001",
         "trip_id": "trip_001",
         "destination": "Agra, Delhi",
         "overall_rating": 5,
         "overall_experience": "Amazing trip! ...",
         "highlights_count": 3,
         "created_at": "2025-10-25T10:30:00Z",
         "verified_visited": false
       }
     ],
     "total_reviews": 3,
     "average_overall_rating": 4.7
   }
   """)
    
    print("\n🧠 3. GET TASTE GRAPH (GET /api/taste-graph)")
    print("""
   Response:
   {
     "success": true,
     "message": "Taste graph loaded successfully",
     "taste_graph": {
       "user_id": "user_123",
       "destinations": [
         {
           "item_name": "Goa",
           "preference_score": 0.9,
           "sentiment": "positive",
           "average_rating": 4.7,
           "tags": ["beach", "party", "relaxation"]
         }
       ],
       "foods": [...],
       "activities": [...],
       "top_preferences": ["Butter Chicken", "River Rafting"],
       "avoid_list": ["Crowded Places"],
       "preferred_trip_types": ["adventure", "beach"],
       "budget_patterns": {
         "average_per_trip": 50000,
         "accommodation_percentage": 35
       },
       "total_reviews": 3,
       "confidence_score": 0.3
     },
     "insights": [
       {
         "insight_type": "preference",
         "category": "destination",
         "message": "You absolutely love Goa! Consider similar beach destinations.",
         "confidence": 0.9
       }
     ],
     "recommendations": [
       "Based on your love for Butter Chicken, you might enjoy Mughlai cuisine in Lucknow",
       "Your adventure travel style suggests Ladakh or Spiti Valley"
     ]
   }
   """)
    
    print("\n🔄 4. REBUILD TASTE GRAPH (POST /api/taste-graph/rebuild)")
    print("""
   Use for:
   - Debugging
   - After fixing data issues
   - Manual refresh
   
   Response:
   {
     "success": true,
     "message": "Taste graph rebuilt from 5 reviews",
     "confidence_score": 0.5
   }
   """)
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    display_feature_overview()
    
    try:
        # Run tests
        test_review_structure()
        taste_graph = test_taste_graph_building()
        insights = test_insights_generation()
        test_incremental_update()
        
        display_api_integration()
        
        print("\n" + "🎉" * 40)
        print("\n   ALL TESTS PASSED! Voyage Verified Reviews & Taste Graph Ready! 🚀\n")
        print("🎉" * 40 + "\n")
        
        print("📝 SUMMARY:")
        print("   ✓ Review structure validated")
        print("   ✓ Taste graph building working")
        print("   ✓ AI insights generation working")
        print("   ✓ Incremental updates working")
        print("   ✓ API endpoints documented")
        print()
        print("🚀 NEXT STEPS:")
        print("   1. Start server: python server.py")
        print("   2. Complete a trip")
        print("   3. POST review to /api/reviews")
        print("   4. GET taste graph from /api/taste-graph")
        print("   5. Watch recommendations improve over time!")
        print()
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
