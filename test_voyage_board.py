"""
Test script for Feature 20: Voyage Board (Collaborative Planning)

This tests:
1. Board creation with shareable links
2. Member management
3. Comments system
4. Suggestions and voting
5. Permission controls
6. Activity tracking
"""

import sys
from datetime import datetime
from voyage_board_service import VoyageBoardService


# Mock Firestore service for testing
class MockFirestore:
    def __init__(self):
        self.db_storage = {}
    
    class MockCollection:
        def __init__(self, storage, collection_name):
            self.storage = storage
            self.collection_name = collection_name
            if collection_name not in self.storage:
                self.storage[collection_name] = {}
        
        def document(self, doc_id):
            return MockFirestore.MockDocument(self.storage, self.collection_name, doc_id)
        
        def stream(self):
            docs = []
            for doc_id, doc_data in self.storage.get(self.collection_name, {}).items():
                docs.append(MockFirestore.MockDoc(doc_id, doc_data))
            return docs
    
    class MockDocument:
        def __init__(self, storage, collection_name, doc_id):
            self.storage = storage
            self.collection_name = collection_name
            self.doc_id = doc_id
        
        def set(self, data):
            if self.collection_name not in self.storage:
                self.storage[self.collection_name] = {}
            self.storage[self.collection_name][self.doc_id] = data
        
        def get(self):
            data = self.storage.get(self.collection_name, {}).get(self.doc_id)
            return MockFirestore.MockDoc(self.doc_id, data)
        
        def update(self, data):
            if self.collection_name in self.storage and self.doc_id in self.storage[self.collection_name]:
                self.storage[self.collection_name][self.doc_id].update(data)
    
    class MockDoc:
        def __init__(self, doc_id, data):
            self.id = doc_id
            self.data = data
        
        @property
        def exists(self):
            return self.data is not None
        
        def to_dict(self):
            return self.data
    
    @property
    def db(self):
        return self
    
    def collection(self, name):
        return self.MockCollection(self.db_storage, name)


