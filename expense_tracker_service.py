"""
On-Trip Expense Tracker Service for Voyage Travel Planner
Live expense tracking with budget management during trips
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
import uuid
from collections import defaultdict
from schemas import (
    Expense, ExpenseCategory, ExpenseTrackerSummary, 
    BudgetAlert, ExpenseAnalyticsResponse
)


class ExpenseTrackerService:
    """
    Service for tracking expenses during trips.
    Transforms static budget into live, interactive expense tracking.
    """
    
    # Standard expense categories
    DEFAULT_CATEGORIES = [
        "Accommodation",
        "Food & Dining",
        "Transportation",
        "Activities & Entertainment",
        "Shopping",
        "Emergency",
        "Other"
    ]
    
    # Budget alert thresholds
    ALERT_THRESHOLDS = {
        "warning": 0.75,      # 75% of budget used
        "critical": 0.90,     # 90% of budget used
        "exceeded": 1.0       # Budget exceeded
    }
    
    def __init__(self, firestore_client=None):
        """Initialize expense tracker service"""
        self.db = firestore_client
        
    def add_expense(
        self,
        trip_id: str,
        user_id: str,
        category: str,
        amount: float,
        description: str,
        date: Optional[datetime] = None,
        location: Optional[str] = None,
        payment_method: Optional[str] = None,
        notes: Optional[str] = None,
        is_shared: bool = False,
        split_with: List[str] = []
    ) -> Expense:
        """
        Add a new expense to the trip
        
        Args:
            trip_id: Trip identifier
            user_id: User logging the expense
            category: Expense category
            amount: Amount spent
            description: What was purchased
            date: When expense occurred (defaults to now)
            location: Where expense occurred
            payment_method: How payment was made
            notes: Additional notes
            is_shared: Whether expense should be split
            split_with: List of user IDs to split with
            
        Returns:
            Expense object
        """
        try:
            expense_id = f"expense_{uuid.uuid4().hex[:12]}"
            expense_date = date or datetime.now(timezone.utc)
            
            print(f"🔧 Creating expense object: {expense_id}")
            print(f"   Trip: {trip_id}, User: {user_id}")
            print(f"   Category: {category}, Amount: {amount}")
            
            expense = Expense(
                expense_id=expense_id,
                trip_id=trip_id,
                user_id=user_id,
                category=category,
                amount=amount,
                currency="INR",
                description=description,
                date=expense_date,
                location=location,
                payment_method=payment_method,
                notes=notes,
                is_shared=is_shared,
                split_with=split_with,
                created_at=datetime.now(timezone.utc)
            )
            
            print(f"✅ Expense object created successfully")
            
            # Save to Firestore
            if self.db:
                print(f"💾 Saving to Firestore collection 'expenses'...")
                expense_ref = self.db.collection('expenses').document(expense_id)
                expense_dict = expense.dict()
                # Add fields required for queries
                expense_dict['deleted'] = False
                expense_dict['updated_at'] = datetime.now(timezone.utc)
                expense_ref.set(expense_dict)
                print(f"✅ Saved to Firestore successfully")
            else:
                print(f"⚠️ No Firestore client - expense not persisted")
            
            # Check if this triggers any budget alerts
            try:
                self._check_budget_alerts(trip_id, category, amount)
            except Exception as alert_error:
                print(f"⚠️ Budget alert check failed: {alert_error}")
                # Don't fail the expense creation if alert check fails
            
            return expense
            
        except Exception as e:
            print(f"❌ Error in add_expense: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def update_expense(
        self,
        expense_id: str,
        updates: Dict
    ) -> Expense:
        """
        Update an existing expense
        
        Args:
            expense_id: Expense to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated Expense object
        """
        if self.db:
            expense_ref = self.db.collection('expenses').document(expense_id)
            expense_doc = expense_ref.get()
            
            if not expense_doc.exists:
                raise Exception(f"Expense {expense_id} not found")
            
            expense_data = expense_doc.to_dict()
            expense_data.update(updates)
            expense_ref.update(updates)
            
            return Expense(**expense_data)
        
        raise Exception("Firestore client not initialized")
    
    def delete_expense(
        self,
        expense_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete an expense
        
        Args:
            expense_id: Expense to delete
            soft_delete: If True, mark as deleted. If False, permanently remove
            
        Returns:
            Success status
        """
        if self.db:
            expense_ref = self.db.collection('expenses').document(expense_id)
            
            if soft_delete:
                expense_ref.update({
                    'deleted': True,
                    'deleted_at': datetime.now(timezone.utc)
                })
            else:
                expense_ref.delete()
            
            return True
        
        return False
    
    def get_expense_tracker(
        self,
        trip_id: str,
        include_deleted: bool = False
    ) -> ExpenseTrackerSummary:
        """
        Get complete expense tracking summary for a trip
        
        Args:
            trip_id: Trip identifier
            include_deleted: Include soft-deleted expenses
            
        Returns:
            ExpenseTrackerSummary with all tracking data
        """
        # Fetch trip details
        trip_data = self._get_trip_data(trip_id)
        
        # Fetch all expenses for this trip
        expenses = self._get_trip_expenses(trip_id, include_deleted)
        
        # Calculate summary
        total_budget = trip_data.get('budget', 0)
        total_spent = sum(e.amount for e in expenses)
        total_remaining = total_budget - total_spent
        percentage_used = (total_spent / total_budget * 100) if total_budget > 0 else 0
        
        # Calculate daily average
        trip_start = trip_data.get('start_date')
        trip_end = trip_data.get('end_date')
        
        if isinstance(trip_start, str):
            trip_start = datetime.fromisoformat(trip_start)
        if isinstance(trip_end, str):
            trip_end = datetime.fromisoformat(trip_end)
        
        now = datetime.now(timezone.utc)
        days_elapsed = max((now - trip_start).days, 1) if trip_start else 1
        days_remaining = max((trip_end - now).days, 0) if trip_end else 0
        total_days = days_elapsed + days_remaining
        
        daily_average = total_spent / days_elapsed if days_elapsed > 0 else 0
        projected_total = daily_average * total_days
        
        # Determine budget status
        if percentage_used >= 100:
            budget_status = "over-budget"
        elif percentage_used >= 90:
            budget_status = "critical"
        elif projected_total > total_budget:
            budget_status = "warning"
        else:
            budget_status = "on-track"
        
        # Group expenses by category
        categories = self._calculate_category_breakdown(
            expenses, 
            trip_data.get('budget_breakdown', {})
        )
        
        # Get recent expenses (last 10)
        recent_expenses = sorted(expenses, key=lambda x: x.created_at, reverse=True)[:10]
        
        # Generate warnings and recommendations
        warnings = self._generate_budget_warnings(
            total_budget,
            total_spent,
            percentage_used,
            categories,
            days_remaining,
            projected_total
        )
        
        recommendations = self._generate_spending_recommendations(
            budget_status,
            categories,
            daily_average,
            days_remaining,
            total_remaining
        )
        
        return ExpenseTrackerSummary(
            trip_id=trip_id,
            total_budget=total_budget,
            total_spent=total_spent,
            total_remaining=total_remaining,
            percentage_used=round(percentage_used, 2),
            daily_average=round(daily_average, 2),
            projected_total=round(projected_total, 2),
            budget_status=budget_status,
            categories=categories,
            recent_expenses=recent_expenses,
            total_expenses_count=len(expenses),
            days_elapsed=days_elapsed,
            days_remaining=days_remaining,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def get_expense_analytics(
        self,
        trip_id: str,
        group_by: str = "category",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ExpenseAnalyticsResponse:
        """
        Get detailed expense analytics
        
        Args:
            trip_id: Trip identifier
            group_by: How to group data (category, day, location, payment_method)
            start_date: Filter start date
            end_date: Filter end date
            
        Returns:
            ExpenseAnalyticsResponse with analytics data
        """
        expenses = self._get_trip_expenses(trip_id, include_deleted=False)
        
        # Filter by date range if provided
        if start_date:
            expenses = [e for e in expenses if e.date >= start_date]
        if end_date:
            expenses = [e for e in expenses if e.date <= end_date]
        
        # Group data
        grouped_data = self._group_expenses(expenses, group_by)
        
        # Get top expenses
        top_expenses = sorted(expenses, key=lambda x: x.amount, reverse=True)[:5]
        
        # Analyze spending trend
        spending_trend = self._analyze_spending_trend(expenses)
        
        # Generate insights
        insights = self._generate_analytics_insights(
            grouped_data,
            expenses,
            group_by
        )
        
        return ExpenseAnalyticsResponse(
            trip_id=trip_id,
            analytics_type=group_by,
            data=grouped_data,
            insights=insights,
            top_expenses=top_expenses,
            spending_trend=spending_trend
        )
    
    def split_expense(
        self,
        expense_id: str,
        split_type: str,
        split_details: List[Dict]
    ) -> Dict:
        """
        Split an expense among multiple people
        
        Args:
            expense_id: Expense to split
            split_type: How to split (equal, custom, percentage)
            split_details: List of split details per user
            
        Returns:
            Split calculation results
        """
        if not self.db:
            raise Exception("Firestore client not initialized")
        
        expense_ref = self.db.collection('expenses').document(expense_id)
        expense_doc = expense_ref.get()
        
        if not expense_doc.exists:
            raise Exception(f"Expense {expense_id} not found")
        
        expense_data = expense_doc.to_dict()
        total_amount = expense_data['amount']
        
        splits = []
        
        if split_type == "equal":
            # Split equally among all people
            num_people = len(split_details)
            per_person = total_amount / num_people
            
            for detail in split_details:
                splits.append({
                    "user_id": detail['user_id'],
                    "user_name": detail.get('user_name', 'Unknown'),
                    "amount": round(per_person, 2),
                    "percentage": round(100 / num_people, 2)
                })
        
        elif split_type == "custom":
            # Custom amounts specified
            for detail in split_details:
                splits.append({
                    "user_id": detail['user_id'],
                    "user_name": detail.get('user_name', 'Unknown'),
                    "amount": detail['amount'],
                    "percentage": round(detail['amount'] / total_amount * 100, 2)
                })
        
        elif split_type == "percentage":
            # Percentage-based split
            for detail in split_details:
                amount = total_amount * (detail['percentage'] / 100)
                splits.append({
                    "user_id": detail['user_id'],
                    "user_name": detail.get('user_name', 'Unknown'),
                    "amount": round(amount, 2),
                    "percentage": detail['percentage']
                })
        
        # Update expense with split details
        expense_ref.update({
            'is_shared': True,
            'split_type': split_type,
            'split_details': splits
        })
        
        return {
            "expense_id": expense_id,
            "total_amount": total_amount,
            "split_type": split_type,
            "splits": splits
        }
    
    def adjust_budget(
        self,
        trip_id: str,
        category: str,
        new_amount: float,
        reason: str
    ) -> Dict:
        """
        Adjust budget for a category during the trip
        
        Args:
            trip_id: Trip identifier
            category: Category to adjust
            new_amount: New budgeted amount
            reason: Reason for adjustment
            
        Returns:
            Updated budget breakdown
        """
        if not self.db:
            raise Exception("Firestore client not initialized")
        
        trip_ref = self.db.collection('trips').document(trip_id)
        trip_doc = trip_ref.get()
        
        if not trip_doc.exists:
            raise Exception(f"Trip {trip_id} not found")
        
        trip_data = trip_doc.to_dict()
        budget_breakdown = trip_data.get('budget_breakdown', {})
        old_amount = budget_breakdown.get(category, 0)
        
        # Update budget
        budget_breakdown[category] = new_amount
        
        # Calculate new total budget
        new_total = sum(budget_breakdown.values())
        
        # Update trip
        trip_ref.update({
            'budget_breakdown': budget_breakdown,
            'budget': new_total
        })
        
        # Log the adjustment
        adjustment_log = {
            'trip_id': trip_id,
            'category': category,
            'old_amount': old_amount,
            'new_amount': new_amount,
            'reason': reason,
            'timestamp': datetime.now(timezone.utc)
        }
        
        self.db.collection('budget_adjustments').add(adjustment_log)
        
        return {
            "category": category,
            "old_amount": old_amount,
            "new_amount": new_amount,
            "total_budget": new_total,
            "budget_breakdown": budget_breakdown
        }
    
    def _get_trip_data(self, trip_id: str) -> Dict:
        """Fetch trip data from Firestore"""
        if not self.db:
            # Return mock data for testing
            return {
                'trip_id': trip_id,
                'budget': 50000,
                'start_date': datetime.now(timezone.utc) - timedelta(days=2),
                'end_date': datetime.now(timezone.utc) + timedelta(days=5),
                'budget_breakdown': {
                    'Accommodation': 15000,
                    'Food & Dining': 12000,
                    'Transportation': 8000,
                    'Activities & Entertainment': 10000,
                    'Shopping': 3000,
                    'Emergency': 2000
                }
            }
        
        # Try 'trips' collection first
        trip_ref = self.db.collection('trips').document(trip_id)
        trip_doc = trip_ref.get()
        
        # Fallback to 'trip_plans' collection
        if not trip_doc.exists:
            trip_ref = self.db.collection('trip_plans').document(trip_id)
            trip_doc = trip_ref.get()
        
        if not trip_doc.exists:
            raise Exception(f"Trip {trip_id} not found in trips or trip_plans collections")
        
        trip_data = trip_doc.to_dict()
        
        # Ensure budget exists with default
        if 'budget' not in trip_data or trip_data['budget'] is None:
            trip_data['budget'] = 50000  # Default budget
        
        # Ensure dates exist
        if 'start_date' not in trip_data or trip_data['start_date'] is None:
            trip_data['start_date'] = datetime.now(timezone.utc)
        
        if 'end_date' not in trip_data or trip_data['end_date'] is None:
            trip_data['end_date'] = datetime.now(timezone.utc) + timedelta(days=7)
        
        return trip_data
    
    def _get_trip_expenses(
        self,
        trip_id: str,
        include_deleted: bool = False
    ) -> List[Expense]:
        """Fetch all expenses for a trip"""
        if not self.db:
            # Return empty list for testing
            return []
        
        query = self.db.collection('expenses').where('trip_id', '==', trip_id)
        
        if not include_deleted:
            query = query.where('deleted', '==', False)
        
        expenses = []
        for doc in query.stream():
            expense_data = doc.to_dict()
            expenses.append(Expense(**expense_data))
        
        return expenses
    
    def _calculate_category_breakdown(
        self,
        expenses: List[Expense],
        budget_breakdown: Dict[str, float]
    ) -> List[ExpenseCategory]:
        """Calculate spending breakdown by category"""
        # Group expenses by category
        category_spending = defaultdict(float)
        category_counts = defaultdict(int)
        
        for expense in expenses:
            category_spending[expense.category] += expense.amount
            category_counts[expense.category] += 1
        
        # Create category objects
        categories = []
        for cat_name, budgeted in budget_breakdown.items():
            spent = category_spending.get(cat_name, 0)
            remaining = budgeted - spent
            percentage = (spent / budgeted * 100) if budgeted > 0 else 0
            
            categories.append(ExpenseCategory(
                name=cat_name,
                budgeted_amount=budgeted,
                spent_amount=spent,
                remaining_amount=remaining,
                percentage_used=round(percentage, 2),
                expense_count=category_counts.get(cat_name, 0)
            ))
        
        # Add categories with spending but no budget
        for cat_name, spent in category_spending.items():
            if cat_name not in budget_breakdown:
                categories.append(ExpenseCategory(
                    name=cat_name,
                    budgeted_amount=0,
                    spent_amount=spent,
                    remaining_amount=-spent,
                    percentage_used=100.0,
                    expense_count=category_counts[cat_name]
                ))
        
        return categories
    
    def _generate_budget_warnings(
        self,
        total_budget: float,
        total_spent: float,
        percentage_used: float,
        categories: List[ExpenseCategory],
        days_remaining: int,
        projected_total: float
    ) -> List[str]:
        """Generate budget warnings based on current spending"""
        warnings = []
        
        # Overall budget warnings with replan triggers
        if percentage_used >= 100:
            over_amount = total_spent - total_budget
            warnings.append(
                f"🔴 BUDGET EXCEEDED! You've spent ₹{over_amount:,.2f} over budget."
            )
            warnings.append(
                f"🔄 AUTOMATIC REPLANNING TRIGGERED: AI will adjust your remaining itinerary to fit remaining budget."
            )
        elif percentage_used >= 90:
            warnings.append(
                f"⚠️ CRITICAL: You've used {percentage_used:.1f}% of your budget!"
            )
            if days_remaining > 2:
                warnings.append(
                    f"🔄 REPLANNING RECOMMENDED: With {days_remaining} days left, consider replanning to avoid overspending."
                )
        elif percentage_used >= 75:
            warnings.append(
                f"⚠️ WARNING: {percentage_used:.1f}% of budget used with {days_remaining} days left."
            )
        
        # Projection warning with automatic replanning trigger
        if projected_total > total_budget * 1.2:  # 20% overage projection
            overage = projected_total - total_budget
            warnings.append(
                f"📊 At current rate, you'll exceed budget by ₹{overage:,.2f}"
            )
            warnings.append(
                f"🤖 AUTOMATIC REPLANNING AVAILABLE: Click 'Replan Trip' to get AI-adjusted itinerary for remaining days."
            )
        elif projected_total > total_budget:
            overage = projected_total - total_budget
            warnings.append(
                f"� At current rate, you'll exceed budget by ₹{overage:,.2f}"
            )
        
        # Category-specific warnings
        for category in categories:
            if category.percentage_used >= 100:
                warnings.append(
                    f"🔴 {category.name}: Budget exceeded! Consider cheaper alternatives."
                )
            elif category.percentage_used >= 90:
                warnings.append(
                    f"⚠️ {category.name}: {category.percentage_used:.1f}% used - switch to budget options"
                )
        
        return warnings
    
    def _generate_spending_recommendations(
        self,
        budget_status: str,
        categories: List[ExpenseCategory],
        daily_average: float,
        days_remaining: int,
        total_remaining: float
    ) -> List[str]:
        """Generate AI-powered spending recommendations"""
        recommendations = []
        
        if budget_status == "over-budget":
            recommendations.append(
                "💡 URGENT: Reduce spending immediately. Consider free activities and local markets."
            )
            recommendations.append(
                "🏠 ACCOMMODATION: Switch to budget hotels, hostels, or homestays immediately."
            )
            recommendations.append(
                "🍜 FOOD: Eat at local dhabas/street food stalls, avoid restaurants. Cook if possible."
            )
            recommendations.append(
                "🚌 TRANSPORT: Use public transport, shared autos instead of private taxis."
            )
            recommendations.append(
                "🎯 ACTIVITIES: Cancel paid activities, focus on free sightseeing, parks, temples."
            )
            recommendations.append(
                "🔄 REPLAN: Consider shortening trip or moving to cheaper nearby destinations."
            )
        
        elif budget_status == "critical":
            daily_limit = total_remaining / max(days_remaining, 1)
            recommendations.append(
                f"💡 STRICT LIMIT: Spend maximum ₹{daily_limit:,.2f} per day for remaining {days_remaining} days."
            )
            recommendations.append(
                "🎯 PRIORITIZE: Keep only must-see attractions, cut all optional activities."
            )
            recommendations.append(
                "🍽️ FOOD: Maximum ₹200-300 per meal. Choose local eateries over tourist restaurants."
            )
            recommendations.append(
                "🏨 DOWNGRADE: Move to cheaper accommodation if current stay is expensive."
            )
            recommendations.append(
                "⚠️ TRACK EVERY EXPENSE: Log all spending immediately to stay aware."
            )
        
        elif budget_status == "warning":
            daily_recommended = total_remaining / max(days_remaining, 1)
            recommendations.append(
                f"💡 Recommended daily limit: ₹{daily_recommended:,.2f} to stay on track."
            )
            recommendations.append(
                "📊 Monitor spending closely. Review expenses daily."
            )
            recommendations.append(
                "🎯 Mix expensive and free activities. Balance your days."
            )
            recommendations.append(
                "🍜 Alternate between nice restaurants and budget meals."
            )
        
        else:  # on-track
            recommendations.append(
                "✅ You're on track! Keep up the good spending habits."
            )
            if total_remaining > daily_average * days_remaining:
                extra = total_remaining - (daily_average * days_remaining)
                recommendations.append(
                    f"🎉 You have ₹{extra:,.2f} extra! Consider splurging on a special experience."
                )
                recommendations.append(
                    "🌟 Ideas: Upgrade to a luxury hotel night, book a special activity, or try fine dining."
                )
        
        # Category-specific recommendations
        overspent_categories = [c for c in categories if c.percentage_used >= 90]
        if overspent_categories:
            cat_names = ", ".join(c.name for c in overspent_categories[:2])
            recommendations.append(
                f"⚠️ Reduce spending on: {cat_names}"
            )
        
        underspent_categories = [c for c in categories if c.percentage_used < 50 and c.budgeted_amount > 0]
        if underspent_categories:
            cat_names = ", ".join(c.name for c in underspent_categories[:2])
            recommendations.append(
                f"💸 You can spend more on: {cat_names}"
            )
        
        return recommendations
    
    def _check_budget_alerts(
        self,
        trip_id: str,
        category: str,
        amount: float
    ):
        """Check if new expense triggers any budget alerts"""
        # Get current spending
        summary = self.get_expense_tracker(trip_id)
        
        # Check overall budget threshold
        if summary.percentage_used >= 75 and summary.percentage_used < 90:
            self._create_alert(trip_id, "warning", None, 
                             f"You've used {summary.percentage_used:.1f}% of your budget")
        elif summary.percentage_used >= 90:
            self._create_alert(trip_id, "critical", None,
                             f"CRITICAL: {summary.percentage_used:.1f}% of budget used!")
        
        # Check category threshold
        for cat in summary.categories:
            if cat.name == category and cat.percentage_used >= 90:
                self._create_alert(trip_id, "warning", category,
                                 f"{category} budget is {cat.percentage_used:.1f}% used")
    
    def _create_alert(
        self,
        trip_id: str,
        alert_type: str,
        category: Optional[str],
        message: str
    ):
        """Create a budget alert"""
        if not self.db:
            return
        
        alert = {
            'alert_id': f"alert_{uuid.uuid4().hex[:12]}",
            'trip_id': trip_id,
            'alert_type': alert_type,
            'category': category,
            'message': message,
            'created_at': datetime.now(timezone.utc),
            'is_read': False
        }
        
        self.db.collection('budget_alerts').add(alert)
    
    def _group_expenses(
        self,
        expenses: List[Expense],
        group_by: str
    ) -> List[Dict]:
        """Group expenses by specified field"""
        grouped = defaultdict(lambda: {"total": 0, "count": 0, "expenses": []})
        
        for expense in expenses:
            if group_by == "category":
                key = expense.category
            elif group_by == "day":
                key = expense.date.strftime('%Y-%m-%d')
            elif group_by == "location":
                key = expense.location or "Unknown"
            elif group_by == "payment_method":
                key = expense.payment_method or "Unknown"
            else:
                key = "Other"
            
            grouped[key]["total"] += expense.amount
            grouped[key]["count"] += 1
            grouped[key]["expenses"].append(expense.dict())
        
        # Convert to list of dicts
        result = []
        for key, data in grouped.items():
            result.append({
                group_by: key,
                "total_amount": round(data["total"], 2),
                "expense_count": data["count"],
                "average_amount": round(data["total"] / data["count"], 2)
            })
        
        # Sort by total amount descending
        result.sort(key=lambda x: x["total_amount"], reverse=True)
        
        return result
    
    def _analyze_spending_trend(self, expenses: List[Expense]) -> str:
        """Analyze spending trend over time"""
        if len(expenses) < 2:
            return "insufficient-data"
        
        # Sort by date
        sorted_expenses = sorted(expenses, key=lambda x: x.date)
        
        # Split into first half and second half
        mid = len(sorted_expenses) // 2
        first_half = sorted_expenses[:mid]
        second_half = sorted_expenses[mid:]
        
        first_half_total = sum(e.amount for e in first_half)
        second_half_total = sum(e.amount for e in second_half)
        
        # Calculate average per day
        first_days = (first_half[-1].date - first_half[0].date).days or 1
        second_days = (second_half[-1].date - second_half[0].date).days or 1
        
        first_daily = first_half_total / first_days
        second_daily = second_half_total / second_days
        
        if second_daily > first_daily * 1.2:
            return "increasing"
        elif second_daily < first_daily * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _generate_analytics_insights(
        self,
        grouped_data: List[Dict],
        expenses: List[Expense],
        group_by: str
    ) -> List[str]:
        """Generate insights from analytics data"""
        insights = []
        
        if not grouped_data:
            return ["No expenses logged yet."]
        
        # Top spending area
        top_group = grouped_data[0]
        insights.append(
            f"💰 Highest spending: {top_group[group_by]} (₹{top_group['total_amount']:,.2f})"
        )
        
        # Average expense amount
        total_expenses = sum(g['expense_count'] for g in grouped_data)
        total_amount = sum(g['total_amount'] for g in grouped_data)
        avg_expense = total_amount / total_expenses if total_expenses > 0 else 0
        
        insights.append(
            f"📊 Average expense: ₹{avg_expense:,.2f}"
        )
        
        # Most frequent expense type
        if grouped_data:
            most_frequent = max(grouped_data, key=lambda x: x['expense_count'])
            insights.append(
                f"🔄 Most frequent: {most_frequent[group_by]} ({most_frequent['expense_count']} times)"
            )
        
        # Spending pattern
        if group_by == "day" and len(grouped_data) >= 3:
            amounts = [g['total_amount'] for g in grouped_data]
            if amounts[-1] > amounts[0] * 1.5:
                insights.append("📈 Spending is increasing over time")
            elif amounts[-1] < amounts[0] * 0.7:
                insights.append("📉 Spending is decreasing over time")
        
        return insights
    
    def should_trigger_replan(self, trip_id: str) -> Dict:
        """
        Check if automatic replanning should be triggered based on spending.
        Returns dict with trigger status and reasons.
        """
        try:
            summary = self.get_expense_tracker(trip_id)
            
            should_replan = False
            reasons = []
            
            # Trigger 1: Budget exceeded
            if summary.percentage_used >= 100:
                should_replan = True
                reasons.append("Budget fully exhausted")
            
            # Trigger 2: Critical overspending with days remaining
            elif summary.percentage_used >= 90 and summary.days_remaining > 2:
                should_replan = True
                reasons.append(f"90% budget used with {summary.days_remaining} days left")
            
            # Trigger 3: Projected overage > 20%
            elif summary.projected_total > summary.total_budget * 1.2:
                should_replan = True
                overage_pct = ((summary.projected_total - summary.total_budget) / summary.total_budget) * 100
                reasons.append(f"Projected to exceed budget by {overage_pct:.0f}%")
            
            # Trigger 4: Multiple categories overspent
            overspent_categories = [c.name for c in summary.categories if c.percentage_used >= 100]
            if len(overspent_categories) >= 2:
                should_replan = True
                reasons.append(f"Multiple categories overspent: {', '.join(overspent_categories)}")
            
            return {
                "should_replan": should_replan,
                "reasons": reasons,
                "remaining_budget": summary.total_remaining,
                "days_remaining": summary.days_remaining,
                "current_daily_rate": summary.daily_average,
                "recommended_daily_rate": summary.total_remaining / max(summary.days_remaining, 1) if summary.days_remaining > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Error checking replan trigger: {e}")
            return {
                "should_replan": False,
                "reasons": [],
                "error": str(e)
            }


def get_expense_tracker_service(firestore_client=None):
    """Factory function to get expense tracker service instance"""
    return ExpenseTrackerService(firestore_client)
