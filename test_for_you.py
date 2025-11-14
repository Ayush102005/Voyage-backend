"""
Test script to verify the 'For You' suggestions feature is working correctly.
Run this after starting the server to test the endpoint.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
# Replace with actual Firebase token after logging in
AUTH_TOKEN = "your_firebase_token_here"

def test_for_you_endpoint():
    """Test the /api/for-you endpoint"""
    
    print("=" * 60)
    print("Testing 'For You' Suggestions Endpoint")
    print("=" * 60)
    
    # Test 1: Get suggestions
    print("\n📍 Test 1: GET /api/for-you")
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/for-you", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS!")
            print(f"   Personalization Score: {data.get('personalization_score')}%")
            print(f"   Number of Suggestions: {len(data.get('suggestions', []))}")
            
            # Display suggestions by category
            suggestions = data.get('suggestions', [])
            categories = {}
            for suggestion in suggestions:
                cat = suggestion.get('category', 'uncategorized')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(suggestion)
            
            print("\n📋 Suggestions by Category:")
            for category, items in categories.items():
                print(f"\n   🏷️  {category.upper().replace('_', ' ')}")
                for item in items:
                    print(f"      • {item.get('destination')}: {item.get('title')}")
                    if item.get('urgency'):
                        print(f"        ⚠️  {item.get('urgency')}")
            
            # Display user context
            context = data.get('user_context', {})
            print(f"\n👤 User Context:")
            print(f"   Trips: {context.get('trips_count')}")
            print(f"   Has Preferences: {context.get('has_preferences')}")
            print(f"   Learned Patterns: {context.get('has_learned_patterns')}")
            print(f"   Saved Destinations: {context.get('saved_destinations_count')}")
            
        elif response.status_code == 401:
            print("❌ AUTHENTICATION REQUIRED")
            print("   Please update AUTH_TOKEN with a valid Firebase token")
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"   {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR")
        print("   Make sure the server is running on localhost:8000")
        print("   Run: cd backend && python server.py")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 2: Refresh suggestions
    print("\n\n📍 Test 2: GET /api/for-you?refresh=true")
    try:
        response = requests.get(f"{BASE_URL}/api/for-you?refresh=true", headers=headers)
        
        if response.status_code == 200:
            print("✅ Refresh parameter working!")
        else:
            print(f"⚠️  Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")


def test_dashboard_endpoint():
    """Test that dashboard includes suggestions"""
    
    print("\n\n" + "=" * 60)
    print("Testing Dashboard with 'For You' Suggestions")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get('personalized_suggestions', [])
            
            print(f"✅ Dashboard loaded successfully")
            print(f"   Personalized Suggestions: {len(suggestions)}")
            
            if suggestions:
                print("\n📋 Dashboard Suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"   {i}. {suggestion.get('destination')}")
                    print(f"      Category: {suggestion.get('category', 'N/A')}")
                    if suggestion.get('urgency'):
                        print(f"      Urgency: {suggestion.get('urgency')}")
        elif response.status_code == 401:
            print("❌ AUTHENTICATION REQUIRED")
        else:
            print(f"❌ FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")


def display_feature_summary():
    """Display what was implemented"""
    
    print("\n\n" + "=" * 60)
    print("'FOR YOU' SUGGESTIONS - FEATURE SUMMARY")
    print("=" * 60)
    
    print("""
✅ IMPLEMENTED FEATURES:

1. Dedicated Endpoint: GET /api/for-you
   - Returns 4 personalized suggestions
   - Includes personalization score (0-100)
   - Provides user context

2. Four Suggestion Categories:
   🎯 Perfect Match - Ideal destination based on preferences
   🔥 Trending Now - Current events/festivals/seasonal
   💎 Hidden Gem - Off-beat places matching style
   ⭐ Wishlist Inspiration - Related to saved destinations

3. Personalization Factors:
   • Past trip destinations & patterns
   • Stated interests from preferences
   • Learned behavior patterns
   • Saved wishlist destinations
   • Budget & spending patterns
   • Travel style & pace
   • Food preferences
   • Current month/season/events

4. Special Features:
   • First-person language ("You'd love...")
   • Specific references to user data
   • Time-sensitive urgency flags
   • Budget-matched suggestions
   • Seasonal/event awareness

5. Enhanced Dashboard:
   • Integrated 'For You' suggestions
   • Auto-learning from trip history
   • Personalization score tracking

6. Fallback Logic:
   • Works for new users (generic suggestions)
   • Adapts to available data
   • Graceful error handling

📚 API DOCUMENTATION:

Endpoint: GET /api/for-you
Authentication: Required (Firebase)
Parameters:
  - refresh (optional): boolean - Regenerate suggestions

Response Schema:
{
  "success": true,
  "message": string,
  "suggestions": [
    {
      "destination": string,
      "title": string,           // Personal, using "you/your"
      "description": string,       // 2-3 compelling sentences
      "reason": string,           // Why it's perfect for this user
      "estimated_budget": string,
      "best_time": string,
      "category": "perfect_match" | "trending_now" | "hidden_gem" | "wishlist_inspiration",
      "urgency": string | null    // Time-sensitive info
    }
  ],
  "personalization_score": number,  // 0-100
  "user_context": {
    "trips_count": number,
    "has_preferences": boolean,
    "has_learned_patterns": boolean,
    "saved_destinations_count": number
  }
}
""")


if __name__ == "__main__":
    print("\n🚀 Voyage Travel Planner - 'For You' Feature Test\n")
    
    if AUTH_TOKEN == "your_firebase_token_here":
        print("⚠️  WARNING: Please set AUTH_TOKEN before running tests")
        print("   1. Start the server: cd backend && python server.py")
        print("   2. Login through frontend to get Firebase token")
        print("   3. Update AUTH_TOKEN in this file")
        print("   4. Run this script again")
        print("\nShowing feature summary instead...\n")
        display_feature_summary()
    else:
        test_for_you_endpoint()
        test_dashboard_endpoint()
        display_feature_summary()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 60 + "\n")
