"""
Monitoring Agent for Pharmaceutical Supply Chain Agentic AI

Monitors inventory levels and generates alerts for stockouts, overstock,
demand anomalies, and other supply chain issues.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Install with: pip install openai")

from utils.database import get_database


class MonitoringAgent:
    """
    Agent for monitoring pharmaceutical inventory and generating alerts
    """

    def __init__(self):
        self.client = None
        self.llm_model = "gpt-4o-mini"

        if OPENAI_AVAILABLE:
            api_key = self._load_api_key()
            if api_key:
                try:
                    self.client = OpenAI(api_key=api_key)
                    logger.info("OpenAI client initialized for monitoring")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI client, AI insights disabled: {e}")
                    self.client = None
            else:
                logger.info("OPENAI_API_KEY not provided; AI insights disabled for monitoring")

        # Alert thresholds
        self.thresholds = {
            "critical_stockout_days": 2,
            "warning_stockout_days": 7,
            "overstock_multiplier": 1.5,
            "understock_multiplier": 0.3,
            "demand_anomaly_threshold": 2.0
        }

    def _load_api_key(self) -> Optional[str]:
        """Load API key from env vars (.env) or env.txt; ignore placeholders"""
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key and env_key not in ("", "your_api_key_here"):
            return env_key

        for filename in [".env", "env.txt"]:
            try:
                with open(filename, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("OPENAI_API_KEY="):
                            candidate = line.split("=", 1)[1]
                            if candidate and candidate != "your_api_key_here":
                                return candidate
            except FileNotFoundError:
                continue
        return None

    def generate_alerts(self, severity_filter: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Generate inventory alerts based on current stock levels"""
        try:
            logger.info(f"Generating alerts, severity_filter: {severity_filter}, limit: {limit}")

            inventory_data = self._get_all_inventory()
            alerts: List[Dict[str, Any]] = []

            for item in inventory_data:
                alerts.extend(self._analyze_inventory_item(item))

            if severity_filter:
                alerts = [a for a in alerts if a["severity"] == severity_filter]

            severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
            alerts.sort(key=lambda x: (severity_order.get(x["severity"], 3), x["timestamp"]))

            alerts = alerts[:limit]
            summary = self._generate_summary(alerts)

            if self.client and alerts:
                ai_insights = self._get_ai_alert_insights(alerts[:10])
            else:
                ai_insights = "AI analysis not available"

            return {
                "alerts": alerts,
                "total_alerts": len(alerts),
                "summary": summary,
                "ai_insights": ai_insights,
                "generated_at": datetime.utcnow(),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
            return self._error_response(str(e))

    def _get_all_inventory(self) -> List[Dict[str, Any]]:
        try:
            db = get_database()
            inventory = list(db.inventory.find({}))
            logger.info(f"Retrieved {len(inventory)} inventory records for monitoring")
            return inventory
        except Exception as e:
            logger.error(f"Error getting inventory data: {e}")
            return []

    def _analyze_inventory_item(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            alerts = []

            current_stock = item.get("current_stock", 0)
            optimal_stock = item.get("optimal_stock", 0)
            safe_stock = item.get("safe_stock", 0)
            branch_id = item.get("branch_id", "UNKNOWN")
            drug_id = item.get("drug_id", "UNKNOWN")

            avg_daily_demand = item.get("demand_forecast", 0) / 30 if item.get("demand_forecast", 0) > 0 else 10
            days_until_stockout = current_stock / avg_daily_demand if avg_daily_demand > 0 else 999

            if days_until_stockout <= self.thresholds["critical_stockout_days"]:
                alerts.append({
                    "severity": "CRITICAL",
                    "branch_id": branch_id,
                    "item_id": drug_id,
                    "alert_type": "STOCKOUT_RISK",
                    "current_stock": current_stock,
                    "days_until_stockout": round(days_until_stockout, 1),
                    "recommended_action": "URGENT_ORDER",
                    "message": f"Critical stockout risk: {days_until_stockout:.1f} days remaining",
                    "timestamp": datetime.utcnow(),
                    "is_resolved": False
                })
            elif days_until_stockout <= self.thresholds["warning_stockout_days"]:
                alerts.append({
                    "severity": "WARNING",
                    "branch_id": branch_id,
                    "item_id": drug_id,
                    "alert_type": "LOW_STOCK",
                    "current_stock": current_stock,
                    "days_until_stockout": round(days_until_stockout, 1),
                    "recommended_action": "ORDER_SOON",
                    "message": f"Low stock warning: {days_until_stockout:.1f} days remaining",
                    "timestamp": datetime.utcnow(),
                    "is_resolved": False
                })

            if current_stock > optimal_stock * self.thresholds["overstock_multiplier"]:
                excess_quantity = current_stock - optimal_stock
                alerts.append({
                    "severity": "WARNING",
                    "branch_id": branch_id,
                    "item_id": drug_id,
                    "alert_type": "OVERSTOCK",
                    "current_stock": current_stock,
                    "optimal_stock": optimal_stock,
                    "excess_quantity": excess_quantity,
                    "recommended_action": "REDISTRIBUTE",
                    "message": f"Overstock: {excess_quantity} units above optimal level",
                    "timestamp": datetime.utcnow(),
                    "is_resolved": False
                })

            if current_stock < safe_stock * self.thresholds["understock_multiplier"]:
                deficit_quantity = safe_stock - current_stock
                alerts.append({
                    "severity": "INFO",
                    "branch_id": branch_id,
                    "item_id": drug_id,
                    "alert_type": "UNDERSTOCK",
                    "current_stock": current_stock,
                    "safe_stock": safe_stock,
                    "deficit_quantity": deficit_quantity,
                    "recommended_action": "CHECK_INVENTORY",
                    "message": f"Understock: {deficit_quantity} units below safe level",
                    "timestamp": datetime.utcnow(),
                    "is_resolved": False
                })

            return alerts
        except Exception as e:
            logger.error(f"Error analyzing inventory item {item.get('drug_id')}: {e}")
            return []

    def _generate_summary(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            total = len(alerts)
            critical = len([a for a in alerts if a["severity"] == "CRITICAL"])
            warning = len([a for a in alerts if a["severity"] == "WARNING"])
            info = len([a for a in alerts if a["severity"] == "INFO"])

            branch_counts: Dict[str, int] = {}
            for alert in alerts:
                branch = alert["branch_id"]
                branch_counts[branch] = branch_counts.get(branch, 0) + 1

            top_branches = sorted(branch_counts.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                "total_alerts": total,
                "critical_count": critical,
                "warning_count": warning,
                "info_count": info,
                "top_affected_branches": top_branches,
                "alert_types": list(set(a["alert_type"] for a in alerts))
            }
        except Exception as e:
            logger.error(f"Error generating alert summary: {e}")
            return {}

    def _get_ai_alert_insights(self, alerts: List[Dict[str, Any]]) -> str:
        if not self.client or not alerts:
            return "AI analysis not available"

        try:
            alert_summary = f"""
Total alerts: {len(alerts)}

Critical alerts: {len([a for a in alerts if a['severity'] == 'CRITICAL'])}
Warning alerts: {len([a for a in alerts if a['severity'] == 'WARNING'])}
Info alerts: {len([a for a in alerts if a['severity'] == 'INFO'])}

Top alert types: {list(set(a['alert_type'] for a in alerts))[:3]}

Sample alerts:
"""

            for i, alert in enumerate(alerts[:5]):
                alert_summary += f"""
{i+1}. {alert['severity']} - {alert['branch_id']}: {alert['message']}
   Action: {alert['recommended_action']}
"""

            prompt = f"""
You are a pharmaceutical supply chain expert analyzing inventory alerts.

{alert_summary}

Provide strategic insights and recommendations:
1. What are the main patterns in these alerts?
2. What immediate actions should be prioritized?
3. What systemic issues might be causing these alerts?
4. Recommendations for preventing similar issues in the future.

Be concise but actionable in your analysis.
"""

            try:
                response = self.client.chat.completions.create(
                    model=self.llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.2
                )
                return response.choices[0].message.content
            except Exception as e:
                err_text = str(e)
                if "invalid_api_key" in err_text or "401" in err_text:
                    logger.warning("OpenAI API key invalid; disabling AI insights.")
                    self.client = None
                else:
                    logger.warning(f"LLM API call failed: {e}")
                return "AI analysis not available due to API error"
        except Exception as e:
            logger.error(f"Error getting AI alert insights: {e}")
            return f"AI analysis failed: {str(e)}"

    def _error_response(self, error_msg: str) -> Dict[str, Any]:
        return {
            "alerts": [],
            "total_alerts": 0,
            "summary": {},
            "ai_insights": "",
            "status": "error",
            "message": error_msg
        }
