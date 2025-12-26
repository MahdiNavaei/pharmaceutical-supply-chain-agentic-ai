"""
Inventory Matching Agent for Pharmaceutical Supply Chain Agentic AI

This agent analyzes inventory levels across branches and recommends
stock transfers using AI analysis for optimal balancing.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Install with: pip install openai")

from utils.database import get_database

class InventoryMatchingAgent:
    """
    Agent for optimizing inventory distribution across branches

    Uses AI analysis to:
    - Identify overstock and understock situations
    - Calculate transfer costs and benefits
    - Recommend optimal stock transfers
    - Consider demand patterns and seasonality
    """

    def __init__(self):
        if OPENAI_AVAILABLE:
            # Load API key from env.txt file
            api_key = self._load_api_key()
            if api_key:
                self.client = OpenAI(api_key=api_key)
                self.llm_model = "gpt-4o-mini"
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OPENAI_API_KEY not found in env.txt")
                self.client = None
        else:
            self.client = None

    def _load_api_key(self):
        """Load API key from env.txt file"""
        try:
            with open('env.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('OPENAI_API_KEY='):
                        return line.split('=', 1)[1]
            return None
        except FileNotFoundError:
            return None

    def find_matches(self, item_id: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find optimal inventory transfers for a pharmaceutical item

        Args:
            item_id: ID of the item to analyze
            policy: Inventory policy parameters

        Returns:
            Dictionary containing transfer recommendations
        """
        try:
            logger.info(f"Finding inventory matches for item: {item_id}")

            # Get inventory data
            inventory_data = self._get_inventory_data(item_id)
            if not inventory_data:
                return self._empty_response("No inventory data found")

            # Analyze inventory levels
            analysis = self._analyze_inventory_levels(inventory_data, policy)

            # Use AI for intelligent recommendations
            ai_recommendations = self._get_ai_recommendations(inventory_data, analysis, policy)

            # Generate transfer recommendations
            transfers = self._generate_transfers(inventory_data, analysis, ai_recommendations)

            # Calculate total savings
            total_savings = sum(t.get('expected_savings', 0) for t in transfers)

            return {
                "matches": transfers,
                "total_matches": len(transfers),
                "total_savings": total_savings,
                "analysis": analysis,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error in inventory matching: {e}")
            return self._error_response(str(e))

    def _get_inventory_data(self, item_id: str) -> List[Dict[str, Any]]:
        """Get current inventory data for an item across all branches"""
        try:
            db = get_database()
            # Query inventory for this item
            query = {"drug_id": item_id.lower()}  # Case insensitive match

            inventory_records = list(db.inventory.find(query))
            logger.info(f"Found {len(inventory_records)} inventory records for {item_id}")

            return inventory_records

        except Exception as e:
            logger.error(f"Error getting inventory data: {e}")
            return []

    def _analyze_inventory_levels(self, inventory_data: List[Dict[str, Any]],
                                policy: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze inventory levels and identify imbalances"""
        try:
            safe_days = policy.get('safe_days', 14)

            overstock = []
            understock = []
            balanced = []

            for item in inventory_data:
                current_stock = item.get('current_stock', 0)
                optimal_stock = item.get('optimal_stock', 0)
                safe_stock = item.get('safe_stock', optimal_stock * 0.2)  # 20% safety stock

                if current_stock > optimal_stock * 1.2:  # Over 20% above optimal
                    overstock.append({
                        "branch_id": item.get('branch_id'),
                        "current_stock": current_stock,
                        "optimal_stock": optimal_stock,
                        "excess": current_stock - optimal_stock,
                        "severity": "high" if current_stock > optimal_stock * 1.5 else "medium"
                    })
                elif current_stock < safe_stock:  # Below safety stock
                    understock.append({
                        "branch_id": item.get('branch_id'),
                        "current_stock": current_stock,
                        "safe_stock": safe_stock,
                        "deficit": safe_stock - current_stock,
                        "severity": "critical" if current_stock < safe_stock * 0.5 else "warning"
                    })
                else:
                    balanced.append({
                        "branch_id": item.get('branch_id'),
                        "current_stock": current_stock,
                        "optimal_stock": optimal_stock
                    })

            return {
                "overstock_branches": overstock,
                "understock_branches": understock,
                "balanced_branches": balanced,
                "total_overstock_quantity": sum(o['excess'] for o in overstock),
                "total_understock_quantity": sum(u['deficit'] for u in understock)
            }

        except Exception as e:
            logger.error(f"Error analyzing inventory levels: {e}")
            return {}

    def _get_ai_recommendations(self, inventory_data: List[Dict[str, Any]],
                              analysis: Dict[str, Any], policy: Dict[str, Any]) -> str:
        """Get AI-powered recommendations for inventory transfers"""
        if not self.client:
            return "AI analysis not available - using rule-based approach"

        try:
            # Prepare data for AI analysis
            overstock_info = "\n".join([
                f"- Branch {o['branch_id']}: {o['excess']} units excess (current: {o['current_stock']}, optimal: {o['optimal_stock']})"
                for o in analysis.get('overstock_branches', [])
            ])

            understock_info = "\n".join([
                f"- Branch {u['branch_id']}: {u['deficit']} units deficit (current: {u['current_stock']}, safe: {u['safe_stock']})"
                for u in analysis.get('understock_branches', [])
            ])

            prompt = f"""
You are an expert pharmaceutical supply chain analyst. Analyze this inventory situation and provide strategic recommendations for stock transfers.

INVENTORY ANALYSIS:
- Total overstock quantity: {analysis.get('total_overstock_quantity', 0)}
- Total understock quantity: {analysis.get('total_understock_quantity', 0)}

OVERSTOCK BRANCHES:
{overstock_info}

UNDERSTOCK BRANCHES:
{understock_info}

POLICY PARAMETERS:
- Safe stock days: {policy.get('safe_days', 14)}
- Maximum transfer distance consideration: 500km
- Transfer cost per unit: $0.50
- Holding cost per unit per month: $2.00

Provide strategic recommendations for:
1. Priority transfer pairs (which branches should transfer to which)
2. Transfer quantities that maximize efficiency
3. Risk considerations (stockouts, transportation, etc.)
4. Expected benefits and cost savings

Be specific and actionable in your recommendations.
"""

            try:
                response = self.client.chat.completions.create(
                    model=self.llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0.3
                )

                ai_analysis = response.choices[0].message.content
            except Exception as e:
                logger.warning(f"LLM API call failed: {e}")
                ai_analysis = "LLM analysis not available due to API error"
            logger.info("AI analysis completed for inventory matching")
            return ai_analysis

        except Exception as e:
            logger.error(f"Error getting AI recommendations: {e}")
            return f"AI analysis failed: {str(e)}"

    def _generate_transfers(self, inventory_data: List[Dict[str, Any]],
                          analysis: Dict[str, Any], ai_recommendations: str) -> List[Dict[str, Any]]:
        """Generate specific transfer recommendations"""
        try:
            transfers = []
            overstock = analysis.get('overstock_branches', [])
            understock = analysis.get('understock_branches', [])

            # Simple matching algorithm: pair closest overstock with understock
            for under in understock:
                for over in overstock:
                    if over['excess'] > 0 and under['deficit'] > 0:
                        # Calculate transfer quantity (min of excess and deficit)
                        transfer_qty = min(over['excess'], under['deficit'])

                        # Calculate costs and savings
                        transfer_cost = transfer_qty * 0.5  # $0.50 per unit
                        holding_cost_saved = transfer_qty * 2.0  # $2.00 per unit per month
                        expected_savings = holding_cost_saved - transfer_cost

                        if expected_savings > 0:  # Only recommend profitable transfers
                            transfer = {
                                "from_branch": over['branch_id'],
                                "to_branch": under['branch_id'],
                                "item_id": inventory_data[0].get('drug_id'),  # Assume same item
                                "quantity": transfer_qty,
                                "transfer_cost": transfer_cost,
                                "expected_savings": expected_savings,
                                "priority": "high" if under['severity'] == "critical" else "medium",
                                "ai_insights": ai_recommendations[:200] + "..." if len(ai_recommendations) > 200 else ai_recommendations
                            }

                            transfers.append(transfer)

                            # Update quantities
                            over['excess'] -= transfer_qty
                            under['deficit'] -= transfer_qty

                            if len(transfers) >= 10:  # Limit to top 10 recommendations
                                break

                if len(transfers) >= 10:
                    break

            # Sort by priority and savings
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            transfers.sort(key=lambda x: (priority_order.get(x['priority'], 3), -x['expected_savings']))

            return transfers[:10]  # Return top 10

        except Exception as e:
            logger.error(f"Error generating transfers: {e}")
            return []

    def _empty_response(self, message: str) -> Dict[str, Any]:
        """Return empty response when no data is available"""
        return {
            "matches": [],
            "total_matches": 0,
            "total_savings": 0,
            "analysis": {},
            "status": "no_data",
            "message": message
        }

    def _error_response(self, error_msg: str) -> Dict[str, Any]:
        """Return error response"""
        return {
            "matches": [],
            "total_matches": 0,
            "total_savings": 0,
            "analysis": {},
            "status": "error",
            "message": error_msg
        }