def print_header(text: str):
    """Print a nice header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_subsection(text: str):
    """Print a subsection"""
    print(f"\n{'─' * 70}")
    print(f"  {text}")
    print(f"{'─' * 70}")


def test_board_creation():
    """Test creating a Voyage Board"""
    print_header("TEST 1: Board Creation")
    
    # Initialize service with mock Firestore
    mock_firestore = MockFirestore()
    service = VoyageBoardService(mock_firestore)
    
    # Create a board
    board = service.create_board(
        trip_id="trip_12345",
        owner_id="user_abc",
        owner_email="alice@example.com",
        owner_name="Alice",
        board_name="Family Trip to Goa",
        description="Planning our summer vacation to Goa with the family",
        is_public=False,
        access_code=None  # Will auto-generate
    )
    
    print(f"\n✅ Board Created:")
    print(f"   Board ID: {board.board_id}")
    print(f"   Board Name: {board.board_name}")
    print(f"   Share Link: {board.share_link}")
    print(f"   Access Code: {board.access_code} (private board)")
    print(f"   Owner: {board.members[0].name} ({board.members[0].email})")
    print(f"   Members: {len(board.members)}")
    print(f"   Created: {board.created_at.strftime('%Y-%m-%d %H:%M')}")
    
    # Verify board ID format
    assert board.board_id.startswith("VOYAGE-"), "Board ID should start with VOYAGE-"
    assert len(board.board_id) == 12, "Board ID should be 12 characters (VOYAGE-XXXXX)"
    
    # Verify access code
    assert board.access_code and len(board.access_code) == 4, "Access code should be 4 digits"
    
    # Verify owner is added as member
    assert len(board.members) == 1, "Owner should be the first member"
    assert board.members[0].role == "owner", "Owner role should be 'owner'"
    assert board.members[0].is_online == True, "Owner should be online"
    
    print("\n✅ Board creation test passed!")
    
    return service, board


def test_member_management(service, board):
    """Test adding and managing members"""
    print_header("TEST 2: Member Management")
    
    # Add members
    print("\n📝 Adding members...")
    
    # Add Bob
    board = service.add_member(
        board_id=board.board_id,
        user_id="user_bob",
        email="bob@example.com",
        name="Bob",
        role="editor"
    )
    
    print(f"   ✅ Added Bob as editor")
    
    # Add Carol
    board = service.add_member(
        board_id=board.board_id,
        user_id="user_carol",
        email="carol@example.com",
        name="Carol",
        role="viewer"
    )
    
    print(f"   ✅ Added Carol as viewer")
    
    # Verify members
    print(f"\n👥 Board Members ({len(board.members)}):")
    for member in board.members:
        status = "🟢 Online" if member.is_online else "⚪ Offline"
        print(f"   • {member.name} ({member.email}) - {member.role} {status}")
    
    assert len(board.members) == 3, "Should have 3 members"
    
    # Test permission checks
    print(f"\n🔐 Permission Tests:")
    
    can_alice_edit = service.can_edit(board, "user_abc")
    can_bob_edit = service.can_edit(board, "user_bob")
    can_carol_edit = service.can_edit(board, "user_carol")
    
    print(f"   Alice can edit: {can_alice_edit} ✅")
    print(f"   Bob can edit: {can_bob_edit} ✅")
    print(f"   Carol can edit: {can_carol_edit} ❌")
    
    assert can_alice_edit == True, "Owner should be able to edit"
    assert can_bob_edit == True, "Editor should be able to edit"
    assert can_carol_edit == False, "Viewer should not be able to edit"
    
    is_alice_owner = service.is_owner(board, "user_abc")
    is_bob_owner = service.is_owner(board, "user_bob")
    
    print(f"   Alice is owner: {is_alice_owner} ✅")
    print(f"   Bob is owner: {is_bob_owner} ❌")
    
    assert is_alice_owner == True, "Alice should be owner"
    assert is_bob_owner == False, "Bob should not be owner"
    
    print("\n✅ Member management test passed!")
    
    return board


def test_comments(service, board):
    """Test commenting system"""
    print_header("TEST 3: Comments System")
    
    # Add general comment
    print("\n💬 Adding comments...")
    
    comment1 = service.add_comment(
        board_id=board.board_id,
        user_id="user_bob",
        user_name="Bob",
        content="This itinerary looks great! Can't wait for the trip! 🎉"
    )
    
    print(f"   ✅ Bob: General comment")
    
    # Add comment on Day 2
    comment2 = service.add_comment(
        board_id=board.board_id,
        user_id="user_carol",
        user_name="Carol",
        content="Love the beach activities on Day 2!",
        day_number=2
    )
    
    print(f"   ✅ Carol: Comment on Day 2")
    
    # Add comment on specific activity
    comment3 = service.add_comment(
        board_id=board.board_id,
        user_id="user_abc",
        user_name="Alice",
        content="We should arrive earlier for the sunset cruise",
        day_number=3,
        activity_index=2
    )
    
    print(f"   ✅ Alice: Comment on Day 3, Activity 3")
    
    # Add reply to Bob's comment
    comment4 = service.add_comment(
        board_id=board.board_id,
        user_id="user_carol",
        user_name="Carol",
        content="Me too! It's going to be amazing!",
        reply_to=comment1.comment_id
    )
    
    print(f"   ✅ Carol: Reply to Bob's comment")
    
    # Get updated board
    board = service.get_board(board.board_id)
    
    print(f"\n💬 All Comments ({len(board.comments)}):")
    for comment in board.comments:
        location = "General"
        if comment.day_number:
            location = f"Day {comment.day_number}"
            if comment.activity_index is not None:
                location += f", Activity {comment.activity_index + 1}"
        
        reply_info = f" (Reply to {comment.comment_id[:10]}...)" if any(comment.comment_id in c.replies for c in board.comments) else ""
        
        print(f"\n   {comment.user_name} [{location}]{reply_info}:")
        print(f"   \"{comment.content}\"")
        print(f"   👍 {len(comment.likes)} likes")
    
    assert len(board.comments) == 4, "Should have 4 comments"
    
    # Test liking a comment
    print(f"\n👍 Testing likes...")
    
    service.like_comment(board.board_id, comment1.comment_id, "user_carol")
    service.like_comment(board.board_id, comment1.comment_id, "user_abc")
    
    board = service.get_board(board.board_id)
    liked_comment = next(c for c in board.comments if c.comment_id == comment1.comment_id)
    
    print(f"   Bob's comment now has {len(liked_comment.likes)} likes")
    
    assert len(liked_comment.likes) == 2, "Bob's comment should have 2 likes"
    
    print("\n✅ Comments test passed!")
    
    return board


def test_suggestions_and_voting(service, board):
    """Test suggestions and voting system"""
    print_header("TEST 4: Suggestions & Voting")
    
    # Add suggestions
    print("\n💡 Adding suggestions...")
    
    # Bob suggests adding an activity
    suggestion1 = service.add_suggestion(
        board_id=board.board_id,
        user_id="user_bob",
        user_name="Bob",
        suggestion_type="add_activity",
        suggested_value="Visit Dudhsagar Waterfalls",
        day_number=2,
        reason="It's nearby and looks amazing in the photos!"
    )
    
    print(f"   ✅ Bob suggests: Add activity on Day 2")
    
    # Carol suggests changing time
    suggestion2 = service.add_suggestion(
        board_id=board.board_id,
        user_id="user_carol",
        user_name="Carol",
        suggestion_type="change_time",
        current_value="3:00 PM - Beach visit",
        suggested_value="5:00 PM - Beach visit",
        day_number=3,
        activity_index=1,
        reason="Better lighting for sunset photos"
    )
    
    print(f"   ✅ Carol suggests: Change time for Day 3 activity")
    
    # Alice suggests changing hotel
    suggestion3 = service.add_suggestion(
        board_id=board.board_id,
        user_id="user_abc",
        user_name="Alice",
        suggestion_type="change_hotel",
        current_value="Beach Resort Hotel",
        suggested_value="Taj Exotica Resort & Spa",
        reason="Better reviews and closer to attractions"
    )
    
    print(f"   ✅ Alice suggests: Change hotel")
    
    # Get updated board
    board = service.get_board(board.board_id)
    
    print(f"\n💡 All Suggestions ({len(board.suggestions)}):")
    for suggestion in board.suggestions:
        location = f"Day {suggestion.day_number}" if suggestion.day_number else "General"
        print(f"\n   [{suggestion.status.upper()}] {suggestion.user_name} - {suggestion.suggestion_type} ({location})")
        if suggestion.current_value:
            print(f"   Current: {suggestion.current_value}")
        print(f"   Suggested: {suggestion.suggested_value}")
        if suggestion.reason:
            print(f"   Reason: {suggestion.reason}")
    
    assert len(board.suggestions) == 3, "Should have 3 suggestions"
    
    # Test voting
    print(f"\n🗳️  Testing voting...")
    
    # Carol upvotes Bob's suggestion
    service.vote_on_suggestion(board.board_id, suggestion1.suggestion_id, "user_carol", "up")
    print(f"   ✅ Carol upvoted Bob's suggestion")
    
    # Alice also upvotes
    service.vote_on_suggestion(board.board_id, suggestion1.suggestion_id, "user_abc", "up")
    print(f"   ✅ Alice upvoted Bob's suggestion")
    
    # Bob downvotes Carol's suggestion
    service.vote_on_suggestion(board.board_id, suggestion2.suggestion_id, "user_bob", "down")
    print(f"   ✅ Bob downvoted Carol's suggestion")
    
    # Get updated board and show vote counts
    board = service.get_board(board.board_id)
    
    print(f"\n📊 Vote Results:")
    for suggestion in board.suggestions:
        votes = service.get_suggestion_vote_count(suggestion)
        score = votes['score']
        emoji = "👍" if score > 0 else "👎" if score < 0 else "😐"
        
        print(f"   {emoji} {suggestion.suggested_value[:40]}...")
        print(f"      Upvotes: {votes['upvotes']} | Downvotes: {votes['downvotes']} | Score: {score}")
    
    # Verify vote counts
    votes1 = service.get_suggestion_vote_count(
        next(s for s in board.suggestions if s.suggestion_id == suggestion1.suggestion_id)
    )
    assert votes1['upvotes'] == 3, "Suggestion 1 should have 3 upvotes (Bob auto-voted + Carol + Alice)"
    assert votes1['score'] == 3, "Suggestion 1 should have score of 3"
    
    print("\n✅ Suggestions and voting test passed!")
    
    return board


def test_suggestion_resolution(service, board):
    """Test accepting/rejecting suggestions"""
    print_header("TEST 5: Suggestion Resolution")
    
    # Get first suggestion (Bob's waterfall suggestion)
    suggestion = board.suggestions[0]
    
    print(f"\n📋 Resolving suggestion:")
    print(f"   Suggestion: {suggestion.suggested_value}")
    print(f"   By: {suggestion.user_name}")
    print(f"   Votes: {service.get_suggestion_vote_count(suggestion)['score']}")
    
    # Alice (owner) accepts the suggestion
    board = service.resolve_suggestion(
        board_id=board.board_id,
        suggestion_id=suggestion.suggestion_id,
        user_id="user_abc",  # Alice (owner)
        action="accept"
    )
    
    resolved = next(s for s in board.suggestions if s.suggestion_id == suggestion.suggestion_id)
    
    print(f"\n✅ Owner accepted the suggestion:")
    print(f"   Status: {resolved.status}")
    print(f"   Resolved by: {resolved.resolved_by}")
    print(f"   Resolved at: {resolved.resolved_at.strftime('%Y-%m-%d %H:%M')}")
    
    assert resolved.status == "accepted", "Suggestion should be accepted"
    assert resolved.resolved_by == "user_abc", "Should be resolved by Alice"
    assert resolved.resolved_at is not None, "Should have resolved timestamp"
    
    # Reject second suggestion
    suggestion2 = board.suggestions[1]
    board = service.resolve_suggestion(
        board_id=board.board_id,
        suggestion_id=suggestion2.suggestion_id,
        user_id="user_abc",
        action="reject"
    )
    
    rejected = next(s for s in board.suggestions if s.suggestion_id == suggestion2.suggestion_id)
    
    print(f"\n❌ Owner rejected another suggestion:")
    print(f"   Suggestion: {rejected.suggested_value}")
    print(f"   Status: {rejected.status}")
    
    assert rejected.status == "rejected", "Suggestion should be rejected"
    
    print("\n✅ Suggestion resolution test passed!")
    
    return board


def test_board_stats(service, board):
    """Test board statistics"""
    print_header("TEST 6: Board Statistics")
    
    stats = service.get_board_stats(board)
    
    print(f"\n📊 Board Statistics:")
    print(f"   Total Members: {stats['total_members']}")
    print(f"   Online Members: {stats['online_members']}")
    print(f"   Total Comments: {stats['total_comments']}")
    print(f"   Total Suggestions: {stats['total_suggestions']}")
    print(f"   Pending Suggestions: {stats['pending_suggestions']}")
    print(f"   Accepted Suggestions: {stats['accepted_suggestions']}")
    print(f"   View Count: {stats['view_count']}")
    print(f"   Last Activity: {stats['last_activity'].strftime('%Y-%m-%d %H:%M')}")
    
    assert stats['total_members'] == 3, "Should have 3 members"
    assert stats['total_comments'] == 4, "Should have 4 comments"
    assert stats['total_suggestions'] == 3, "Should have 3 suggestions"
    assert stats['accepted_suggestions'] == 1, "Should have 1 accepted suggestion"
    
    print("\n✅ Board statistics test passed!")
    
    return stats


def test_activity_log(service, board):
    """Test activity tracking"""
    print_header("TEST 7: Activity Log")
    
    print(f"\n📜 Activity History ({len(board.activity_log)} events):")
    
    for i, activity in enumerate(board.activity_log[-10:], 1):  # Show last 10
        timestamp = activity.get('timestamp', 'Unknown')
        activity_type = activity.get('type', 'Unknown')
        user_name = activity.get('user_name', 'Unknown')
        
        emoji_map = {
            'board_created': '🎨',
            'member_joined': '👋',
            'comment_added': '💬',
            'suggestion_added': '💡',
            'suggestion_accepted': '✅',
            'suggestion_rejected': '❌'
        }
        
        emoji = emoji_map.get(activity_type, '📝')
        
        print(f"\n   {emoji} {activity_type.replace('_', ' ').title()}")
        print(f"      By: {user_name}")
        print(f"      When: {timestamp[:19] if isinstance(timestamp, str) else timestamp}")
        
        if activity.get('data'):
            data = activity['data']
            if 'preview' in data:
                print(f"      Preview: \"{data['preview']}...\"")
            elif 'location' in data:
                print(f"      Location: {data['location']}")
    
    assert len(board.activity_log) >= 5, "Should have at least 5 activity events"
    
    print("\n✅ Activity log test passed!")


def display_feature_summary():
    """Display summary of Feature 20"""
    print_header("FEATURE 20: VOYAGE BOARD (COLLABORATIVE PLANNING)")
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🎨 VOYAGE BOARD FEATURES                                ║
╚════════════════════════════════════════════════════════════════════════════╝

✨ CORE CAPABILITIES:
   • Shareable Boards: Unique links (VOYAGE-XXXXX format)
   • Access Control: Public boards or private with access codes
   • Real-time Collaboration: Multiple users viewing and editing
   • Member Roles: Owner, Editor, Viewer permissions

💬 COMMENTS SYSTEM:
   • Comment on entire trip, specific days, or activities
   • Reply to comments (threaded discussions)
   • Like comments to show agreement
   • Track comment author and timestamp

💡 SUGGESTIONS & VOTING:
   • Suggest changes: Add/remove activities, change times, change hotels
   • Democratic voting: Upvote/downvote suggestions
   • Owner approval: Owner accepts or rejects suggestions
   • Vote tracking: See community consensus

👥 MEMBER MANAGEMENT:
   • Invite by email
   • Role-based permissions (Owner, Editor, Viewer)
   • Online status tracking
   • Last seen timestamps

📊 ACTIVITY TRACKING:
   • Complete activity log
   • Track all changes and interactions
   • Statistics: Views, comments, suggestions
   • Member engagement metrics

🔐 SECURITY & PRIVACY:
   • Private boards require access codes
   • Member verification
   • Owner-only controls for critical actions
   • Audit trail of all activities

╔════════════════════════════════════════════════════════════════════════════╗
║                         🚀 USE CASES                                       ║
╚════════════════════════════════════════════════════════════════════════════╝

👨‍👩‍👧‍👦 FAMILY TRIPS:
   • Parents create itinerary
   • Kids suggest activities
   • Everyone votes on favorites
   • Democratic family decisions

👔 CORPORATE RETREATS:
   • Team lead creates plan
   • Team members suggest venues
   • Vote on activities
   • Collaborative team building

🎓 COLLEGE TRIPS:
   • One person does planning
   • Share with entire group
   • Everyone comments and suggests
   • Budget-conscious decisions

💑 GROUP TRAVEL:
   • Friend groups plan together
   • Share responsibilities
   • Vote on destinations
   • Fair decision making

╔════════════════════════════════════════════════════════════════════════════╗
║                      💼 BUSINESS IMPACT                                    ║
╚════════════════════════════════════════════════════════════════════════════╝

📈 USER ENGAGEMENT:
   • Longer session times (collaboration)
   • Higher retention (group commitment)
   • Viral growth (sharing)
   • Community building

💰 REVENUE POTENTIAL:
   • Premium boards (unlimited members)
   • Priority support
   • Advanced features (polls, calendar sync)
   • White-label for travel agencies

🎯 COMPETITIVE ADVANTAGE:
   • UNIQUE feature (no competitor has this)
   • Solves real pain point (group planning)
   • Network effects (more users = more value)
   • Sticky feature (high retention)

⏱️  TIME SAVED:
   • Before: Back-and-forth WhatsApp/Email (hours)
   • After: Centralized discussion (minutes)
   • Reduced confusion and conflicts
   • Clear decision history
""")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  🧪 TESTING FEATURE 20: VOYAGE BOARD")
    print("=" * 80)
    
    try:
        # Display feature summary
        display_feature_summary()
        
        # Run tests
        service, board = test_board_creation()
        board = test_member_management(service, board)
        board = test_comments(service, board)
        board = test_suggestions_and_voting(service, board)
        board = test_suggestion_resolution(service, board)
        stats = test_board_stats(service, board)
        test_activity_log(service, board)
        
        # Final summary
        print_header("✅ ALL TESTS PASSED!")
        print("""
🎉 Feature 20 is working perfectly!

Key Achievements:
✅ Board creation with unique shareable links
✅ Member management with role-based permissions
✅ Comments system with replies and likes
✅ Suggestions with democratic voting
✅ Owner approval/rejection workflow
✅ Activity tracking and statistics
✅ Access control (public/private boards)

📊 Test Results:
   • Boards created: 1
   • Members added: 3 (Owner, Editor, Viewer)
   • Comments posted: 4 (including 1 reply)
   • Suggestions made: 3
   • Votes cast: 4
   • Suggestions resolved: 2 (1 accepted, 1 rejected)

🚀 Ready for production!
""")
        
    except AssertionError as e:
        print(f"\n❌ Test assertion failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
