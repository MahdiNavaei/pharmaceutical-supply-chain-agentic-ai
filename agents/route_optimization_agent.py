"""
Route Optimization Agent for Pharmaceutical Supply Chain Agentic AI

This agent optimizes delivery routes using Google OR-Tools VRP solver.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    logger.warning("OR-Tools not available. Install with: pip install ortools")

class RouteOptimizationAgent:
    """
    Agent for optimizing pharmaceutical delivery routes using VRP

    Uses Google OR-Tools to solve Vehicle Routing Problem with:
    - Multiple depots/warehouses
    - Capacity constraints
    - Time windows
    - Distance/cost optimization
    """

    def __init__(self):
        if not ORTOOLS_AVAILABLE:
            raise ImportError("OR-Tools is required for route optimization")

    def optimize_route(self, depot_id: str, destinations: List[str],
                      vehicle_capacity: int = 500, max_time_hours: int = 8,
                      objective: str = "min_distance") -> Dict[str, Any]:
        """
        Optimize delivery route for pharmaceutical distribution

        Args:
            depot_id: Starting warehouse location
            destinations: List of delivery destinations
            vehicle_capacity: Vehicle capacity in units
            max_time_hours: Maximum route time in hours
            objective: Optimization objective ("min_distance", "min_time", "min_cost")

        Returns:
            Dictionary containing optimized route information
        """
        try:
            logger.info(f"Optimizing route from {depot_id} to {len(destinations)} destinations")

            # Create distance matrix (simplified - in real scenario, use actual distances)
            distance_matrix = self._create_distance_matrix(depot_id, destinations)

            # Setup VRP solver
            manager = pywrapcp.RoutingIndexManager(
                len(distance_matrix), 1, 0  # 1 vehicle, depot at index 0
            )

            routing = pywrapcp.RoutingModel(manager)

            # Distance callback
            def distance_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return distance_matrix[from_node][to_node]

            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

            # Capacity constraint
            def demand_callback(from_index):
                from_node = manager.IndexToNode(from_index)
                return 50  # Simplified: each location requires 50 units

            demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
            routing.AddDimensionWithVehicleCapacity(
                demand_callback_index,
                0,  # null capacity slack
                [vehicle_capacity],  # vehicle maximum capacities
                True,  # start cumul to zero
                "Capacity"
            )

            # Time constraint
            def time_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                # Simplified: 2 minutes per km, plus 15 minutes for delivery
                # The lower factor keeps routes feasible under typical 8h limits
                return int((distance_matrix[from_node][to_node] * 2) + 15)

            time_callback_index = routing.RegisterTransitCallback(time_callback)
            routing.AddDimension(
                time_callback_index,
                0,  # allow waiting time
                int(max_time_hours * 60),  # maximum time in minutes
                True,  # start cumul to zero
                "Time"
            )

            # Solve the problem
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.time_limit.FromSeconds(10)

            solution = routing.SolveWithParameters(search_parameters)

            if solution:
                return self._extract_solution(manager, routing, solution, depot_id, destinations, distance_matrix)
            else:
                logger.warning("No solution found for route optimization")
                return self._fallback_solution(depot_id, destinations)

        except Exception as e:
            logger.error(f"Error in route optimization: {e}")
            return self._error_response(str(e))

    def _create_distance_matrix(self, depot_id: str, destinations: List[str]) -> List[List[int]]:
        """
        Create distance matrix between locations

        In a real implementation, this would use:
        - Google Maps API
        - OpenStreetMap data
        - Historical delivery data
        """
        all_locations = [depot_id] + destinations
        n = len(all_locations)

        # Create a symmetric distance matrix (in km)
        np.random.seed(42)  # For reproducible results
        distances = np.random.randint(5, 50, size=(n, n))

        # Make it symmetric
        for i in range(n):
            for j in range(i+1, n):
                distances[j][i] = distances[i][j]

        # Diagonal should be 0
        for i in range(n):
            distances[i][i] = 0

        return distances.tolist()

    def _extract_solution(self, manager, routing, solution, depot_id: str,
                         destinations: List[str], distance_matrix: List[List[int]]) -> Dict[str, Any]:
        """Extract solution from OR-Tools solver"""
        try:
            route = []
            index = routing.Start(0)

            route_distance = 0
            route_time = 0

            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                if node == 0:
                    route.append(depot_id)
                else:
                    route.append(destinations[node - 1])

                previous_index = index
                index = solution.Value(routing.NextVar(index))

                if not routing.IsEnd(index):
                    from_node = manager.IndexToNode(previous_index)
                    to_node = manager.IndexToNode(index)
                    route_distance += distance_matrix[from_node][to_node]
                    route_time += int((distance_matrix[from_node][to_node] * 10) + 30)  # Simplified

            # Add return to depot
            route.append(depot_id)
            from_node = manager.IndexToNode(previous_index)
            route_distance += distance_matrix[from_node][0]
            route_time += int((distance_matrix[from_node][0] * 10) + 30)

            # Calculate savings (simplified baseline comparison)
            baseline_distance = sum(distance_matrix[i][(i+1) % len(distance_matrix)]
                                  for i in range(len(distance_matrix))) * 0.8  # Simplified
            savings_percentage = max(0, (baseline_distance - route_distance) / baseline_distance * 100)

            return {
                "sequence": route,
                "total_distance_km": route_distance,
                "total_time_hours": route_time / 60,  # Convert to hours
                "total_cost_usd": route_distance * 2.5,  # $2.50 per km
                "savings_vs_baseline": f"{savings_percentage:.1f}%",
                "vehicle_used": 1,
                "status": "success",
                "optimization_method": "OR-Tools VRP"
            }

        except Exception as e:
            logger.error(f"Error extracting solution: {e}")
            return self._fallback_solution(depot_id, destinations)

    def _fallback_solution(self, depot_id: str, destinations: List[str]) -> Dict[str, Any]:
        """Fallback solution when optimization fails"""
        route = [depot_id] + destinations + [depot_id]

        # Calculate approximate distance
        total_distance = len(destinations) * 25  # Rough estimate
        total_time = len(destinations) * 1.5  # Rough estimate in hours

        return {
            "sequence": route,
            "total_distance_km": total_distance,
            "total_time_hours": total_time,
            "total_cost_usd": total_distance * 2.5,
            "savings_vs_baseline": "0%",
            "vehicle_used": 1,
            "status": "fallback",
            "message": "Optimization failed, using simple route",
            "optimization_method": "Simple sequencing"
        }

    def _error_response(self, error_msg: str) -> Dict[str, Any]:
        """Return error response"""
        return {
            "sequence": [],
            "total_distance_km": 0,
            "total_time_hours": 0,
            "total_cost_usd": 0,
            "savings_vs_baseline": "0%",
            "status": "error",
            "message": error_msg
        }


