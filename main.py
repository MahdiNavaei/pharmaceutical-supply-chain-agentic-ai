#!/usr/bin/env python3
"""
Pharmaceutical Supply Chain Agentic AI - FastAPI Backend

This is the main FastAPI application for the Agentic AI system
that optimizes pharmaceutical supply chain operations.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import hashlib
import json
import os

# Import API models
from models.api_models import (
    ForecastRequest, ForecastResponse,
    RouteOptimizationRequest, RouteOptimizationResponse,
    InventoryMatchingRequest, InventoryMatchingResponse,
    AlertResponse, DashboardKPIs, AlertSummary, HealthCheckResponse
)

# Simple in-memory cache for forecasts
forecast_cache = {}
CACHE_EXPIRY_MINUTES = 60

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_cache_key(request: ForecastRequest) -> str:
    """Generate cache key for forecast request"""
    request_dict = {
        "entity_type": request.entity_type,
        "entity_id": request.entity_id,
        "item_id": request.item_id,
        "horizon_days": request.horizon_days,
        "model": request.model
    }
    request_str = json.dumps(request_dict, sort_keys=True)
    return hashlib.md5(request_str.encode()).hexdigest()

def get_cached_forecast(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached forecast if still valid"""
    if cache_key in forecast_cache:
        cached_data = forecast_cache[cache_key]
        if datetime.utcnow() < cached_data["expiry"]:
            logger.info(f"Cache hit for forecast: {cache_key}")
            return cached_data["result"]
        else:
            # Remove expired cache
            del forecast_cache[cache_key]
    return None

def set_cached_forecast(cache_key: str, result: Dict[str, Any]):
    """Cache forecast result"""
    forecast_cache[cache_key] = {
        "result": result,
        "expiry": datetime.utcnow() + timedelta(minutes=CACHE_EXPIRY_MINUTES)
    }
    logger.info(f"Cached forecast result: {cache_key}")

# Create FastAPI app
app = FastAPI(
    title="Pharmaceutical Supply Chain Agentic AI",
    description="Agentic AI system for optimizing pharmaceutical supply chain operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API models are imported from models.api_models

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "service": "pharma-supply-chain-agentic-ai"
    }

# API v1 endpoints
@app.post("/api/v1/forecast/predict", response_model=ForecastResponse)
async def forecast_demand(request: ForecastRequest):
    """
    Forecast demand for a pharmaceutical item

    This endpoint uses the Forecasting Agent to predict future demand
    based on historical sales data.
    """
    try:
        from agents.forecasting_agent import ForecastingAgent
        import asyncio

        logger.info(f"Forecast request: {request}")

        # Check cache first
        cache_key = get_cache_key(request)
        cached_result = get_cached_forecast(cache_key)
        if cached_result:
            logger.info("Returning cached forecast result")
            return ForecastResponse(**cached_result)

        # Initialize forecasting agent
        agent = ForecastingAgent()

        # Run forecasting with timeout
        async def run_forecast():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: agent.forecast(
                drug_id=request.item_id,
                branch_id=request.entity_id if request.entity_type == "branch" else None,
                horizon_days=request.horizon_days,
                model=request.model
            ))

        try:
            result = await asyncio.wait_for(run_forecast(), timeout=120.0)  # 2 minute timeout
            # Cache the result
            set_cached_forecast(cache_key, result)
        except asyncio.TimeoutError:
            logger.error("Forecasting timeout")
            raise HTTPException(status_code=408, detail="Forecasting request timed out")

        # Convert result to response format
        forecast_data = []
        for item in result.get('forecast', []):
            forecast_data.append({
                'date': item['date'],
                'yhat': item['yhat'],
                'yhat_lower': item.get('yhat_lower'),
                'yhat_upper': item.get('yhat_upper')
            })

        response = ForecastResponse(**result)

        return response

    except Exception as e:
        logger.error(f"Error in forecast endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/routes/optimize", response_model=RouteOptimizationResponse)
