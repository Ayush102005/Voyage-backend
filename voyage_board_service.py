"""
Voyage Board Service - Collaborative Planning
Feature 20: Real-time collaborative itinerary planning

This service handles:
- Creating shareable Voyage Boards
- Managing members and permissions
- Comments and suggestions
- Voting system
- Activity tracking
"""

from typing import Optional, List, Dict
from datetime import datetime
import secrets
import string
from schemas import (
    VoyageBoard,
    VoyageBoardMember,
    VoyageBoardComment,
    VoyageBoardSuggestion,
    VoyageBoardActivityUpdate,
    VoyageBoardPoll,
    VoyageBoardPollOption
)


class VoyageBoardService:
    """
    Service for managing collaborative Voyage Boards
    """
    
    def __init__(self, firestore_service):
        """
        Initialize with Firestore service for persistence
        """
        self.firestore = firestore_service
        self.collection = "voyage_boards"
    
    # =========================================================================
    # Board Creation & Management
    # =========================================================================
    
    def generate_board_id(self) -> str:
        """
        Generate a unique, human-readable board ID
        Format: VOYAGE-XXXXX (e.g., VOYAGE-A7K3M)
        """
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(secrets.choice(chars) for _ in range(5))
        return f"VOYAGE-{random_part}"
    
    def generate_share_link(self, board_id: str, base_url: str = "https://voyage.in") -> str:
        """
        Generate shareable link for a board
        """
        return f"{base_url}/board/{board_id}"
    
    def generate_access_code(self) -> str:
        """
        Generate 4-digit access code for private boards
        """
        return ''.join(secrets.choice(string.digits) for _ in range(4))
    
    def create_board(
        self,
        trip_id: str,
        owner_id: str,
        owner_email: str,
        owner_name: str,
        board_name: str,
        description: Optional[str] = None,
        is_public: bool = False,
        access_code: Optional[str] = None
    ) -> VoyageBoard:
        """
        Create a new Voyage Board for collaborative planning
        """
        board_id = self.generate_board_id()
        share_link = self.generate_share_link(board_id)
        
        # Generate access code if private and none provided
        if not is_public and not access_code:
            access_code = self.generate_access_code()
        
        # Create owner as first member
        owner_member = VoyageBoardMember(
            user_id=owner_id,
            email=owner_email,
            name=owner_name,
            role="owner",
            joined_at=datetime.now(),
            is_online=True,
            last_seen=datetime.now()
        )
        
        # Create board
        board = VoyageBoard(
            board_id=board_id,
            trip_id=trip_id,
            owner_id=owner_id,
            board_name=board_name,
            description=description,
            share_link=share_link,
            is_public=is_public,
            access_code=access_code,
            members=[owner_member],
            comments=[],
            suggestions=[],
            activity_log=[{
                "type": "board_created",
                "user_id": owner_id,
                "user_name": owner_name,
                "timestamp": datetime.now().isoformat(),
                "data": {"board_name": board_name}
            }],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            view_count=0
        )
        
        # Save to Firestore
        board_dict = board.model_dump(mode='json')
        self.firestore.db.collection(self.collection).document(board_id).set(board_dict)
        
        return board
    
    def get_board(self, board_id: str) -> Optional[VoyageBoard]:
        """
        Retrieve a Voyage Board by ID
        """
        doc = self.firestore.db.collection(self.collection).document(board_id).get()
        
        if not doc.exists:
            return None
        
        board_data = doc.to_dict()
        
        # Helper function to convert datetime (handles both str and datetime objects)
        def to_datetime(value):
            if value is None:
                return None
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            return value
        
        # Convert datetime strings back to datetime objects
        board_data['created_at'] = to_datetime(board_data['created_at'])
        board_data['updated_at'] = to_datetime(board_data['updated_at'])
        
        # Convert members
        for member in board_data.get('members', []):
            member['joined_at'] = to_datetime(member['joined_at'])
            if member.get('last_seen'):
                member['last_seen'] = to_datetime(member['last_seen'])
        
        # Convert comments
        for comment in board_data.get('comments', []):
            comment['created_at'] = to_datetime(comment['created_at'])
            if comment.get('updated_at'):
                comment['updated_at'] = to_datetime(comment['updated_at'])
        
        # Convert suggestions
        for suggestion in board_data.get('suggestions', []):
            suggestion['created_at'] = to_datetime(suggestion['created_at'])
            if suggestion.get('resolved_at'):
                suggestion['resolved_at'] = to_datetime(suggestion['resolved_at'])
        
        # Convert polls
        for poll in board_data.get('polls', []):
            poll['created_at'] = to_datetime(poll['created_at'])
        
        return VoyageBoard(**board_data)
    
    def get_board_by_trip_id(self, trip_id: str) -> Optional[VoyageBoard]:
        """
        Get a board by trip_id (since one trip can have one board)
        """
        boards_ref = self.firestore.db.collection(self.collection)
        query = boards_ref.where('trip_id', '==', trip_id).limit(1)
        docs = query.stream()
        
        for doc in docs:
            board_data = doc.to_dict()
            
            # Helper function to convert datetime
            def to_datetime(value):
                if value is None:
                    return None
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    return datetime.fromisoformat(value)
                return value
            
            # Convert datetime fields
            board_data['created_at'] = to_datetime(board_data['created_at'])
            board_data['updated_at'] = to_datetime(board_data['updated_at'])
            
            # Convert member timestamps
            for member in board_data.get('members', []):
                member['joined_at'] = to_datetime(member['joined_at'])
                member['last_seen'] = to_datetime(member['last_seen'])
            
            # Convert comments
            for comment in board_data.get('comments', []):
                comment['created_at'] = to_datetime(comment['created_at'])
            
            # Convert suggestions
            for suggestion in board_data.get('suggestions', []):
                suggestion['created_at'] = to_datetime(suggestion['created_at'])
                if suggestion.get('resolved_at'):
                    suggestion['resolved_at'] = to_datetime(suggestion['resolved_at'])
            
            # Convert polls
            for poll in board_data.get('polls', []):
                poll['created_at'] = to_datetime(poll['created_at'])
            
            return VoyageBoard(**board_data)
        
        return None
    
    def update_board(self, board: VoyageBoard) -> bool:
        """
        Update a Voyage Board in Firestore
        """
        board.updated_at = datetime.now()
        board_dict = board.model_dump(mode='json')
        
        self.firestore.db.collection(self.collection).document(board.board_id).set(board_dict)
        return True
    
    def increment_view_count(self, board_id: str):
        """
        Increment view count when someone accesses the board
        """
        doc_ref = self.firestore.db.collection(self.collection).document(board_id)
        doc = doc_ref.get()
        
        if doc.exists:
            current_count = doc.to_dict().get('view_count', 0)
            doc_ref.update({'view_count': current_count + 1})
    
    # =========================================================================
    # Member Management
    # =========================================================================
    
    def add_member(
        self,
        board_id: str,
        user_id: str,
        email: str,
        name: Optional[str] = None,
        role: str = "viewer"
    ) -> Optional[VoyageBoard]:
        """
        Add a member to the board
        """
        board = self.get_board(board_id)
        
        if not board:
            return None
        
        # Check if already a member
        if any(m.user_id == user_id for m in board.members):
            return board
        
        # Add new member
        new_member = VoyageBoardMember(
            user_id=user_id,
            email=email,
            name=name or email.split('@')[0],
            role=role,
            joined_at=datetime.now(),
            is_online=True,
            last_seen=datetime.now()
        )
        
        board.members.append(new_member)
        
        # Log activity
        board.activity_log.append({
            "type": "member_joined",
            "user_id": user_id,
            "user_name": new_member.name,
            "timestamp": datetime.now().isoformat(),
            "data": {"role": role}
        })
        
        self.update_board(board)
        return board
    
    def update_member_status(
        self,
        board_id: str,
        user_id: str,
        is_online: bool
    ) -> Optional[VoyageBoard]:
        """
        Update member's online status
        """
        board = self.get_board(board_id)
        
        if not board:
            return None
        
        for member in board.members:
            if member.user_id == user_id:
                member.is_online = is_online
                member.last_seen = datetime.now()
                break
        
        self.update_board(board)
        return board
    
    def get_member_role(self, board: VoyageBoard, user_id: str) -> Optional[str]:
        """
        Get a member's role on the board
        """
        for member in board.members:
            if member.user_id == user_id:
                return member.role
        return None
    
    def can_edit(self, board: VoyageBoard, user_id: str) -> bool:
        """
        Check if user can edit the board
        """
        role = self.get_member_role(board, user_id)
        return role in ["owner", "editor"]
    
    def is_owner(self, board: VoyageBoard, user_id: str) -> bool:
        """
        Check if user is the board owner
        """
        return board.owner_id == user_id
    
    # =========================================================================
    # Comments
    # =========================================================================
    
    def add_comment(
        self,
        board_id: str,
        user_id: str,
        user_name: str,
        content: str,
        day_number: Optional[int] = None,
        activity_index: Optional[int] = None,
        reply_to: Optional[str] = None,
        user_avatar: Optional[str] = None
    ) -> Optional[VoyageBoardComment]:
        """
        Add a comment to the board
        """
        board = self.get_board(board_id)
        
        if not board or not board.allow_comments:
            return None
        
        # Generate comment ID
        comment_id = f"comment_{secrets.token_urlsafe(8)}"
        
        # Create comment
        comment = VoyageBoardComment(
            comment_id=comment_id,
            user_id=user_id,
            user_name=user_name,
            user_avatar=user_avatar,
            content=content,
            day_number=day_number,
            activity_index=activity_index,
            created_at=datetime.now(),
            likes=[],
            replies=[]
        )
        
        board.comments.append(comment)
        
        # If reply, add to parent's replies list
        if reply_to:
            for c in board.comments:
                if c.comment_id == reply_to:
                    c.replies.append(comment_id)
                    break
        
        # Log activity
        location = "general"
        if day_number is not None:
            location = f"Day {day_number}"
            if activity_index is not None:
                location += f", Activity {activity_index + 1}"
        
        board.activity_log.append({
            "type": "comment_added",
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "comment_id": comment_id,
                "location": location,
                "preview": content[:50]
            }
        })
        
        self.update_board(board)
        return comment
    
    def like_comment(
        self,
        board_id: str,
        comment_id: str,
        user_id: str
    ) -> Optional[VoyageBoard]:
        """
        Toggle like on a comment
        """
        board = self.get_board(board_id)
        
        if not board:
            return None
        
        for comment in board.comments:
            if comment.comment_id == comment_id:
                if user_id in comment.likes:
                    comment.likes.remove(user_id)
                else:
                    comment.likes.append(user_id)
                break
        
        self.update_board(board)
        return board
    
    # =========================================================================
    # Suggestions & Voting
    # =========================================================================
    
    def add_suggestion(
        self,
        board_id: str,
        user_id: str,
        user_name: str,
        suggestion_type: str,
        suggested_value: str,
        day_number: Optional[int] = None,
        activity_index: Optional[int] = None,
        current_value: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Optional[VoyageBoardSuggestion]:
        """
        Add a suggestion to the board
        """
        board = self.get_board(board_id)
        
        if not board or not board.allow_suggestions:
            return None
        
        # Generate suggestion ID
        suggestion_id = f"suggestion_{secrets.token_urlsafe(8)}"
        
        # Create suggestion
        suggestion = VoyageBoardSuggestion(
            suggestion_id=suggestion_id,
            user_id=user_id,
            user_name=user_name,
            suggestion_type=suggestion_type,
            day_number=day_number,
            activity_index=activity_index,
            current_value=current_value,
            suggested_value=suggested_value,
            reason=reason,
            created_at=datetime.now(),
            votes={user_id: "up"},  # Creator auto-votes up
            status="pending"
        )
        
        board.suggestions.append(suggestion)
        
        # Log activity
        location = f"Day {day_number}" if day_number else "General"
        
        board.activity_log.append({
            "type": "suggestion_added",
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "suggestion_id": suggestion_id,
                "type": suggestion_type,
                "location": location,
                "preview": suggested_value[:50]
            }
        })
        
        self.update_board(board)
        return suggestion
    
    def vote_on_suggestion(
        self,
        board_id: str,
        suggestion_id: str,
        user_id: str,
        vote: str  # "up", "down", or "neutral"
    ) -> Optional[VoyageBoard]:
        """
        Vote on a suggestion
        """
        board = self.get_board(board_id)
        
        if not board:
            return None
        
        for suggestion in board.suggestions:
            if suggestion.suggestion_id == suggestion_id:
                if vote == "neutral" and user_id in suggestion.votes:
                    del suggestion.votes[user_id]
                else:
                    suggestion.votes[user_id] = vote
                break
        
        self.update_board(board)
        return board
    
    def resolve_suggestion(
        self,
        board_id: str,
        suggestion_id: str,
        user_id: str,
        action: str  # "accept" or "reject"
    ) -> Optional[VoyageBoard]:
        """
        Accept or reject a suggestion (owner only)
        """
        board = self.get_board(board_id)
        
        if not board or not self.is_owner(board, user_id):
            return None
        
        for suggestion in board.suggestions:
            if suggestion.suggestion_id == suggestion_id:
                suggestion.status = "accepted" if action == "accept" else "rejected"
                suggestion.resolved_by = user_id
                suggestion.resolved_at = datetime.now()
                
                # Log activity
                board.activity_log.append({
                    "type": f"suggestion_{action}ed",
                    "user_id": user_id,
                    "user_name": next((m.name for m in board.members if m.user_id == user_id), "Unknown"),
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "suggestion_id": suggestion_id,
                        "suggester": suggestion.user_name
                    }
                })
                break
        
        self.update_board(board)
        return board
    
    def get_suggestion_vote_count(self, suggestion: VoyageBoardSuggestion) -> Dict[str, int]:
        """
        Count votes on a suggestion
        """
        upvotes = sum(1 for vote in suggestion.votes.values() if vote == "up")
        downvotes = sum(1 for vote in suggestion.votes.values() if vote == "down")
        
        return {
            "upvotes": upvotes,
            "downvotes": downvotes,
            "total": len(suggestion.votes),
            "score": upvotes - downvotes
        }
    
    # =========================================================================
    # Polls
    # =========================================================================
    
    def create_poll(
        self,
        board_id: str,
        user_id: str,
        user_name: str,
        question: str,
        options: List[str],
        allow_multiple: bool = False
    ) -> Optional[VoyageBoardPoll]:
        """
        Create a new poll on the board
        """
        board = self.get_board(board_id)
        
        if not board:
            return None
        
        # Generate poll and option IDs
        poll_id = f"poll_{secrets.token_urlsafe(8)}"
        
        # Create poll options
        poll_options = []
        for idx, option_text in enumerate(options):
            option = VoyageBoardPollOption(
                option_id=f"opt_{poll_id}_{idx}",
                option_text=option_text,
                votes=[]
            )
            poll_options.append(option)
        
        # Create poll
        poll = VoyageBoardPoll(
            poll_id=poll_id,
            question=question,
            options=poll_options,
            created_by=user_id,
            created_by_name=user_name,
            created_at=datetime.now(),
            allow_multiple=allow_multiple,
            is_closed=False
        )
        
        board.polls.append(poll)
        
        # Log activity
        board.activity_log.append({
            "type": "poll_created",
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "poll_id": poll_id,
                "question": question[:50],
                "option_count": len(options)
            }
        })
        
        self.update_board(board)
        return poll
    
    def vote_on_poll(
        self,
        board_id: str,
        poll_id: str,
        option_id: str,
        user_id: str
    ) -> Optional[VoyageBoard]:
        """
        Vote on a poll option
        If allow_multiple is False, removes previous votes from other options
        """
        board = self.get_board(board_id)
        
        if not board:
            return None
        
        for poll in board.polls:
            if poll.poll_id == poll_id:
                if poll.is_closed:
                    return None  # Poll is closed
                
                # If not allowing multiple votes, remove user's vote from other options
                if not poll.allow_multiple:
                    for option in poll.options:
                        if user_id in option.votes:
                            option.votes.remove(user_id)
                
                # Add vote to selected option (toggle if already voted for this option)
                for option in poll.options:
                    if option.option_id == option_id:
                        if user_id in option.votes:
                            option.votes.remove(user_id)  # Toggle off
                        else:
                            option.votes.append(user_id)  # Vote
                        break
                
                break
        
        self.update_board(board)
        return board
    
    def close_poll(
        self,
        board_id: str,
        poll_id: str,
        user_id: str
    ) -> Optional[VoyageBoard]:
        """
        Close a poll (creator or owner only)
        """
        board = self.get_board(board_id)
        
        if not board:
            return None
        
        for poll in board.polls:
            if poll.poll_id == poll_id:
                # Check if user is creator or board owner
                if user_id == poll.created_by or user_id == board.owner_id:
                    poll.is_closed = True
                break
        
        self.update_board(board)
        return board
    
    # =========================================================================
    # Activity & Analytics
    # =========================================================================
    
    def get_board_stats(self, board: VoyageBoard) -> Dict:
        """
        Get statistics about the board
        """
        pending_suggestions = [s for s in board.suggestions if s.status == "pending"]
        accepted_suggestions = [s for s in board.suggestions if s.status == "accepted"]
        
        return {
            "total_members": len(board.members),
            "online_members": sum(1 for m in board.members if m.is_online),
            "total_comments": len(board.comments),
            "total_suggestions": len(board.suggestions),
            "pending_suggestions": len(pending_suggestions),
            "accepted_suggestions": len(accepted_suggestions),
            "view_count": board.view_count,
            "last_activity": board.updated_at
        }
    
    def get_user_boards(self, user_id: str) -> List[VoyageBoard]:
        """
        Get all boards where user is a member
        """
        boards = []
        
        # Helper function to convert datetime (handles both str and datetime objects)
        def to_datetime(value):
            if value is None:
                return None
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            return value
        
        # Query Firestore for boards where user is a member
        docs = self.firestore.db.collection(self.collection).stream()
        
        for doc in docs:
            board_data = doc.to_dict()
            
            # Check if user is a member
            is_member = any(
                m.get('user_id') == user_id 
                for m in board_data.get('members', [])
            )
            
            if is_member:
                # Convert to VoyageBoard object
                board_data['created_at'] = to_datetime(board_data['created_at'])
                board_data['updated_at'] = to_datetime(board_data['updated_at'])
                
                for member in board_data.get('members', []):
                    member['joined_at'] = to_datetime(member['joined_at'])
                    if member.get('last_seen'):
                        member['last_seen'] = to_datetime(member['last_seen'])
                
                for comment in board_data.get('comments', []):
                    comment['created_at'] = to_datetime(comment['created_at'])
                    if comment.get('updated_at'):
                        comment['updated_at'] = to_datetime(comment['updated_at'])
                
                for suggestion in board_data.get('suggestions', []):
                    suggestion['created_at'] = to_datetime(suggestion['created_at'])
                    if suggestion.get('resolved_at'):
                        suggestion['resolved_at'] = to_datetime(suggestion['resolved_at'])
                
                for poll in board_data.get('polls', []):
                    poll['created_at'] = to_datetime(poll['created_at'])
                
                boards.append(VoyageBoard(**board_data))
        
        return boards


# Singleton instance
_voyage_board_service = None

def get_voyage_board_service(firestore_service):
    """Get singleton instance of VoyageBoardService"""
    global _voyage_board_service
    if _voyage_board_service is None:
        _voyage_board_service = VoyageBoardService(firestore_service)
    return _voyage_board_service
