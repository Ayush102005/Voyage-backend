"""
User Dashboard Service for Voyage Travel Planner
Aggregates data from trips and expenses for comprehensive dashboard view
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional
import uuid
from collections import defaultdict
from schemas import (
    UserDashboard, DashboardStats, TripSummaryCard, RecentActivity,
    BudgetInsight
)


class DashboardService:
    """
    Service for generating user dashboard data.
    Aggregates information from trips, expenses, and budget tracking.
    """
    
    def __init__(self, firestore_client=None, firestore_service=None):
        """Initialize dashboard service"""
        self.db = firestore_client
        self.firestore_service = firestore_service
    
    def get_user_dashboard(self, user_id: str, user_email: str = None) -> UserDashboard:
        """
        Get complete dashboard data for a user
        
        Args:
            user_id: User ID
            user_email: User email (optional)
            
        Returns:
            UserDashboard with all aggregated data (expense tracking + trip planning)
        """
        # Get all user's trips
        trips = self._get_user_trips(user_id)
        
        # Get all expenses
        all_expenses = self._get_all_user_expenses(user_id)
        
        # Calculate overall statistics
        stats = self._calculate_dashboard_stats(trips, all_expenses)
        
        # Categorize trips
        now = datetime.now(timezone.utc)
        active_trips = []
        upcoming_trips = []
        completed_trips = []
        
        for trip in trips:
            trip_card = self._create_trip_summary_card(trip, all_expenses)
            
            if trip_card.status == "ongoing":
                active_trips.append(trip_card)
            elif trip_card.status == "upcoming":
                upcoming_trips.append(trip_card)
            elif trip_card.status == "completed":
                completed_trips.append(trip_card)
        
        # Sort by date
        active_trips.sort(key=lambda x: x.start_date)
        upcoming_trips.sort(key=lambda x: x.start_date)
        completed_trips.sort(key=lambda x: x.start_date, reverse=True)
        
        # Get recent activity
        recent_activity = self._generate_recent_activity(trips, all_expenses, limit=20)
        
        # Generate budget insights
        budget_insights = self._generate_budget_insights(trips, all_expenses, stats)
        
        # Count unread alerts
        unread_alerts = self._count_unread_alerts(user_id)
        
        # Calculate spending trend
        spending_trend = self._calculate_spending_trend(all_expenses)
        
        # Get top categories
        top_categories = self._get_top_categories(all_expenses)
        
        # === Trip Planning Features (from old dashboard) ===
        
        # User info
        user_info = None
        if user_email:
            # Format display name from email
            username = user_email.split('@')[0]
            # Split by common separators and numbers, capitalize each part
            import re
            parts = re.split(r'[._-]|\d+', username)
            formatted_parts = [part.capitalize() for part in parts if part]
            display_name = ' '.join(formatted_parts) if formatted_parts else username
            
            user_info = {
                "email": user_email,
                "display_name": display_name
            }
        
        # Get user profile for preferences
        profile = None
        if self.firestore_service:
            try:
                profile = self.firestore_service.get_user_profile(user_id=user_id)
            except Exception as e:
                print(f"Could not fetch profile: {e}")
        
        # Past trips summary (convert completed TripSummaryCards to TripSummary format)
        from schemas import TripSummary
        past_trips = []
        for trip_card in completed_trips[:10]:  # Max 10 past trips
            try:
                past_trips.append(TripSummary(
                    trip_id=trip_card.trip_id,
                    destination=trip_card.destination,
                    start_date=trip_card.start_date,
                    end_date=trip_card.end_date,
                    num_days=(trip_card.end_date - trip_card.start_date).days + 1,
                    budget=trip_card.total_budget,
                    interests="",  # Not available in TripSummaryCard
                    created_at=trip_card.start_date
                ))
            except Exception as e:
                print(f"Error converting trip card: {e}")
        
        # Saved destinations
        saved_destinations = []
        if self.db:
            try:
                saved_ref = self.db.collection('saved_destinations').where('user_id', '==', user_id)
                for doc in saved_ref.stream():
                    dest_data = doc.to_dict()
                    saved_destinations.append(dest_data)
            except Exception as e:
                print(f"Error fetching saved destinations: {e}")
        
        # Personalized suggestions (if profile has learned preferences)
        personalized_suggestions = []
        if profile and profile.get('learned_preferences'):
            # For now, use empty list - AI suggestions would be generated here
            # This would call the AI service to generate suggestions based on preferences
            pass
        
        # Quick actions for UI
        quick_actions = [
            {"label": "Plan New Trip", "action": "create_trip", "icon": "add_circle"},
            {"label": "Track Expense", "action": "add_expense", "icon": "receipt"},
            {"label": "View Budget Alerts", "action": "view_alerts", "icon": "notifications"},
            {"label": "Explore Destinations", "action": "explore", "icon": "explore"}
        ]
        
        return UserDashboard(
            user_id=user_id,
            # Expense tracking section
            stats=stats,
            active_trips=active_trips[:10],  # Show max 10
            upcoming_trips=upcoming_trips[:10],  # Show max 10
            recent_activity=recent_activity,
            budget_insights=budget_insights,
            unread_alerts=unread_alerts,
            spending_trend=spending_trend,
            top_categories=top_categories,
            # Trip planning section
            user_info=user_info,
            past_trips=past_trips,
            saved_destinations=saved_destinations,
            personalized_suggestions=personalized_suggestions,
            quick_actions=quick_actions,
            last_updated=datetime.now(timezone.utc)
        )
    
    def _get_user_trips(self, user_id: str) -> List[Dict]:
        """Get all trips for a user"""
        if not self.db:
            return []
        
        trips_ref = self.db.collection('trips').where('user_id', '==', user_id)
        trips = []
        
        for doc in trips_ref.stream():
            trip_data = doc.to_dict()
            trip_data['trip_id'] = doc.id
            trips.append(trip_data)
        
        return trips
    
    def _get_all_user_expenses(self, user_id: str) -> List[Dict]:
        """Get all expenses for a user across all trips"""
        if not self.db:
            return []
        
        expenses_ref = self.db.collection('expenses').where('user_id', '==', user_id)
        expenses = []
        
        for doc in expenses_ref.stream():
            expense_data = doc.to_dict()
            expense_data['expense_id'] = doc.id
            
            # Skip deleted expenses
            if not expense_data.get('deleted', False):
                expenses.append(expense_data)
        
        return expenses
    
    def _calculate_dashboard_stats(self, trips: List[Dict], expenses: List[Dict]) -> DashboardStats:
        """Calculate overall dashboard statistics"""
        now = datetime.now(timezone.utc)
        
        total_trips = len(trips)
        active_trips = 0
        completed_trips = 0
        upcoming_trips = 0
        total_budget = 0
        total_spent = 0
        within_budget_count = 0
        
        # Category spending
        category_spending = defaultdict(float)
        
        # Destination frequency
        destination_count = defaultdict(int)
        
        for trip in trips:
            start_date = trip.get('start_date')
            end_date = trip.get('end_date')
            
            # Convert to datetime if string
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            # Categorize trip
            if start_date <= now <= end_date:
                active_trips += 1
            elif now < start_date:
                upcoming_trips += 1
            else:
                completed_trips += 1
            
            # Budget tracking
            trip_budget = trip.get('budget', {})
            if isinstance(trip_budget, dict):
                trip_total_budget = trip_budget.get('total_budget', 0)
            else:
                trip_total_budget = trip_budget
            
            total_budget += trip_total_budget
            
            # Get expenses for this trip
            trip_expenses = [e for e in expenses if e.get('trip_id') == trip.get('trip_id')]
            trip_spent = sum(e.get('amount', 0) for e in trip_expenses)
            total_spent += trip_spent
            
            # Check if within budget
            if trip_spent <= trip_total_budget:
                within_budget_count += 1
            
            # Track destination
            destination = trip.get('destination', 'Unknown')
            destination_count[destination] += 1
        
        # Calculate category spending
        for expense in expenses:
            category = expense.get('category', 'Other')
            amount = expense.get('amount', 0)
            category_spending[category] += amount
        
        # Find most expensive category
        most_expensive_category = "Other"
        if category_spending:
            most_expensive_category = max(category_spending, key=category_spending.get)
        
        # Find favorite destination
        favorite_destination = None
        if destination_count:
            favorite_destination = max(destination_count, key=destination_count.get)
        
        # Calculate averages
        average_trip_cost = total_spent / total_trips if total_trips > 0 else 0
        budget_adherence_rate = (within_budget_count / total_trips * 100) if total_trips > 0 else 100.0
        
        return DashboardStats(
            total_trips=total_trips,
            active_trips=active_trips,
            completed_trips=completed_trips,
            upcoming_trips=upcoming_trips,
            total_expenses_logged=len(expenses),
            total_amount_spent=total_spent,
            average_trip_cost=average_trip_cost,
            budget_adherence_rate=budget_adherence_rate,
            most_expensive_category=most_expensive_category,
            favorite_destination=favorite_destination
        )
    
    def _create_trip_summary_card(self, trip: Dict, all_expenses: List[Dict]) -> TripSummaryCard:
        """Create a summary card for a trip"""
        now = datetime.now(timezone.utc)
        
        trip_id = trip.get('trip_id')
        start_date = trip.get('start_date')
        end_date = trip.get('end_date')
        
        # Convert to datetime if string
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Determine status
        if start_date <= now <= end_date:
            status = "ongoing"
        elif now < start_date:
            status = "upcoming"
        else:
            status = "completed"
        
        # Get trip expenses
        trip_expenses = [e for e in all_expenses if e.get('trip_id') == trip_id]
        
        # Calculate spending
        total_spent = sum(e.get('amount', 0) for e in trip_expenses)
        
        # Get budget
        trip_budget = trip.get('budget', {})
        if isinstance(trip_budget, dict):
            total_budget = trip_budget.get('total_budget', 0)
        else:
            total_budget = trip_budget
        
        # Calculate percentage
        percentage_used = (total_spent / total_budget * 100) if total_budget > 0 else 0
        
        # Determine budget status
        if percentage_used >= 100:
            budget_status = "over-budget"
        elif percentage_used >= 90:
            budget_status = "critical"
        elif percentage_used >= 75:
            budget_status = "warning"
        else:
            budget_status = "on-track"
        
        # Calculate days remaining
        days_remaining = 0
        if status in ["upcoming", "ongoing"]:
            days_remaining = max(0, (end_date - now).days)
        
        # Get last expense date
        last_expense_date = None
        if trip_expenses:
            last_expense = max(trip_expenses, key=lambda x: x.get('created_at', datetime.min))
            last_expense_date = last_expense.get('created_at')
            if isinstance(last_expense_date, str):
                last_expense_date = datetime.fromisoformat(last_expense_date.replace('Z', '+00:00'))
        
        # Count unread alerts for this trip
        alerts_count = self._count_trip_alerts(trip_id)
        
        return TripSummaryCard(
            trip_id=trip_id,
            destination=trip.get('destination', 'Unknown'),
            start_date=start_date,
            end_date=end_date,
            status=status,
            total_budget=total_budget,
            total_spent=total_spent,
            percentage_used=percentage_used,
            budget_status=budget_status,
            days_remaining=days_remaining,
            expense_count=len(trip_expenses),
            last_expense_date=last_expense_date,
            alerts_count=alerts_count
        )
    
    def _generate_recent_activity(self, trips: List[Dict], expenses: List[Dict], limit: int = 20) -> List[RecentActivity]:
        """Generate recent activity feed"""
        activities = []
        
        # Create map of trip_id to trip name
        trip_names = {t.get('trip_id'): t.get('destination', 'Unknown') for t in trips}
        
        # Add expense activities
        for expense in sorted(expenses, key=lambda x: x.get('created_at', datetime.min), reverse=True)[:limit]:
            created_at = expense.get('created_at')
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            trip_id = expense.get('trip_id')
            trip_name = trip_names.get(trip_id, 'Unknown Trip')
            category = expense.get('category', 'Other')
            amount = expense.get('amount', 0)
            description = expense.get('description', 'Expense')
            
            # Determine icon and color based on category
            icon_map = {
                "Accommodation": "hotel",
                "Food & Dining": "restaurant",
                "Transportation": "directions_car",
                "Activities & Entertainment": "local_activity",
                "Shopping": "shopping_bag",
                "Emergency": "warning",
                "Other": "receipt"
            }
            
            color_map = {
                "Accommodation": "blue",
                "Food & Dining": "orange",
                "Transportation": "green",
                "Activities & Entertainment": "purple",
                "Shopping": "pink",
                "Emergency": "red",
                "Other": "gray"
            }
            
            activities.append(RecentActivity(
                activity_id=expense.get('expense_id'),
                activity_type="expense_added",
                trip_id=trip_id,
                trip_name=trip_name,
                title=f"Spent ₹{amount:,.0f} on {category}",
                description=description,
                amount=amount,
                category=category,
                timestamp=created_at,
                icon=icon_map.get(category, "receipt"),
                color=color_map.get(category, "gray")
            ))
        
        # Sort by timestamp
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        
        return activities[:limit]
    
    def _generate_budget_insights(self, trips: List[Dict], expenses: List[Dict], stats: DashboardStats) -> List[BudgetInsight]:
        """Generate AI-powered budget insights"""
        insights = []
        now = datetime.now(timezone.utc)
        
        # Insight 1: Budget adherence achievement
        if stats.budget_adherence_rate >= 80:
            insights.append(BudgetInsight(
                insight_id=str(uuid.uuid4()),
                type="achievement",
                title="🏆 Excellent Budget Management!",
                message=f"You've stayed within budget on {stats.budget_adherence_rate:.0f}% of your trips. Keep up the great work!",
                action=None,
                priority="low",
                trip_id=None,
                created_at=now
            ))
        
        # Insight 2: Warning for active trips over budget
        for trip in trips:
            start_date = trip.get('start_date')
            end_date = trip.get('end_date')
            
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            if start_date <= now <= end_date:  # Active trip
                trip_id = trip.get('trip_id')
                trip_expenses = [e for e in expenses if e.get('trip_id') == trip_id]
                total_spent = sum(e.get('amount', 0) for e in trip_expenses)
                
                trip_budget = trip.get('budget', {})
                if isinstance(trip_budget, dict):
                    total_budget = trip_budget.get('total_budget', 0)
                else:
                    total_budget = trip_budget
                
                percentage_used = (total_spent / total_budget * 100) if total_budget > 0 else 0
                
                if percentage_used >= 90:
                    days_remaining = max(0, (end_date - now).days)
                    remaining_budget = total_budget - total_spent
                    daily_limit = remaining_budget / days_remaining if days_remaining > 0 else 0
                    
                    insights.append(BudgetInsight(
                        insight_id=str(uuid.uuid4()),
                        type="warning",
                        title=f"⚠️ Budget Alert: {trip.get('destination')}",
                        message=f"You've used {percentage_used:.0f}% of your budget. Limit spending to ₹{daily_limit:.0f}/day for the remaining {days_remaining} days.",
                        action="View trip details",
                        priority="high",
                        trip_id=trip_id,
                        created_at=now
                    ))
        
        # Insight 3: Spending pattern tip
        if stats.most_expensive_category:
            insights.append(BudgetInsight(
                insight_id=str(uuid.uuid4()),
                type="tip",
                title="💡 Spending Pattern Insight",
                message=f"Your highest spending category is {stats.most_expensive_category}. Consider budgeting more for this category in future trips.",
                action=None,
                priority="medium",
                trip_id=None,
                created_at=now
            ))
        
        # Insight 4: Upcoming trip reminder
        upcoming_count = stats.upcoming_trips
        if upcoming_count > 0:
            insights.append(BudgetInsight(
                insight_id=str(uuid.uuid4()),
                type="recommendation",
                title="🗓️ Upcoming Trips",
                message=f"You have {upcoming_count} upcoming trip{'s' if upcoming_count > 1 else ''}. Review your budgets and make sure you're prepared!",
                action="View upcoming trips",
                priority="medium",
                trip_id=None,
                created_at=now
            ))
        
        return insights
    
    def _count_unread_alerts(self, user_id: str) -> int:
        """Count unread budget alerts for user"""
        if not self.db:
            return 0
        
        # Get all user's trips
        trips_ref = self.db.collection('trips').where('user_id', '==', user_id)
        trip_ids = [doc.id for doc in trips_ref.stream()]
        
        # Count unread alerts across all trips
        unread_count = 0
        for trip_id in trip_ids:
            alerts_ref = self.db.collection('budget_alerts')\
                .where('trip_id', '==', trip_id)\
                .where('is_read', '==', False)
            
            unread_count += len(list(alerts_ref.stream()))
        
        return unread_count
    
    def _count_trip_alerts(self, trip_id: str) -> int:
        """Count unread alerts for a specific trip"""
        if not self.db:
            return 0
        
        alerts_ref = self.db.collection('budget_alerts')\
            .where('trip_id', '==', trip_id)\
            .where('is_read', '==', False)
        
        return len(list(alerts_ref.stream()))
    
    def _calculate_spending_trend(self, expenses: List[Dict]) -> str:
        """Calculate overall spending trend"""
        if len(expenses) < 2:
            return "stable"
        
        # Sort by date
        sorted_expenses = sorted(expenses, key=lambda x: x.get('created_at', datetime.min))
        
        # Split into first half and second half
        mid_point = len(sorted_expenses) // 2
        first_half = sorted_expenses[:mid_point]
        second_half = sorted_expenses[mid_point:]
        
        # Calculate averages
        first_avg = sum(e.get('amount', 0) for e in first_half) / len(first_half)
        second_avg = sum(e.get('amount', 0) for e in second_half) / len(second_half)
        
        # Determine trend
        if second_avg > first_avg * 1.2:
            return "increasing"
        elif second_avg < first_avg * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _get_top_categories(self, expenses: List[Dict], limit: int = 5) -> List[Dict]:
        """Get top spending categories"""
        category_spending = defaultdict(lambda: {'total': 0, 'count': 0})
        
        for expense in expenses:
            category = expense.get('category', 'Other')
            amount = expense.get('amount', 0)
            
            category_spending[category]['total'] += amount
            category_spending[category]['count'] += 1
        
        # Convert to list and sort
        categories = []
        for category, data in category_spending.items():
            categories.append({
                'category': category,
                'total_spent': data['total'],
                'expense_count': data['count'],
                'average_expense': data['total'] / data['count'] if data['count'] > 0 else 0
            })
        
        categories.sort(key=lambda x: x['total_spent'], reverse=True)
        
        return categories[:limit]


def get_dashboard_service(firestore_client, firestore_service=None):
    """Factory function to get dashboard service instance"""
    return DashboardService(firestore_client, firestore_service)