async def optimize_routes(request: RouteOptimizationRequest):
    """
    Optimize delivery routes for pharmaceutical distribution

    This endpoint uses the Route Optimization Agent to find the most
    efficient delivery routes.
    """
    try:
        from agents.route_optimization_agent import RouteOptimizationAgent
        import asyncio

        logger.info(f"Route optimization request: {request}")

        # Initialize route optimization agent
        agent = RouteOptimizationAgent()

        # Run optimization with timeout
        async def run_optimization():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: agent.optimize_route(
                depot_id=request.depot_id,
                destinations=request.destinations,
                vehicle_capacity=request.vehicle_capacity,
                max_time_hours=request.max_time_hours,
                objective=request.objective
            ))

        try:
            result = await asyncio.wait_for(run_optimization(), timeout=60.0)  # 1 minute timeout
        except asyncio.TimeoutError:
            logger.error("Route optimization timeout")
            raise HTTPException(status_code=408, detail="Route optimization request timed out")

        return RouteOptimizationResponse(**result)

    except Exception as e:
        logger.error(f"Error in route optimization endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/inventory/match", response_model=InventoryMatchingResponse)
async def match_inventory(request: InventoryMatchingRequest):
    """
    Match inventory across branches to optimize stock levels

    This endpoint uses the Inventory Matching Agent with AI analysis to suggest
    transfers between branches.
    """
    try:
        from agents.inventory_matching_agent import InventoryMatchingAgent
        import asyncio

        logger.info(f"Inventory matching request: {request}")

        # Initialize inventory matching agent
        agent = InventoryMatchingAgent()

        # Run matching with timeout
        async def run_matching():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: agent.find_matches(
                item_id=request.item_id,
                policy=request.policy.dict()
            ))

        try:
            result = await asyncio.wait_for(run_matching(), timeout=90.0)  # 1.5 minute timeout
        except asyncio.TimeoutError:
            logger.error("Inventory matching timeout")
            raise HTTPException(status_code=408, detail="Inventory matching request timed out")

        return InventoryMatchingResponse(**result)

    except Exception as e:
        logger.error(f"Error in inventory matching endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/alerts", response_model=AlertResponse)
