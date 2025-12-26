"""
LangGraph Workflow for Pharmaceutical Supply Chain Agentic AI

This module orchestrates all agents using LangGraph for intelligent
decision making and workflow management.
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
    logger.info("LangGraph successfully imported")
except ImportError as e:
    LANGGRAPH_AVAILABLE = False
    logger.warning(f"LangGraph not available: {e}. Install with: pip install langgraph")

# Import all agents
from .forecasting_agent import ForecastingAgent
from .route_optimization_agent import RouteOptimizationAgent
from .inventory_matching_agent import InventoryMatchingAgent
from .monitoring_agent import MonitoringAgent

class SupplyChainState(TypedDict):
    """Global state for the supply chain workflow"""
    # Input parameters
    item_id: Optional[str]
    depot_id: Optional[str]
    destinations: Optional[List[str]]
    horizon_days: int
    policy: Optional[Dict[str, Any]]

    # Agent outputs
    demand_forecast: Optional[Dict[str, Any]]
    route_plan: Optional[Dict[str, Any]]
    transfer_plan: Optional[Dict[str, Any]]
    alerts: Optional[List[Dict[str, Any]]]

    # Workflow metadata
    agent_logs: List[Dict[str, Any]]
    kpi_metrics: Dict[str, Any]
    workflow_status: str
    error_message: Optional[str]

class SupplyChainWorkflow:
    """
    LangGraph-based workflow for orchestrating supply chain agents

    The workflow intelligently decides which agents to run based on:
    - Input parameters
    - Previous agent results
    - Business rules and thresholds
    """

    def __init__(self):
        if not LANGGRAPH_AVAILABLE:
            logger.warning("LangGraph not available, using simplified workflow")
            self.graph = None
        else:
            # Initialize workflow graph
            self.graph = self._build_workflow_graph()

        self.forecasting_agent = ForecastingAgent()
        self.route_agent = RouteOptimizationAgent()
        self.inventory_agent = InventoryMatchingAgent()
        self.monitoring_agent = MonitoringAgent()

        # Initialize workflow graph
        self.graph = self._build_workflow_graph()

    def _build_workflow_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(SupplyChainState)

        # Add nodes (agent functions)
        workflow.add_node("forecasting_agent", self._run_forecasting)
        workflow.add_node("inventory_analysis", self._run_inventory_analysis)
        workflow.add_node("route_optimization", self._run_route_optimization)
        workflow.add_node("transfer_matching", self._run_transfer_matching)
        workflow.add_node("monitoring_alerts", self._run_monitoring)
        workflow.add_node("final_summary", self._generate_summary)

        # Define conditional routing logic
        def should_run_forecasting(state: SupplyChainState) -> str:
            """Decide if forecasting should run"""
            if state.get("item_id") and not state.get("demand_forecast"):
                return "forecasting_agent"
            return "inventory_analysis"

        def should_run_route_optimization(state: SupplyChainState) -> str:
            """Decide if route optimization should run"""
            if (state.get("depot_id") and state.get("destinations") and
                len(state.get("destinations", [])) > 0):
                return "route_optimization"
            return "transfer_matching"

        def should_run_inventory_matching(state: SupplyChainState) -> str:
            """Decide if inventory matching should run"""
            if state.get("item_id"):
                return "transfer_matching"
            return "monitoring_alerts"

        def should_run_monitoring(state: SupplyChainState) -> str:
            """Always run monitoring for alerts"""
            return "monitoring_alerts"

        # Add conditional edges
        workflow.add_conditional_edges(
            "forecasting_agent",
            should_run_forecasting,
            {
                "forecasting_agent": "forecasting_agent",
                "inventory_analysis": "inventory_analysis"
            }
        )

        workflow.add_conditional_edges(
            "inventory_analysis",
            should_run_route_optimization,
            {
                "route_optimization": "route_optimization",
                "transfer_matching": "transfer_matching"
            }
        )

        workflow.add_conditional_edges(
            "route_optimization",
            should_run_inventory_matching,
            {
                "transfer_matching": "transfer_matching",
                "monitoring_alerts": "monitoring_alerts"
            }
        )

        workflow.add_conditional_edges(
            "transfer_matching",
            should_run_monitoring,
            {
                "monitoring_alerts": "monitoring_alerts"
            }
        )

        # Always go to final summary
        workflow.add_edge("monitoring_alerts", "final_summary")
        workflow.add_edge("final_summary", END)

        # Set entry point
        workflow.set_entry_point("forecasting_agent")

        # Add memory for state persistence
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    def run_workflow(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the supply chain workflow

        Args:
            initial_state: Initial workflow state

        Returns:
            Final workflow state with all results
        """
        try:
            logger.info("Starting supply chain workflow")

            # If LangGraph is not available, run simplified workflow
            if not LANGGRAPH_AVAILABLE or self.graph is None:
                return self._run_simplified_workflow(initial_state)

            # Prepare initial state
            state = SupplyChainState(
                item_id=initial_state.get("item_id"),
                depot_id=initial_state.get("depot_id"),
                destinations=initial_state.get("destinations", []),
                horizon_days=initial_state.get("horizon_days", 30),
                policy=initial_state.get("policy", {"safe_days": 14}),
                demand_forecast=None,
                route_plan=None,
                transfer_plan=None,
                alerts=None,
                agent_logs=[],
                kpi_metrics={},
                workflow_status="running",
                error_message=None
            )

            # Run workflow
            config = {"configurable": {"thread_id": f"supply_chain_{datetime.utcnow().timestamp()}"}}
            final_state = None

            for output in self.graph.stream(state, config=config):
                for node_name, node_state in output.items():
                    logger.info(f"Completed node: {node_name}")
                    final_state = node_state

            if final_state:
                final_state["workflow_status"] = "completed"
                logger.info("Workflow completed successfully")
                return dict(final_state)
            else:
                return {
                    "workflow_status": "error",
                    "error_message": "Workflow did not produce final state"
                }

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "workflow_status": "error",
                "error_message": str(e)
            }

    def _run_simplified_workflow(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Run simplified workflow without LangGraph"""
        try:
            logger.info("Running simplified workflow (LangGraph not available)")

            # Initialize agents
            forecasting_agent = ForecastingAgent()
            route_agent = RouteOptimizationAgent()
            inventory_agent = InventoryMatchingAgent()
            monitoring_agent = MonitoringAgent()

            agent_logs = []
            results = {}

            # Run forecasting if item_id provided
            if initial_state.get("item_id"):
                try:
                    forecast_result = forecasting_agent.forecast(
                        drug_id=initial_state["item_id"],
                        horizon_days=initial_state.get("horizon_days", 30),
                        model="prophet"
                    )
                    results["demand_forecast"] = forecast_result
                    agent_logs.append({
                        "agent": "forecasting",
                        "timestamp": datetime.utcnow(),
                        "status": forecast_result.get("status", "unknown"),
                        "result": f"Generated forecast"
                    })
                except Exception as e:
                    logger.error(f"Forecasting failed: {e}")

            # Run route optimization if depot and destinations provided
            if (initial_state.get("depot_id") and
                initial_state.get("destinations") and
                len(initial_state.get("destinations", [])) > 0):
                try:
                    route_result = route_agent.optimize_route(
                        depot_id=initial_state["depot_id"],
                        destinations=initial_state["destinations"],
                        vehicle_capacity=500
                    )
                    results["route_plan"] = route_result
                    agent_logs.append({
                        "agent": "route_optimization",
                        "timestamp": datetime.utcnow(),
                        "status": route_result.get("status", "unknown"),
                        "result": f"Optimized route"
                    })
                except Exception as e:
                    logger.error(f"Route optimization failed: {e}")

            # Run inventory matching if item_id provided
            if initial_state.get("item_id"):
                try:
                    matching_result = inventory_agent.find_matches(
                        item_id=initial_state["item_id"],
                        policy=initial_state.get("policy", {"safe_days": 14})
                    )
                    results["transfer_plan"] = matching_result
                    agent_logs.append({
                        "agent": "inventory_matching",
                        "timestamp": datetime.utcnow(),
                        "status": matching_result.get("status", "unknown"),
                        "result": f"Found transfer recommendations"
                    })
                except Exception as e:
                    logger.error(f"Inventory matching failed: {e}")

            # Always run monitoring
            try:
                alerts_result = monitoring_agent.generate_alerts(limit=20)
                results["alerts"] = alerts_result.get("alerts", [])
                agent_logs.append({
                    "agent": "monitoring",
                    "timestamp": datetime.utcnow(),
                    "status": alerts_result.get("status", "unknown"),
                    "result": f"Generated alerts"
                })
            except Exception as e:
                logger.error(f"Monitoring failed: {e}")

            # Generate summary
            kpi_metrics = {
                "agents_executed": len(agent_logs),
                "workflow_duration": "completed",
            }

            return {
                "workflow_status": "completed",
                "agent_logs": agent_logs,
                "kpi_metrics": kpi_metrics,
                **results
            }

        except Exception as e:
            logger.error(f"Simplified workflow failed: {e}")
            return {
                "workflow_status": "error",
                "error_message": str(e)
            }

    def _run_forecasting(self, state: SupplyChainState) -> SupplyChainState:
        """Run forecasting agent"""
        try:
            logger.info("Running forecasting agent")

            if not state.get("item_id"):
                logger.warning("No item_id provided for forecasting")
                return state

            forecast_result = self.forecasting_agent.forecast(
                drug_id=state["item_id"],
                horizon_days=state.get("horizon_days", 30),
                model="prophet"
            )

            # Update state
            new_state = state.copy()
            new_state["demand_forecast"] = forecast_result

            # Log agent execution
            new_state["agent_logs"].append({
                "agent": "forecasting",
                "timestamp": datetime.utcnow(),
                "status": forecast_result.get("status", "unknown"),
                "result": f"Generated {len(forecast_result.get('forecast', []))} forecast points"
            })

            logger.info("Forecasting agent completed")
            return new_state

        except Exception as e:
            logger.error(f"Forecasting agent failed: {e}")
            new_state = state.copy()
            new_state["error_message"] = f"Forecasting failed: {str(e)}"
            return new_state

    def _run_inventory_analysis(self, state: SupplyChainState) -> SupplyChainState:
        """Analyze inventory levels (preprocessing for other agents)"""
        try:
            logger.info("Running inventory analysis")

            # This could include pre-analysis for routing or matching decisions
            new_state = state.copy()
            new_state["agent_logs"].append({
                "agent": "inventory_analysis",
                "timestamp": datetime.utcnow(),
                "status": "completed",
                "result": "Inventory analysis completed"
            })

            return new_state

        except Exception as e:
            logger.error(f"Inventory analysis failed: {e}")
            new_state = state.copy()
            new_state["error_message"] = f"Inventory analysis failed: {str(e)}"
            return new_state

    def _run_route_optimization(self, state: SupplyChainState) -> SupplyChainState:
        """Run route optimization agent"""
        try:
            logger.info("Running route optimization agent")

            if not (state.get("depot_id") and state.get("destinations")):
                logger.warning("Missing depot or destinations for route optimization")
                return state

            route_result = self.route_agent.optimize_route(
                depot_id=state["depot_id"],
                destinations=state["destinations"],
                vehicle_capacity=500,
                max_time_hours=8,
                objective="min_distance"
            )

            # Update state
            new_state = state.copy()
            new_state["route_plan"] = route_result

            # Log agent execution
            new_state["agent_logs"].append({
                "agent": "route_optimization",
                "timestamp": datetime.utcnow(),
                "status": route_result.get("status", "unknown"),
                "result": f"Optimized route with {len(route_result.get('sequence', []))} stops"
            })

            logger.info("Route optimization agent completed")
            return new_state

        except Exception as e:
            logger.error(f"Route optimization agent failed: {e}")
            new_state = state.copy()
            new_state["error_message"] = f"Route optimization failed: {str(e)}"
            return new_state

    def _run_transfer_matching(self, state: SupplyChainState) -> SupplyChainState:
        """Run inventory matching agent"""
        try:
            logger.info("Running inventory matching agent")

            if not state.get("item_id"):
                logger.warning("No item_id provided for inventory matching")
                return state

            matching_result = self.inventory_agent.find_matches(
                item_id=state["item_id"],
                policy=state.get("policy", {"safe_days": 14})
            )

            # Update state
            new_state = state.copy()
            new_state["transfer_plan"] = matching_result

            # Log agent execution
            new_state["agent_logs"].append({
                "agent": "inventory_matching",
                "timestamp": datetime.utcnow(),
                "status": matching_result.get("status", "unknown"),
                "result": f"Found {matching_result.get('total_matches', 0)} transfer recommendations"
            })

            logger.info("Inventory matching agent completed")
            return new_state

        except Exception as e:
            logger.error(f"Inventory matching agent failed: {e}")
            new_state = state.copy()
            new_state["error_message"] = f"Inventory matching failed: {str(e)}"
            return new_state

    def _run_monitoring(self, state: SupplyChainState) -> SupplyChainState:
        """Run monitoring agent"""
        try:
            logger.info("Running monitoring agent")

            alerts_result = self.monitoring_agent.generate_alerts(limit=20)

            # Update state
            new_state = state.copy()
            new_state["alerts"] = alerts_result.get("alerts", [])

            # Log agent execution
            new_state["agent_logs"].append({
                "agent": "monitoring",
                "timestamp": datetime.utcnow(),
                "status": alerts_result.get("status", "unknown"),
                "result": f"Generated {alerts_result.get('total_alerts', 0)} alerts"
            })

            logger.info("Monitoring agent completed")
            return new_state

        except Exception as e:
            logger.error(f"Monitoring agent failed: {e}")
            new_state = state.copy()
            new_state["error_message"] = f"Monitoring failed: {str(e)}"
            return new_state

    def _generate_summary(self, state: SupplyChainState) -> SupplyChainState:
        """Generate final workflow summary"""
        try:
            logger.info("Generating workflow summary")

            # Calculate KPIs
            kpi_metrics = {
                "forecast_accuracy": 0,  # Would be calculated from actual vs predicted
                "route_efficiency": state.get("route_plan", {}).get("savings_vs_baseline", "0%"),
                "inventory_optimization": state.get("transfer_plan", {}).get("total_savings", 0),
                "alerts_count": len(state.get("alerts", [])),
                "agents_executed": len(state.get("agent_logs", [])),
                "workflow_duration": "calculated",  # Would track actual duration
            }

            new_state = state.copy()
            new_state["kpi_metrics"] = kpi_metrics
            new_state["workflow_status"] = "completed"

            logger.info("Workflow summary generated")
            return new_state

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            new_state = state.copy()
            new_state["error_message"] = f"Summary generation failed: {str(e)}"
            return new_state
