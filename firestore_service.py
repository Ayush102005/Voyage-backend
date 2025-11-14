from firebase_config import get_firestore_client
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
    


logger = logging.getLogger(__name__)

class FirestoreService:
    def create_user_profile(self, user_id: str, email: str, name: str = None) -> Dict[str, Any]:
        """Create a new user profile in Firestore"""
        if not self.db:
            raise Exception("Firestore not initialized")
        try:
            profile_data = {
                'email': email,
                'name': name or email.split('@')[0],
                'created_at': datetime.utcnow(),
                'preferences': {},
                'learned_preferences': {}
            }
            self.db.collection('user_profiles').document(user_id).set(profile_data)
            profile_data['id'] = user_id
            return profile_data
        except Exception as e:
            logger.error(f"Error creating user profile: {str(e)}")
            raise

    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences from Firestore users collection"""
        if not self.db:
            print(f"⚠️ Firestore not initialized")
            return None
        try:
            doc = self.db.collection('users').document(user_id).get()
            if doc.exists:
                prefs = doc.to_dict()
                print(f"✅ Found preferences for user {user_id}")
                return prefs
            else:
                print(f"ℹ️ No preferences found for user {user_id}")
            return None
        except Exception as e:
            print(f"❌ Error getting user preferences: {str(e)}")
            logger.error(f"Error getting user preferences: {str(e)}")
            return None

    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Save or update user preferences in Firestore users collection"""
        if not self.db:
            raise Exception("Firestore not initialized")
        try:
            preferences['updatedAt'] = datetime.utcnow()
            if 'createdAt' not in preferences:
                preferences['createdAt'] = datetime.utcnow()
            
            self.db.collection('users').document(user_id).set(preferences, merge=True)
            print(f"✅ Saved preferences for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving user preferences: {str(e)}")
            print(f"❌ Error saving preferences: {str(e)}")
            raise

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile data from Firestore"""
        if not self.db:
            print(f"⚠️ Firestore not initialized")
            return None
        try:
            doc = self.db.collection('user_profiles').document(user_id).get()
            if doc.exists:
                profile_data = doc.to_dict()
                profile_data['id'] = doc.id
                return profile_data
            else:
                print(f"❌ User profile {user_id} does not exist in user_profiles collection")
            return None
        except Exception as e:
            print(f"❌ Error getting user profile: {str(e)}")
            logger.error(f"Error getting user profile: {str(e)}")
            return None
    def __init__(self):
        self.db = get_firestore_client()
        print("[OK] FirestoreService initialized")
    
    def get_user_trip_plans(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all trip plans for a user"""
        if not self.db:
            return []
        try:
            trips_ref = self.db.collection('trip_plans').where('user_id', '==', user_id).limit(limit)
            trips = []
            for doc in trips_ref.stream():
                trip_data = doc.to_dict()
                trip_data['id'] = doc.id
                trips.append(trip_data)
            return trips
        except Exception as e:
            logger.error(f"Error getting user trip plans: {str(e)}")
            return []
    
    def get_trip_plan_by_id(self, trip_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific trip plan by ID"""
        if not self.db:
            print(f"⚠️ Firestore not initialized")
            return None
        try:
            print(f"🔍 Looking for trip_id: {trip_id}, user_id: {user_id}")
            doc = self.db.collection('trip_plans').document(trip_id).get()
            if doc.exists:
                print(f"✅ Document found")
                trip_data = doc.to_dict()
                trip_owner = trip_data.get('user_id')
                print(f"   Trip owner: {trip_owner}, Requesting user: {user_id}")
                if trip_owner == user_id:
                    trip_data['id'] = doc.id
                    print(f"✅ User authorized")
                    return trip_data
                else:
                    print(f"❌ User not authorized (owner: {trip_owner}, requester: {user_id})")
            else:
                print(f"❌ Document {trip_id} does not exist in trip_plans collection")
            return None
        except Exception as e:
            print(f"❌ Error getting trip plan: {str(e)}")
            logger.error(f"Error getting trip plan: {str(e)}")
            return None
    
    def save_trip_plan(self, user_id: str, trip_data: Dict[str, Any]) -> str:
        """Save a new trip plan"""
        if not self.db:
            raise Exception("Firestore not initialized")
        try:
            trip_data['user_id'] = user_id
            trip_data['created_at'] = datetime.utcnow()
            trip_data['updated_at'] = datetime.utcnow()
            trip_ref = self.db.collection('trip_plans').document()
            trip_ref.set(trip_data)
            return trip_ref.id
        except Exception as e:
            logger.error(f"Error saving trip plan: {str(e)}")
            raise
    
    def update_trip_plan(self, trip_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing trip plan"""
        if not self.db:
            return False
        try:
            updates['updated_at'] = datetime.utcnow()
            doc_ref = self.db.collection('trip_plans').document(trip_id)
            doc = doc_ref.get()
            if doc.exists and doc.to_dict().get('user_id') == user_id:
                doc_ref.update(updates)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating trip plan: {str(e)}")
            return False
    
    def delete_trip_plan(self, trip_id: str, user_id: str) -> bool:
        """Delete a trip plan"""
        if not self.db:
            return False
        try:
            doc_ref = self.db.collection('trip_plans').document(trip_id)
            doc = doc_ref.get()
            if doc.exists and doc.to_dict().get('user_id') == user_id:
                doc_ref.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting trip plan: {str(e)}")
            return False
    
    def update_trip_status(self, trip_id: str, user_id: str, status: str) -> bool:
        """Update trip status"""
        return self.update_trip_plan(trip_id, user_id, {'trip_status': status})
    
    def save_destination(self, user_id: str, destination_name: str, notes: str = None) -> str:
        """Save a destination to favorites"""
        if not self.db:
            raise Exception("Firestore not initialized")
        try:
            dest_data = {
                'user_id': user_id,
                'destination_name': destination_name,
                'notes': notes,
                'created_at': datetime.utcnow()
            }
            dest_ref = self.db.collection('saved_destinations').document()
            dest_ref.set(dest_data)
            return dest_ref.id
        except Exception as e:
            logger.error(f"Error saving destination: {str(e)}")
            raise
    
    def get_user_saved_destinations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's saved destinations"""
        if not self.db:
            return []
        try:
            dests_ref = self.db.collection('saved_destinations').where('user_id', '==', user_id)
            destinations = []
            for doc in dests_ref.stream():
                dest_data = doc.to_dict()
                dest_data['id'] = doc.id
                destinations.append(dest_data)
            return destinations
        except Exception as e:
            logger.error(f"Error getting saved destinations: {str(e)}")
            return []
    def get_taste_graph(self, user_id: str) -> dict:
        """Fetch user's taste graph from Firestore"""
        if not self.db:
            return {}
        try:
            doc = self.db.collection('taste_graphs').document(user_id).get()
            if doc.exists:
                return doc.to_dict()
            return {}
        except Exception as e:
            logger.error(f"Error getting taste graph: {str(e)}")
            return {}

    def save_taste_graph(self, user_id: str, graph_data: dict) -> bool:
        """Save or update user's taste graph in Firestore"""
        if not self.db:
            return False
        try:
            doc_ref = self.db.collection('taste_graphs').document(user_id)
            doc_ref.set(graph_data)
            return True
        except Exception as e:
            logger.error(f"Error saving taste graph: {str(e)}")
            return False
    def get_user_trips(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all trips for a user (for compatibility with For You section)"""
        if not self.db:
            return []
        try:
            trips_ref = self.db.collection('trip_plans').where('user_id', '==', user_id).limit(limit)
            trips = []
            for doc in trips_ref.stream():
                trip_data = doc.to_dict()
                trip_data['id'] = doc.id
                trips.append(trip_data)
            return trips
        except Exception as e:
            logger.error(f"Error getting user trips: {str(e)}")
            return []

firestore_service = FirestoreService()
