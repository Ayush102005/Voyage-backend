"""
Taste Graph Service - Build and maintain user taste graphs from reviews
Uses AI to extract preferences and patterns from verified reviews
"""

from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict, Counter
import json

from schemas import (
    TripReview, ReviewHighlight, TasteGraph, TasteGraphNode,
    TasteGraphInsight, VoyageVerifiedReview
)


class TasteGraphBuilder:
    """
    Builds and updates user taste graphs from review data
    """
    
    def __init__(self):
        self.preference_weights = {
            5: 1.0,    # 5-star rating = max preference
            4: 0.7,    # 4-star = strong positive
            3: 0.4,    # 3-star = neutral/mild positive
            2: 0.2,    # 2-star = mild negative
            1: 0.0     # 1-star = avoid
        }
    
    def build_taste_graph(
        self, 
        user_id: str, 
        reviews: List[VoyageVerifiedReview]
    ) -> TasteGraph:
        """
        Build a complete taste graph from all user reviews
        """
        if not reviews:
            return self._create_empty_taste_graph(user_id)
        
        # Extract nodes by category
        destinations = self._extract_destination_nodes(reviews)
        foods = self._extract_food_nodes(reviews)
        activities = self._extract_activity_nodes(reviews)
        accommodations = self._extract_accommodation_nodes(reviews)
        experiences = self._extract_experience_nodes(reviews)
        
        # Calculate high-level insights
        top_preferences = self._extract_top_preferences(reviews)
        avoid_list = self._extract_avoid_list(reviews)
        preferred_trip_types = self._extract_trip_types(reviews)
        budget_patterns = self._calculate_budget_patterns(reviews)
        seasonality = self._calculate_seasonality(reviews)
        
        # Calculate statistics
        total_reviews = len(reviews)
        total_trips = len(set(r.trip_id for r in reviews))
        average_rating = sum(r.review.ratings.overall for r in reviews) / total_reviews
        
        # Confidence score based on data volume
        confidence_score = min(total_reviews / 10, 1.0)  # Full confidence at 10+ reviews
        
        return TasteGraph(
            user_id=user_id,
            destinations=destinations,
            foods=foods,
            activities=activities,
            accommodations=accommodations,
            experiences=experiences,
            top_preferences=top_preferences,
            avoid_list=avoid_list,
            preferred_trip_types=preferred_trip_types,
            budget_patterns=budget_patterns,
            seasonality=seasonality,
            total_reviews=total_reviews,
            total_trips=total_trips,
            average_rating=average_rating,
            last_updated=datetime.now(),
            confidence_score=confidence_score
        )
    
    def update_taste_graph_incremental(
        self,
        existing_graph: TasteGraph,
        new_review: VoyageVerifiedReview
    ) -> TasteGraph:
        """
        Update an existing taste graph with a new review (incremental update)
        """
        # Update statistics
        existing_graph.total_reviews += 1
        existing_graph.total_trips = len(set([new_review.trip_id]))  # Simplified
        existing_graph.average_rating = (
            (existing_graph.average_rating * (existing_graph.total_reviews - 1) + 
             new_review.review.ratings.overall) / existing_graph.total_reviews
        )
        existing_graph.last_updated = datetime.now()
        existing_graph.confidence_score = min(existing_graph.total_reviews / 10, 1.0)
        
        # Extract and merge new nodes
        new_destinations = self._extract_destination_nodes([new_review])
        new_foods = self._extract_food_nodes([new_review])
        new_activities = self._extract_activity_nodes([new_review])
        new_accommodations = self._extract_accommodation_nodes([new_review])
        
        existing_graph.destinations = self._merge_nodes(existing_graph.destinations, new_destinations)
        existing_graph.foods = self._merge_nodes(existing_graph.foods, new_foods)
        existing_graph.activities = self._merge_nodes(existing_graph.activities, new_activities)
        existing_graph.accommodations = self._merge_nodes(existing_graph.accommodations, new_accommodations)
        
        return existing_graph
    
    def _extract_destination_nodes(self, reviews: List[VoyageVerifiedReview]) -> List[TasteGraphNode]:
        """Extract destination preferences from reviews"""
        nodes_dict = {}
        
        for review in reviews:
            # From highlights
            for highlight in review.review.highlights:
                if highlight.category.lower() in ['destination', 'place', 'location', 'city']:
                    node_id = self._normalize_id(highlight.item_name)
                    
                    if node_id not in nodes_dict:
                        nodes_dict[node_id] = {
                            'item_name': highlight.item_name,
                            'ratings': [],
                            'tags': set(),
                            'notes': [],
                            'first_interaction': review.created_at,
                            'last_interaction': review.created_at
                        }
                    
                    nodes_dict[node_id]['ratings'].append(highlight.rating)
                    if highlight.tags:
                        nodes_dict[node_id]['tags'].update(highlight.tags)
                    nodes_dict[node_id]['notes'].append(highlight.description)
                    nodes_dict[node_id]['last_interaction'] = max(
                        nodes_dict[node_id]['last_interaction'],
                        review.created_at
                    )
            
            # From overall ratings
            destination_rating = review.review.ratings.destinations
            # Can add main destination from trip_id lookup if needed
        
        # Convert to TasteGraphNode objects
        nodes = []
        for node_id, data in nodes_dict.items():
            avg_rating = sum(data['ratings']) / len(data['ratings'])
            preference_score = self.preference_weights.get(round(avg_rating), 0.5)
            sentiment = self._rating_to_sentiment(avg_rating)
            
            nodes.append(TasteGraphNode(
                category='destination',
                item_id=node_id,
                item_name=data['item_name'],
                preference_score=preference_score,
                sentiment=sentiment,
                interaction_count=len(data['ratings']),
                average_rating=avg_rating,
                tags=list(data['tags']),
                last_interaction=data['last_interaction'],
                first_interaction=data['first_interaction'],
                notes='; '.join(data['notes'][:3])  # Top 3 notes
            ))
        
        # Sort by preference score
        nodes.sort(key=lambda x: x.preference_score, reverse=True)
        return nodes
    
    def _extract_food_nodes(self, reviews: List[VoyageVerifiedReview]) -> List[TasteGraphNode]:
        """Extract food preferences from reviews"""
        nodes_dict = {}
        
        for review in reviews:
            # From highlights
            for highlight in review.review.highlights:
                if highlight.category.lower() in ['food', 'restaurant', 'cuisine', 'dish']:
                    node_id = self._normalize_id(highlight.item_name)
                    
                    if node_id not in nodes_dict:
                        nodes_dict[node_id] = {
                            'item_name': highlight.item_name,
                            'ratings': [],
                            'tags': set(),
                            'notes': [],
                            'locations': set(),
                            'first_interaction': review.created_at,
                            'last_interaction': review.created_at
                        }
                    
                    nodes_dict[node_id]['ratings'].append(highlight.rating)
                    if highlight.tags:
                        nodes_dict[node_id]['tags'].update(highlight.tags)
                    if highlight.location:
                        nodes_dict[node_id]['locations'].add(highlight.location)
                    nodes_dict[node_id]['notes'].append(highlight.description)
                    nodes_dict[node_id]['last_interaction'] = max(
                        nodes_dict[node_id]['last_interaction'],
                        review.created_at
                    )
        
        # Convert to nodes
        nodes = []
        for node_id, data in nodes_dict.items():
            avg_rating = sum(data['ratings']) / len(data['ratings'])
            preference_score = self.preference_weights.get(round(avg_rating), 0.5)
            sentiment = self._rating_to_sentiment(avg_rating)
            
            tags_list = list(data['tags'])
            if data['locations']:
                tags_list.extend([f"found_in:{loc}" for loc in list(data['locations'])[:3]])
            
            nodes.append(TasteGraphNode(
                category='food',
                item_id=node_id,
                item_name=data['item_name'],
                preference_score=preference_score,
                sentiment=sentiment,
                interaction_count=len(data['ratings']),
                average_rating=avg_rating,
                tags=tags_list,
                last_interaction=data['last_interaction'],
                first_interaction=data['first_interaction'],
                notes='; '.join(data['notes'][:3])
            ))
        
        nodes.sort(key=lambda x: x.preference_score, reverse=True)
        return nodes
    
    def _extract_activity_nodes(self, reviews: List[VoyageVerifiedReview]) -> List[TasteGraphNode]:
        """Extract activity preferences from reviews"""
        nodes_dict = {}
        
        for review in reviews:
            for highlight in review.review.highlights:
                if highlight.category.lower() in ['activity', 'experience', 'adventure', 'tour']:
                    node_id = self._normalize_id(highlight.item_name)
                    
                    if node_id not in nodes_dict:
                        nodes_dict[node_id] = {
                            'item_name': highlight.item_name,
                            'ratings': [],
                            'tags': set(),
                            'notes': [],
                            'first_interaction': review.created_at,
                            'last_interaction': review.created_at
                        }
                    
                    nodes_dict[node_id]['ratings'].append(highlight.rating)
                    if highlight.tags:
                        nodes_dict[node_id]['tags'].update(highlight.tags)
                    nodes_dict[node_id]['notes'].append(highlight.description)
                    nodes_dict[node_id]['last_interaction'] = max(
                        nodes_dict[node_id]['last_interaction'],
                        review.created_at
                    )
        
        nodes = []
        for node_id, data in nodes_dict.items():
            avg_rating = sum(data['ratings']) / len(data['ratings'])
            preference_score = self.preference_weights.get(round(avg_rating), 0.5)
            sentiment = self._rating_to_sentiment(avg_rating)
            
            nodes.append(TasteGraphNode(
                category='activity',
                item_id=node_id,
                item_name=data['item_name'],
                preference_score=preference_score,
                sentiment=sentiment,
                interaction_count=len(data['ratings']),
                average_rating=avg_rating,
                tags=list(data['tags']),
                last_interaction=data['last_interaction'],
                first_interaction=data['first_interaction'],
                notes='; '.join(data['notes'][:3])
            ))
        
        nodes.sort(key=lambda x: x.preference_score, reverse=True)
        return nodes
    
    def _extract_accommodation_nodes(self, reviews: List[VoyageVerifiedReview]) -> List[TasteGraphNode]:
        """Extract accommodation preferences from reviews"""
        nodes_dict = {}
        
        for review in reviews:
            for highlight in review.review.highlights:
                if highlight.category.lower() in ['accommodation', 'hotel', 'stay', 'resort', 'homestay']:
                    node_id = self._normalize_id(highlight.item_name)
                    
                    if node_id not in nodes_dict:
                        nodes_dict[node_id] = {
                            'item_name': highlight.item_name,
                            'ratings': [],
                            'tags': set(),
                            'notes': [],
                            'first_interaction': review.created_at,
                            'last_interaction': review.created_at
                        }
                    
                    nodes_dict[node_id]['ratings'].append(highlight.rating)
                    if highlight.tags:
                        nodes_dict[node_id]['tags'].update(highlight.tags)
                    nodes_dict[node_id]['notes'].append(highlight.description)
                    nodes_dict[node_id]['last_interaction'] = max(
                        nodes_dict[node_id]['last_interaction'],
                        review.created_at
                    )
        
        nodes = []
        for node_id, data in nodes_dict.items():
            avg_rating = sum(data['ratings']) / len(data['ratings'])
            preference_score = self.preference_weights.get(round(avg_rating), 0.5)
            sentiment = self._rating_to_sentiment(avg_rating)
            
            nodes.append(TasteGraphNode(
                category='accommodation',
                item_id=node_id,
                item_name=data['item_name'],
                preference_score=preference_score,
                sentiment=sentiment,
                interaction_count=len(data['ratings']),
                average_rating=avg_rating,
                tags=list(data['tags']),
                last_interaction=data['last_interaction'],
                first_interaction=data['first_interaction'],
                notes='; '.join(data['notes'][:3])
            ))
        
        nodes.sort(key=lambda x: x.preference_score, reverse=True)
        return nodes
    
    def _extract_experience_nodes(self, reviews: List[VoyageVerifiedReview]) -> List[TasteGraphNode]:
        """Extract general experience preferences"""
        # Similar pattern for other experience types
        return []
    
    def _extract_top_preferences(self, reviews: List[VoyageVerifiedReview]) -> List[str]:
        """Extract top 10 things user consistently loves"""
        all_items = []
        
        for review in reviews:
            for highlight in review.review.highlights:
                if highlight.rating >= 4 and highlight.would_recommend:
                    all_items.append(highlight.item_name)
        
        # Count frequency
        counter = Counter(all_items)
        return [item for item, count in counter.most_common(10)]
    
    def _extract_avoid_list(self, reviews: List[VoyageVerifiedReview]) -> List[str]:
        """Extract things user dislikes"""
        avoid = []
        
        for review in reviews:
            # From lowlights
            if review.review.lowlights:
                for lowlight in review.review.lowlights:
                    if lowlight.rating <= 2 and not lowlight.would_recommend:
                        avoid.append(lowlight.item_name)
            
            # From highlights with low ratings
            for highlight in review.review.highlights:
                if highlight.rating <= 2:
                    avoid.append(highlight.item_name)
        
        return list(set(avoid))
    
    def _extract_trip_types(self, reviews: List[VoyageVerifiedReview]) -> List[str]:
        """Extract preferred trip types from reviews"""
        trip_types = []
        
        for review in reviews:
            # Extract from tags and highlights
            for highlight in review.review.highlights:
                if highlight.tags:
                    trip_types.extend([
                        tag for tag in highlight.tags 
                        if tag in ['adventure', 'relaxation', 'cultural', 'luxury', 'budget', 'spiritual', 'party', 'family']
                    ])
        
        counter = Counter(trip_types)
        return [tt for tt, count in counter.most_common(5)]
    
    def _calculate_budget_patterns(self, reviews: List[VoyageVerifiedReview]) -> Dict:
        """Calculate spending patterns by category"""
        patterns = {
            'average_per_trip': 0,
            'accommodation_percentage': 0,
            'food_percentage': 0,
            'activities_percentage': 0,
            'transport_percentage': 0
        }
        
        total_spent = []
        breakdowns = []
        
        for review in reviews:
            if review.review.actual_spent:
                total_spent.append(review.review.actual_spent)
            if review.review.budget_breakdown:
                breakdowns.append(review.review.budget_breakdown)
        
        if total_spent:
            patterns['average_per_trip'] = sum(total_spent) / len(total_spent)
        
        if breakdowns:
            # Calculate average percentages
            categories = ['accommodation', 'food', 'activities', 'transport']
            for category in categories:
                values = [b.get(category, 0) for b in breakdowns]
                if values:
                    patterns[f'{category}_percentage'] = (sum(values) / len(values) / patterns['average_per_trip'] * 100) if patterns['average_per_trip'] > 0 else 0
        
        return patterns
    
    def _calculate_seasonality(self, reviews: List[VoyageVerifiedReview]) -> Dict:
        """Calculate preferred months/seasons for travel"""
        months = []
        seasons = []
        
        for review in reviews:
            if review.review.travel_dates and 'start' in review.review.travel_dates:
                try:
                    start_date = datetime.fromisoformat(review.review.travel_dates['start'])
                    months.append(start_date.strftime('%B'))
                    
                    # Determine season
                    month_num = start_date.month
                    if month_num in [11, 12, 1, 2]:
                        seasons.append('winter')
                    elif month_num in [3, 4, 5]:
                        seasons.append('spring')
                    elif month_num in [6, 7, 8, 9]:
                        seasons.append('monsoon')
                    else:
                        seasons.append('autumn')
                except:
                    pass
        
        month_counter = Counter(months)
        season_counter = Counter(seasons)
        
        return {
            'preferred_months': [m for m, c in month_counter.most_common(3)],
            'preferred_seasons': [s for s, c in season_counter.most_common(2)]
        }
    
    def _merge_nodes(
        self, 
        existing: List[TasteGraphNode], 
        new: List[TasteGraphNode]
    ) -> List[TasteGraphNode]:
        """Merge new nodes into existing nodes"""
        existing_dict = {node.item_id: node for node in existing}
        
        for new_node in new:
            if new_node.item_id in existing_dict:
                # Update existing node
                existing_node = existing_dict[new_node.item_id]
                
                # Recalculate average
                total_interactions = existing_node.interaction_count + new_node.interaction_count
                existing_node.average_rating = (
                    (existing_node.average_rating * existing_node.interaction_count +
                     new_node.average_rating * new_node.interaction_count) / total_interactions
                )
                existing_node.interaction_count = total_interactions
                
                # Update preference score
                existing_node.preference_score = self.preference_weights.get(
                    round(existing_node.average_rating), 0.5
                )
                existing_node.sentiment = self._rating_to_sentiment(existing_node.average_rating)
                
                # Merge tags
                existing_tags = set(existing_node.tags)
                existing_tags.update(new_node.tags)
                existing_node.tags = list(existing_tags)
                
                # Update timestamps
                existing_node.last_interaction = max(
                    existing_node.last_interaction,
                    new_node.last_interaction
                )
            else:
                # Add new node
                existing_dict[new_node.item_id] = new_node
        
        # Convert back to list and sort
        nodes = list(existing_dict.values())
        nodes.sort(key=lambda x: x.preference_score, reverse=True)
        return nodes
    
    def _normalize_id(self, name: str) -> str:
        """Normalize item name to ID"""
        return name.lower().strip().replace(' ', '_').replace("'", '')
    
    def _rating_to_sentiment(self, rating: float) -> str:
        """Convert rating to sentiment"""
        if rating >= 4:
            return 'positive'
        elif rating >= 3:
            return 'neutral'
        else:
            return 'negative'
    
    def _create_empty_taste_graph(self, user_id: str) -> TasteGraph:
        """Create an empty taste graph for new users"""
        return TasteGraph(
            user_id=user_id,
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
            total_reviews=0,
            total_trips=0,
            average_rating=0,
            last_updated=datetime.now(),
            confidence_score=0
        )
    
    def generate_insights(
        self, 
        taste_graph: TasteGraph, 
        llm=None
    ) -> List[TasteGraphInsight]:
        """
        Generate AI-powered insights from taste graph
        """
        insights = []
        
        # Rule-based insights (fast)
        
        # 1. Strong preferences
        if taste_graph.destinations:
            top_dest = taste_graph.destinations[0]
            if top_dest.preference_score >= 0.8:
                insights.append(TasteGraphInsight(
                    insight_type='preference',
                    category='destination',
                    message=f"You absolutely love {top_dest.item_name}! Consider similar destinations.",
                    confidence=top_dest.preference_score,
                    supporting_evidence=[f"Rated {top_dest.average_rating:.1f}/5 across {top_dest.interaction_count} trips"]
                ))
        
        # 2. Avoid patterns
        if taste_graph.avoid_list:
            insights.append(TasteGraphInsight(
                insight_type='warning',
                category='general',
                message=f"Based on past trips, we'll avoid recommending: {', '.join(taste_graph.avoid_list[:3])}",
                confidence=0.9,
                supporting_evidence=taste_graph.avoid_list[:5]
            ))
        
        # 3. Budget patterns
        if taste_graph.budget_patterns.get('average_per_trip', 0) > 0:
            avg_budget = taste_graph.budget_patterns['average_per_trip']
            insights.append(TasteGraphInsight(
                insight_type='pattern',
                category='budget',
                message=f"Your average trip budget is ₹{avg_budget:,.0f}. We'll plan accordingly.",
                confidence=min(taste_graph.total_reviews / 5, 1.0),
                supporting_evidence=[f"Based on {taste_graph.total_reviews} trips"]
            ))
        
        # 4. Seasonal preferences
        if taste_graph.seasonality.get('preferred_seasons'):
            seasons = taste_graph.seasonality['preferred_seasons']
            insights.append(TasteGraphInsight(
                insight_type='pattern',
                category='seasonality',
                message=f"You prefer traveling in {' and '.join(seasons)}. Perfect timing recommendations coming!",
                confidence=0.8,
                supporting_evidence=seasons
            ))
        
        # 5. Food preferences
        if taste_graph.foods:
            top_foods = [f.item_name for f in taste_graph.foods[:3] if f.preference_score >= 0.7]
            if top_foods:
                insights.append(TasteGraphInsight(
                    insight_type='preference',
                    category='food',
                    message=f"Must-try foods on your next trip: {', '.join(top_foods)}",
                    confidence=0.85,
                    supporting_evidence=top_foods
                ))
        
        # 6. Activity patterns
        if taste_graph.preferred_trip_types:
            trip_type = taste_graph.preferred_trip_types[0]
            insights.append(TasteGraphInsight(
                insight_type='recommendation',
                category='trip_type',
                message=f"Your trips are usually {trip_type}-focused. We'll prioritize similar experiences.",
                confidence=0.8,
                supporting_evidence=taste_graph.preferred_trip_types
            ))
        
        # 7. Confidence note
        if taste_graph.confidence_score < 0.5:
            insights.append(TasteGraphInsight(
                insight_type='pattern',
                category='general',
                message=f"Complete more trips and reviews to unlock better personalization! ({taste_graph.total_reviews}/10)",
                confidence=1.0,
                supporting_evidence=[f"{taste_graph.total_reviews} reviews so far"]
            ))
        
        return insights


# Global instance
_taste_graph_builder = None

def get_taste_graph_builder() -> TasteGraphBuilder:
    """Get or create the global taste graph builder instance"""
    global _taste_graph_builder
    if _taste_graph_builder is None:
        _taste_graph_builder = TasteGraphBuilder()
    return _taste_graph_builder
