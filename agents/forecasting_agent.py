"""
Forecasting Agent for Pharmaceutical Supply Chain Agentic AI

This agent predicts future demand for pharmaceutical products using
machine learning models like Prophet and LSTM.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not available. Install with: pip install prophet")

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from sklearn.preprocessing import MinMaxScaler
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available. Install with: pip install tensorflow")

from utils.database import get_sales_data, get_inventory_data

class ForecastingAgent:
    """
    Agent for forecasting pharmaceutical demand using ML models

    Supports multiple forecasting models:
    - Prophet (Facebook's forecasting library)
    - LSTM (Deep Learning approach)
    - Simple moving average (baseline)
    """

    def __init__(self):
        self.models = {
            'prophet': self._forecast_prophet,
            'lstm': self._forecast_lstm,
            'moving_average': self._forecast_moving_average
        }

    def forecast(self, drug_id: str, branch_id: Optional[str] = None,
                horizon_days: int = 30, model: str = 'prophet',
                sales_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Forecast demand for a pharmaceutical product

        Args:
            drug_id: ID of the drug to forecast
            branch_id: Optional branch ID for location-specific forecast
            horizon_days: Number of days to forecast
            model: Forecasting model to use ('prophet', 'lstm', 'moving_average')

        Returns:
            Dictionary containing forecast results, metrics, and confidence intervals
        """
        try:
            logger.info(f"Starting forecast for drug {drug_id}, model: {model}, horizon: {horizon_days} days")

            # Get historical sales data
            if sales_data is None:
                sales_data = get_sales_data(drug_id, branch_id, days=365)

            if not sales_data:
                logger.warning(f"No sales data found for drug {drug_id}")
                return self._empty_forecast_response(horizon_days)

            # Convert to DataFrame
            df = self._prepare_data(sales_data)

            if df.empty or len(df) < 7:  # Need at least a week of data
                logger.warning(f"Insufficient data for drug {drug_id}: {len(df)} records")
                return self._empty_forecast_response(horizon_days)

            # Select and run forecasting model
            if model not in self.models:
                logger.warning(f"Unknown model {model}, using prophet")
                model = 'prophet'

            forecast_result = self.models[model](df, horizon_days)

            logger.info(f"Forecast completed for drug {drug_id}")
            return forecast_result

        except Exception as e:
            logger.error(f"Error in forecasting for drug {drug_id}: {e}")
            return self._error_response(str(e), horizon_days)

    def _prepare_data(self, sales_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare sales data for forecasting"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(sales_data)

            # Ensure date column is datetime
            df['date'] = pd.to_datetime(df['date'])

            # Group by date and sum quantities (in case of multiple entries per day)
            df_daily = df.groupby('date')['quantity'].sum().reset_index()

            # Sort by date
            df_daily = df_daily.sort_values('date')

            # Rename columns for Prophet compatibility
            df_daily = df_daily.rename(columns={'date': 'ds', 'quantity': 'y'})

            # Ensure no missing dates (fill with 0)
            date_range = pd.date_range(start=df_daily['ds'].min(),
                                      end=df_daily['ds'].max(),
                                      freq='D')
            df_daily = df_daily.set_index('ds').reindex(date_range, fill_value=0).reset_index()
            df_daily = df_daily.rename(columns={'index': 'ds'})

            return df_daily

        except Exception as e:
            logger.error(f"Error preparing data: {e}")
            return pd.DataFrame()

    def _forecast_prophet(self, df: pd.DataFrame, horizon_days: int) -> Dict[str, Any]:
        """Forecast using Facebook Prophet"""
        if not PROPHET_AVAILABLE:
            logger.error("Prophet not available")
            return self._error_response("Prophet not installed", horizon_days)

        try:
            # Initialize Prophet model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                seasonality_mode='additive',
                changepoint_prior_scale=0.05,
                interval_width=0.95
            )

            # Fit model
            model.fit(df)

            # Create future dates
            future = model.make_future_dataframe(periods=horizon_days, freq='D')

            # Forecast
            forecast = model.predict(future)

            # Extract forecast for future period only
            last_date = df['ds'].max()
            future_forecast = forecast[forecast['ds'] > last_date].copy()

            # Prepare response
            forecast_data = []
            for _, row in future_forecast.iterrows():
                forecast_data.append({
                    'date': row['ds'].strftime('%Y-%m-%d'),
                    'yhat': float(row['yhat']),
                    'yhat_lower': float(row['yhat_lower']),
                    'yhat_upper': float(row['yhat_upper'])
                })

            # Calculate metrics using historical data
            metrics = self._calculate_metrics(df, forecast[forecast['ds'] <= last_date])

            return {
                'forecast': forecast_data,
                'metrics': metrics,
                'confidence_interval': {
                    'lower': float(future_forecast['yhat_lower'].mean()),
                    'upper': float(future_forecast['yhat_upper'].mean())
                },
                'model': 'prophet',
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Error in Prophet forecasting: {e}")
            return self._error_response(f"Prophet error: {str(e)}", horizon_days)

    def _forecast_lstm(self, df: pd.DataFrame, horizon_days: int) -> Dict[str, Any]:
        """Forecast using LSTM neural network"""
        if not TENSORFLOW_AVAILABLE:
            logger.error("TensorFlow not available")
            return self._error_response("TensorFlow not installed", horizon_days)

        try:
            # Prepare data for LSTM
            data = df['y'].values.reshape(-1, 1)

            # Normalize data
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(data)

            # Create sequences
            sequence_length = min(30, len(scaled_data) - 1)  # Use up to 30 days of history
            X, y = [], []

            for i in range(sequence_length, len(scaled_data)):
                X.append(scaled_data[i-sequence_length:i, 0])
                y.append(scaled_data[i, 0])

            X, y = np.array(X), np.array(y)
            X = np.reshape(X, (X.shape[0], X.shape[1], 1))

            if len(X) < 5:  # Need minimum training data
                return self._forecast_moving_average(df, horizon_days)

            # Build LSTM model
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(1)
            ])

            model.compile(optimizer='adam', loss='mean_squared_error')

            # Train model (quick training for demo)
            model.fit(X, y, epochs=10, batch_size=16, verbose=0)

            # In-sample reconstruction for basic metrics
            train_pred_scaled = model.predict(X, verbose=0).flatten()
            train_pred = scaler.inverse_transform(train_pred_scaled.reshape(-1, 1)).flatten()
            train_actual = scaler.inverse_transform(y.reshape(-1, 1)).flatten()
            lstm_metrics = self._compute_basic_metrics(train_actual, train_pred)

            # Forecast future values
            forecast_data = []
            last_sequence = scaled_data[-sequence_length:].flatten()

            for i in range(horizon_days):
                # Prepare input
                input_seq = last_sequence[-sequence_length:].reshape(1, sequence_length, 1)

                # Predict next value
                predicted_scaled = model.predict(input_seq, verbose=0)[0][0]

                # Inverse transform
                predicted_value = scaler.inverse_transform([[predicted_scaled]])[0][0]

                # Ensure non-negative
                predicted_value = max(0, predicted_value)

                # Add to forecast
                forecast_date = df['ds'].max() + timedelta(days=i+1)
                forecast_data.append({
                    'date': forecast_date.strftime('%Y-%m-%d'),
                    'yhat': float(predicted_value),
                    'yhat_lower': float(predicted_value * 0.8),  # Simple confidence interval
                    'yhat_upper': float(predicted_value * 1.2)
                })

                # Update sequence for next prediction
                last_sequence = np.append(last_sequence, predicted_scaled)

            return {
                'forecast': forecast_data,
                'metrics': lstm_metrics,
                'confidence_interval': {
                    'lower': float(np.mean([f['yhat_lower'] for f in forecast_data])),
                    'upper': float(np.mean([f['yhat_upper'] for f in forecast_data]))
                },
                'model': 'lstm',
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Error in LSTM forecasting: {e}")
            return self._error_response(f"LSTM error: {str(e)}", horizon_days)

    def _forecast_moving_average(self, df: pd.DataFrame, horizon_days: int) -> Dict[str, Any]:
        """Simple moving average forecast (baseline)"""
        try:
            # Calculate moving average (last 7 days)
            window = min(7, len(df))
            avg_value = df['y'].tail(window).mean()

            # Use recent window as a hold-out to compute metrics
            recent_actual = df['y'].tail(window).values
            recent_pred = np.full_like(recent_actual, avg_value, dtype=float)
            metrics = self._compute_basic_metrics(recent_actual, recent_pred)

            forecast_data = []
            for i in range(horizon_days):
                forecast_date = df['ds'].max() + timedelta(days=i+1)
                forecast_data.append({
                    'date': forecast_date.strftime('%Y-%m-%d'),
                    'yhat': float(avg_value),
                    'yhat_lower': float(avg_value * 0.7),
                    'yhat_upper': float(avg_value * 1.3)
                })

            return {
                'forecast': forecast_data,
                'metrics': metrics,
                'confidence_interval': {
                    'lower': float(avg_value * 0.7),
                    'upper': float(avg_value * 1.3)
                },
                'model': 'moving_average',
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Error in moving average forecasting: {e}")
            return self._error_response(f"Moving average error: {str(e)}", horizon_days)

    def _calculate_metrics(self, actual_df: pd.DataFrame, forecast_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate forecasting metrics"""
        try:
            # Merge actual and forecast data
            merged = pd.merge(actual_df, forecast_df[['ds', 'yhat']],
                            on='ds', how='inner')

            if len(merged) < 2:
                return {'mape': None, 'rmse': None, 'mae': None}

            actual = merged['y'].values
            predicted = merged['yhat'].values

            # Calculate metrics
            mae = mean_absolute_error(actual, predicted)
            rmse = np.sqrt(mean_squared_error(actual, predicted))

            # MAPE (avoid division by zero)
            non_zero_mask = actual != 0
            if np.any(non_zero_mask):
                mape = np.mean(np.abs((actual[non_zero_mask] - predicted[non_zero_mask]) / actual[non_zero_mask])) * 100
            else:
                mape = None

            return {
                'mape': float(mape) if mape is not None else None,
                'rmse': float(rmse),
                'mae': float(mae)
            }

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {'mape': None, 'rmse': None, 'mae': None}

    def _empty_forecast_response(self, horizon_days: int) -> Dict[str, Any]:
        """Return empty forecast response when no data is available"""
        return {
            'forecast': [],
            'metrics': {'mape': None, 'rmse': None, 'mae': None},
            'confidence_interval': {'lower': 0, 'upper': 0},
            'model': 'none',
            'status': 'no_data',
            'message': 'No historical data available for forecasting'
        }

    def _error_response(self, error_msg: str, horizon_days: int) -> Dict[str, Any]:
        """Return error response"""
        return {
            'forecast': [],
            'metrics': {'mape': None, 'rmse': None, 'mae': None},
            'confidence_interval': {'lower': 0, 'upper': 0},
            'model': 'error',
            'status': 'error',
            'message': error_msg
        }

    def _compute_basic_metrics(self, actual: np.ndarray, predicted: np.ndarray) -> Dict[str, Optional[float]]:
        """Compute MAE, RMSE, MAPE for given arrays"""
        try:
            if len(actual) == 0:
                return {'mape': None, 'rmse': None, 'mae': None}

            mae = mean_absolute_error(actual, predicted)
            rmse = np.sqrt(mean_squared_error(actual, predicted))

            non_zero_mask = actual != 0
            if np.any(non_zero_mask):
                mape = np.mean(np.abs((actual[non_zero_mask] - predicted[non_zero_mask]) / actual[non_zero_mask])) * 100
            else:
                mape = None

            return {
                'mape': float(mape) if mape is not None else None,
                'rmse': float(rmse),
                'mae': float(mae)
            }
        except Exception as e:
            logger.error(f"Error computing basic metrics: {e}")
            return {'mape': None, 'rmse': None, 'mae': None}