async def get_alerts(severity: Optional[str] = None, limit: int = 10):
    """
    Get inventory alerts and notifications

    This endpoint returns current alerts from the Monitoring Agent with AI insights.
    """
    try:
        from agents.monitoring_agent import MonitoringAgent
        import asyncio

        logger.info(f"Alerts request: severity={severity}, limit={limit}")

        # Initialize monitoring agent
        agent = MonitoringAgent()

        # Run monitoring with timeout
        async def run_monitoring():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: agent.generate_alerts(
                severity_filter=severity,
                limit=limit
            ))

        try:
            result = await asyncio.wait_for(run_monitoring(), timeout=60.0)  # 1 minute timeout
        except asyncio.TimeoutError:
            logger.error("Monitoring timeout")
            raise HTTPException(status_code=408, detail="Monitoring request timed out")

        # Convert alerts to expected format
        alerts = []
        for alert in result.get('alerts', []):
            alerts.append({
                "severity": alert.get('severity', 'INFO'),
                "branch_id": alert.get('branch_id', 'UNKNOWN'),
                "item_id": alert.get('item_id', 'UNKNOWN'),
                "alert_type": alert.get('alert_type', 'GENERAL'),
                "message": alert.get('message', 'Alert generated by monitoring agent'),
                "current_stock": alert.get('current_stock', 0),
                "days_until_stockout": alert.get('days_until_stockout', 0),
                "recommended_action": alert.get('recommended_action', 'REVIEW'),
                "timestamp": alert.get('timestamp', datetime.utcnow()),
                "is_resolved": alert.get('is_resolved', False)
            })

        return AlertResponse(
            alerts=alerts,
            total_alerts=result.get('total_alerts', 0),
            critical_count=result.get('summary', {}).get('critical_count', 0),
            warning_count=result.get('summary', {}).get('warning_count', 0),
            info_count=result.get('summary', {}).get('info_count', 0),
            ai_insights=result.get('ai_insights', ''),
            status=result.get('status', 'unknown'),
            message=result.get('message'),
            generated_at=result.get('generated_at')
        )

    except Exception as e:
        logger.error(f"Error in alerts endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard endpoints
@app.get("/api/v1/dashboard/kpi")
async def get_dashboard_kpi():
    """Get dashboard KPI data"""
    try:
        # TODO: Calculate real KPIs from data
        return {
            "forecast_accuracy": {"value": 92.0, "change": 2.1, "unit": "%"},
            "route_savings": {"value": 1250000, "change": 15.3, "unit": "USD"},
            "stockout_reduction": {"value": 67.0, "change": -5.2, "unit": "%"},
            "response_time": {"value": 245, "change": -8, "unit": "ms"},
            "last_updated": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error in dashboard KPI endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard/kpis")
async def get_dashboard_kpis():
    """Get dashboard KPI data in the format used by the UI"""
    try:
        return {
            "total_forecast_accuracy": 92.0,
            "inventory_turnover": 12.8,
            "delivery_on_time": 97.5,
            "stockout_reduction": 67.0,
            "cost_savings": 1250000,
            "alerts_critical": 3,
            "alerts_warning": 12,
            "system_health": "healthy"
        }
    except Exception as e:
        logger.error(f"Error in dashboard KPIs endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard/alerts/summary")
async def get_alerts_summary():
    """Get alerts summary for dashboard"""
    try:
        # TODO: Get real alerts summary
        return {
            "critical": 3,
            "warning": 12,
            "info": 25,
            "total": 40,
            "last_updated": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error in alerts summary endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# LangGraph Workflow Endpoint
@app.post("/api/v1/workflow/execute")
async def execute_workflow(item_id: Optional[str] = None,
                          depot_id: Optional[str] = None,
                          destinations: Optional[str] = None,
                          horizon_days: int = 30):
    """
    Execute complete supply chain optimization workflow

    This endpoint runs all agents in orchestrated sequence using LangGraph.
    """
    try:
        from agents.langgraph_workflow import SupplyChainWorkflow
        import asyncio

        logger.info(f"Workflow execution request: item_id={item_id}, depot_id={depot_id}")

        # Parse destinations if provided
        dest_list = destinations.split(",") if destinations else []

        # Initialize workflow
        workflow = SupplyChainWorkflow()

        initial_state = {
            "item_id": item_id,
            "depot_id": depot_id,
            "destinations": dest_list,
            "horizon_days": horizon_days,
            "policy": {"safe_days": 14}
        }

        # Run workflow with timeout
        async def run_workflow():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: workflow.run_workflow(initial_state))

        try:
            result = await asyncio.wait_for(run_workflow(), timeout=300.0)  # 5 minute timeout
        except asyncio.TimeoutError:
            logger.error("Workflow execution timeout")
            raise HTTPException(status_code=408, detail="Workflow execution timed out")

        return {
            "status": result.get("workflow_status", "unknown"),
            "results": {
                "forecast": result.get("demand_forecast"),
                "route": result.get("route_plan"),
                "transfers": result.get("transfer_plan"),
                "alerts": result.get("alerts")
            },
            "kpi_metrics": result.get("kpi_metrics", {}),
            "agent_logs": result.get("agent_logs", []),
            "execution_time": "completed"
        }

    except Exception as e:
        logger.error(f"Error in workflow execution endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("Starting Pharmaceutical Supply Chain Agentic AI...")

    # TODO: Initialize database connections
    # TODO: Initialize ML models
    # TODO: Start background tasks if needed

    logger.info("Application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Shutting down Pharmaceutical Supply Chain Agentic AI...")

    # TODO: Close database connections
    # TODO: Save model states if needed
    # TODO: Cleanup resources

    logger.info("Application shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=1020,
        reload=True,
        log_level="info"
    )
