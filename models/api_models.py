"""
API models for Pharmaceutical Supply Chain Agentic AI

This module contains Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Forecasting Models
class ForecastRequest(BaseModel):
    entity_type: str = Field(..., description="Type of entity (branch, pharmacy, etc.)")
    entity_id: str = Field(..., description="ID of the entity")
    item_id: str = Field(..., description="ID of the item/drug to forecast")
    horizon_days: int = Field(30, ge=1, le=365, description="Number of days to forecast")
    model: str = Field("prophet", description="Forecasting model to use")

class ForecastData(BaseModel):
    date: str = Field(..., description="Forecast date in YYYY-MM-DD format")
    yhat: float = Field(..., description="Point forecast value")
    yhat_lower: Optional[float] = Field(None, description="Lower bound of confidence interval")
    yhat_upper: Optional[float] = Field(None, description="Upper bound of confidence interval")

class ForecastMetrics(BaseModel):
    mape: Optional[float] = Field(None, description="Mean Absolute Percentage Error")
    rmse: Optional[float] = Field(None, description="Root Mean Square Error")
    mae: Optional[float] = Field(None, description="Mean Absolute Error")

class ForecastResponse(BaseModel):
    forecast: List[ForecastData] = Field(..., description="List of forecast data points")
    metrics: ForecastMetrics = Field(..., description="Forecast accuracy metrics")
    confidence_interval: Dict[str, float] = Field(..., description="Overall confidence interval bounds")
    model: str = Field(..., description="Model used for forecasting")
    status: str = Field(..., description="Response status")
    message: Optional[str] = Field(None, description="Optional status message")

# Route Optimization Models
class RouteOptimizationRequest(BaseModel):
    depot_id: str = Field(..., description="ID of the depot/warehouse")
    destinations: List[str] = Field(..., description="List of destination IDs")
    vehicle_capacity: int = Field(500, gt=0, description="Vehicle capacity in units")
    max_time_hours: int = Field(8, gt=0, le=24, description="Maximum time allowed in hours")
    objective: str = Field("min_distance", description="Optimization objective")

class RouteStop(BaseModel):
    location_id: str = Field(..., description="Location identifier")
    sequence: int = Field(..., description="Visit sequence number")
    arrival_time: Optional[str] = Field(None, description="Estimated arrival time")
    departure_time: Optional[str] = Field(None, description="Estimated departure time")

class RouteOptimizationResponse(BaseModel):
    sequence: List[str] = Field(..., description="Optimized visit sequence")
    total_distance_km: float = Field(..., description="Total route distance in km")
    total_time_hours: float = Field(..., description="Total route time in hours")
    total_cost_usd: float = Field(..., description="Total route cost in USD")
    savings_vs_baseline: str = Field(..., description="Savings compared to baseline")
    stops: Optional[List[RouteStop]] = Field(None, description="Detailed stop information")
    status: str = Field(..., description="Response status")

# Inventory Matching Models
class InventoryPolicy(BaseModel):
    safe_days: int = Field(14, ge=1, description="Number of safe days stock")
    reorder_point: Optional[int] = Field(None, description="Reorder point threshold")
    max_stock: Optional[int] = Field(None, description="Maximum stock level")

class InventoryMatchingRequest(BaseModel):
    item_id: str = Field(..., description="ID of the item/drug")
    policy: InventoryPolicy = Field(..., description="Inventory policy parameters")

class TransferRecommendation(BaseModel):
    from_branch: str = Field(..., description="Source branch ID")
    to_branch: str = Field(..., description="Destination branch ID")
    item_id: str = Field(..., description="Item ID")
    quantity: int = Field(..., description="Recommended transfer quantity")
    transfer_cost: float = Field(..., description="Estimated transfer cost")
    expected_savings: float = Field(..., description="Expected cost savings")
    priority: str = Field(..., description="Transfer priority level")

class InventoryMatchingResponse(BaseModel):
    matches: List[TransferRecommendation] = Field(..., description="List of recommended transfers")
    total_matches: int = Field(..., description="Total number of recommendations")
    total_savings: float = Field(..., description="Total expected savings")
    total_cost: float = Field(..., description="Total transfer costs")
    status: str = Field(..., description="Response status")

# Monitoring/Alert Models
class AlertItem(BaseModel):
    severity: str = Field(..., description="Alert severity (CRITICAL, WARNING, INFO)")
    branch_id: str = Field(..., description="Branch ID where alert occurred")
    item_id: str = Field(..., description="Item ID causing the alert")
    alert_type: Optional[str] = Field(None, description="Type/category of the alert")
    message: str = Field(..., description="Human-readable alert description")
    current_stock: int = Field(..., description="Current stock level")
    days_until_stockout: float = Field(..., description="Days until stockout")
    recommended_action: str = Field(..., description="Recommended action")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Alert timestamp")
    is_resolved: bool = Field(False, description="Whether alert is resolved")

class AlertResponse(BaseModel):
    alerts: List[AlertItem] = Field(..., description="List of active alerts")
    total_alerts: int = Field(..., description="Total number of alerts")
    critical_count: int = Field(..., description="Number of critical alerts")
    warning_count: int = Field(..., description="Number of warning alerts")
    info_count: int = Field(..., description="Number of info alerts")
    ai_insights: Optional[str] = Field(None, description="AI-generated insights summarizing current alerts")
    status: str = Field(..., description="Response status")
    message: Optional[str] = Field(None, description="Optional status or error message")
    generated_at: Optional[datetime] = Field(None, description="Timestamp when alerts were generated")

# Dashboard Models
class KPIMetric(BaseModel):
    value: float = Field(..., description="Current KPI value")
    change: float = Field(..., description="Change from previous period")
    unit: str = Field(..., description="Unit of measurement")
    trend: str = Field(..., description="Trend direction (up, down, stable)")

class DashboardKPIs(BaseModel):
    forecast_accuracy: KPIMetric = Field(..., description="Forecast accuracy KPI")
    route_savings: KPIMetric = Field(..., description="Route optimization savings KPI")
    stockout_reduction: KPIMetric = Field(..., description="Stockout reduction KPI")
    response_time: KPIMetric = Field(..., description="API response time KPI")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

class AlertSummary(BaseModel):
    critical: int = Field(..., description="Number of critical alerts")
    warning: int = Field(..., description="Number of warning alerts")
    info: int = Field(..., description="Number of info alerts")
    total: int = Field(..., description="Total number of alerts")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

# Health Check Model
class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    version: str = Field(..., description="API version")
    service: str = Field(..., description="Service name")
    database: Optional[str] = Field(None, description="Database connection status")
    agents: Optional[Dict[str, str]] = Field(None, description="Agent status")

# Error Response Model
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier")


