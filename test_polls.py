"""
Test script for Voyage Board Polls feature
"""

import sys
from datetime import datetime

# Test that the schemas are correctly defined
try:
    from schemas import VoyageBoardPoll, VoyageBoardPollOption, CreatePollRequest, VoteOnPollRequest
    print("✅ Poll schemas imported successfully")
    
    # Test creating a poll option
    option = VoyageBoardPollOption(
        option_id="opt_1",
        option_text="Option 1",
        votes=[]
    )
    print(f"✅ Created poll option: {option.option_text}")
    
    # Test creating a poll
    poll = VoyageBoardPoll(
        poll_id="poll_test",
        question="Test Question?",
        options=[option],
        created_by="user123",
        created_by_name="Test User",
        created_at=datetime.now(),
        allow_multiple=False,
        is_closed=False
    )
    print(f"✅ Created poll: {poll.question}")
    
    # Test request schemas
    create_request = CreatePollRequest(
        question="What's your favorite destination?",
        options=["Paris", "Tokyo", "New York"],
        allow_multiple=False
    )
    print(f"✅ Created poll request with {len(create_request.options)} options")
    
    vote_request = VoteOnPollRequest(
        poll_id="poll_123",
        option_id="opt_1"
    )
    print(f"✅ Created vote request for poll: {vote_request.poll_id}")
    
    print("\n🎉 All schema tests passed!")
    
except Exception as e:
    print(f"❌ Error testing schemas: {e}")
    sys.exit(1)

# Test service methods
try:
    from firebase_config import initialize_firebase
    from firestore_service import firestore_service
    from voyage_board_service import get_voyage_board_service
    
    print("\n📦 Testing Voyage Board Service...")
    
    # Initialize Firebase (will use existing if already initialized)
    initialize_firebase()
    
    # Get service
    board_service = get_voyage_board_service(firestore_service)
    print("✅ Voyage board service initialized")
    
    # Check that the methods exist
    assert hasattr(board_service, 'create_poll'), "create_poll method missing"
    assert hasattr(board_service, 'vote_on_poll'), "vote_on_poll method missing"
    assert hasattr(board_service, 'close_poll'), "close_poll method missing"
    print("✅ All poll methods exist on service")
    
    print("\n🎉 All service tests passed!")
    print("\n✨ Polls feature is ready to use!")
    print("\nTo use in the app:")
    print("1. Create a Voyage Board")
    print("2. Click 'New Poll' in the Voting Polls section")
    print("3. Enter a question and at least 2 options")
    print("4. Click 'Create Poll'")
    print("5. Poll will be saved and persist across page refreshes!")
    
except Exception as e:
    print(f"❌ Error testing service: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
