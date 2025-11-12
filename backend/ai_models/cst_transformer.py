"""
CST-Transformer: Cross-Stream Transformer for Spatio-Temporal Hotspot Forecasting
Advanced AI model for predicting cybercrime hotspots using multi-modal data streams
"""

import asyncio
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import logging
import json
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import text
from data_sources.ncrp_integration import ncrp_integration
from data_sources.bank_integration import bank_integration
from data_sources.i4c_integration import i4c_integration

logger = logging.getLogger(__name__)

class SpatioTemporalDataset(Dataset):
    """
    Dataset for spatio-temporal hotspot prediction
    """

    def __init__(self, features: np.ndarray, targets: np.ndarray, sequence_length: int = 24):
        self.features = features
        self.targets = targets
        self.sequence_length = sequence_length

    def __len__(self):
        return len(self.features) - self.sequence_length

    def __getitem__(self, idx):
        return (
            torch.FloatTensor(self.features[idx:idx + self.sequence_length]),
            torch.FloatTensor(self.targets[idx + self.sequence_length])
        )

class MultiHeadAttention(nn.Module):
    """
    Multi-head attention mechanism for transformer
    """

    def __init__(self, d_model: int, num_heads: int):
        super().__init__()
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads

        assert self.head_dim * num_heads == d_model, "d_model must be divisible by num_heads"

        self.query = nn.Linear(d_model, d_model)
        self.key = nn.Linear(d_model, d_model)
        self.value = nn.Linear(d_model, d_model)
        self.out = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(0.1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, d_model = x.size()

        # Split into multiple heads
        Q = self.query(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        K = self.key(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        V = self.value(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(self.head_dim)
        attention = torch.softmax(scores, dim=-1)
        attention = self.dropout(attention)

        out = torch.matmul(attention, V)
        out = out.transpose(1, 2).contiguous().view(batch_size, seq_len, d_model)
        return self.out(out)

class TransformerBlock(nn.Module):
    """
    Transformer block with multi-head attention and feed-forward
    """

    def __init__(self, d_model: int, num_heads: int, ff_dim: int):
        super().__init__()
        self.attention = MultiHeadAttention(d_model, num_heads)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

        self.ff = nn.Sequential(
            nn.Linear(d_model, ff_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(ff_dim, d_model),
            nn.Dropout(0.1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Self-attention with residual connection
        attn_out = self.attention(x)
        x = self.norm1(x + attn_out)

        # Feed-forward with residual connection
        ff_out = self.ff(x)
        x = self.norm2(x + ff_out)

        return x

class CSTTransformer(nn.Module):
    """
    Cross-Stream Transformer for Spatio-Temporal Hotspot Forecasting
    """

    def __init__(self, input_dim: int = 12, d_model: int = 256, num_heads: int = 8,
                 num_layers: int = 6, ff_dim: int = 512, max_seq_len: int = 24):
        super().__init__()
        self.d_model = d_model
        self.max_seq_len = max_seq_len

        # Input embedding
        self.input_embedding = nn.Linear(input_dim, d_model)
        self.positional_encoding = self._create_positional_encoding(max_seq_len, d_model)

        # Transformer layers
        self.transformer_blocks = nn.ModuleList([
            TransformerBlock(d_model, num_heads, ff_dim) for _ in range(num_layers)
        ])

        # Output heads
        self.hotspot_head = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),  # Hotspot probability
            nn.Sigmoid()
        )

        self.location_head = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 2)  # Latitude, Longitude
        )

        self.confidence_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Linear(64, 1),  # Confidence score
            nn.Sigmoid()
        )

        self.time_window_head = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Linear(32, 1)  # Time window in minutes
        )

    def _create_positional_encoding(self, max_len: int, d_model: int) -> torch.Tensor:
        """Create positional encoding for transformer"""
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)

        div_term = torch.exp(torch.arange(0, d_model, 2).float() *
                           (-np.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        return pe.unsqueeze(0)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        batch_size, seq_len, _ = x.size()

        # Input embedding
        x = self.input_embedding(x) * np.sqrt(self.d_model)

        # Add positional encoding
        pe = self.positional_encoding[:, :seq_len, :].to(x.device)
        x = x + pe

        # Pass through transformer blocks
        for block in self.transformer_blocks:
            x = block(x)

        # Use the last token for predictions
        last_token = x[:, -1, :]

        # Generate predictions
        hotspot_prob = self.hotspot_head(last_token)
        location = self.location_head(last_token)
        confidence = self.confidence_head(last_token)
        time_window = self.time_window_head(last_token)

        return {
            'hotspot_probability': hotspot_prob,
            'location': location,
            'confidence': confidence,
            'time_window_minutes': time_window
        }

class CSTTransformerService:
    """
    Service for training and using CST-Transformer model
    """

    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = CSTTransformer().to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.0001)
        self.criterion = nn.MSELoss()
        self.is_trained = False

        # Feature dimensions
        self.feature_columns = [
            'complaint_count', 'avg_amount', 'suspicious_transactions',
            'risk_score', 'hour_of_day', 'day_of_week',
            'lat_norm', 'lon_norm', 'scam_type_encoded',
            'severity_score', 'repeat_offender_rate', 'historical_density'
        ]

    async def prepare_training_data(self, days_back: int = 30) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data from multiple data sources
        """
        try:
            # Get data from all sources
            ncrp_data = await ncrp_integration.get_complaints_batch(limit=1000, offset=0)
            suspicious_txns = await bank_integration.get_suspicious_transactions(hours_back=days_back * 24)
            i4c_data = await i4c_integration.get_training_data_for_ml(months_back=1)

            # Process and combine data
            features = []
            targets = []

            # Create time-based features
            for hour_offset in range(days_back * 24):
                timestamp = datetime.utcnow() - timedelta(hours=hour_offset)

                # Extract features for this time window
                feature_vector = await self._extract_features(
                    timestamp, ncrp_data, suspicious_txns, i4c_data
                )

                if feature_vector:
                    features.append(feature_vector)

                    # Target: whether a hotspot occurred in the next hour
                    target = await self._get_target_for_timestamp(
                        timestamp + timedelta(hours=1), ncrp_data, suspicious_txns
                    )
                    targets.append(target)

            return np.array(features), np.array(targets)

        except Exception as e:
            logger.error(f"[CST-Transformer] Error preparing training data: {str(e)}")
            return np.array([]), np.array([])

    async def _extract_features(self, timestamp: datetime, ncrp_data: List,
                               suspicious_txns: List, i4c_data: List) -> Optional[List[float]]:
        """
        Extract feature vector for a given timestamp
        """
        try:
            features = []

            # Temporal features
            features.append(timestamp.hour)  # hour_of_day
            features.append(timestamp.weekday())  # day_of_week

            # Complaint-based features
            recent_complaints = [c for c in ncrp_data if
                               datetime.fromisoformat(c['complaint_timestamp']) > timestamp - timedelta(hours=1)]
            features.append(len(recent_complaints))  # complaint_count

            if recent_complaints:
                avg_amount = np.mean([c['amount'] for c in recent_complaints])
                features.append(avg_amount)  # avg_amount

                # Average location
                avg_lat = np.mean([c['victim_location']['lat'] for c in recent_complaints])
                avg_lon = np.mean([c['victim_location']['lon'] for c in recent_complaints])
                features.append(avg_lat)  # lat_norm
                features.append(avg_lon)  # lon_norm
            else:
                features.extend([0, 28.6139, 77.2090])  # Default to Delhi

            # Transaction-based features
            recent_txns = [t for t in suspicious_txns if
                          datetime.fromisoformat(t['timestamp']) > timestamp - timedelta(hours=1)]
            features.append(len(recent_txns))  # suspicious_transactions

            if recent_txns:
                avg_risk_score = np.mean([t['risk_score'] for t in recent_txns])
                features.append(avg_risk_score)  # risk_score
            else:
                features.append(0)

            # Historical patterns from I4C
            if i4c_data:
                # Use historical data for patterns
                features.append(5.5)  # avg_severity_score (mock)
                features.append(0.25)  # repeat_offender_rate (mock)
                features.append(0.1)  # historical_density (mock)
            else:
                features.extend([0, 0, 0])

            # Scam type encoding (one-hot would be better, simplified for demo)
            features.append(1)  # scam_type_encoded (mock)

            return features

        except Exception as e:
            logger.error(f"[CST-Transformer] Error extracting features: {str(e)}")
            return None

    async def _get_target_for_timestamp(self, timestamp: datetime, ncrp_data: List,
                                      suspicious_txns: List) -> float:
        """
        Get target value (hotspot occurrence) for timestamp
        """
        try:
            # Count events in the next hour
            future_complaints = [c for c in ncrp_data if
                               datetime.fromisoformat(c['complaint_timestamp']) > timestamp and
                               datetime.fromisoformat(c['complaint_timestamp']) <= timestamp + timedelta(hours=1)]

            future_txns = [t for t in suspicious_txns if
                          datetime.fromisoformat(t['timestamp']) > timestamp and
                          datetime.fromisoformat(t['timestamp']) <= timestamp + timedelta(hours=1)]

            # Hotspot if high activity (threshold based on historical patterns)
            total_activity = len(future_complaints) + len(future_txns)
            return 1.0 if total_activity >= 5 else 0.0

        except Exception as e:
            logger.error(f"[CST-Transformer] Error getting target: {str(e)}")
            return 0.0

    async def train_model(self, epochs: int = 10, batch_size: int = 32) -> Dict[str, Any]:
        """
        Train the CST-Transformer model
        """
        try:
            logger.info("[CST-Transformer] Starting model training...")

            # Prepare training data
            features, targets = await self.prepare_training_data(days_back=7)

            if len(features) == 0:
                raise ValueError("No training data available")

            # Normalize features
            features = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-8)

            # Create dataset and dataloader
            dataset = SpatioTemporalDataset(features, targets)
            dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

            # Training loop
            self.model.train()
            total_loss = 0

            for epoch in range(epochs):
                epoch_loss = 0
                num_batches = 0

                for batch_features, batch_targets in dataloader:
                    batch_features = batch_features.to(self.device)
                    batch_targets = batch_targets.to(self.device)

                    # Forward pass
                    predictions = self.model(batch_features)
                    loss = self.criterion(predictions['hotspot_probability'].squeeze(), batch_targets)

                    # Backward pass
                    self.optimizer.zero_grad()
                    loss.backward()
                    self.optimizer.step()

                    epoch_loss += loss.item()
                    num_batches += 1

                avg_epoch_loss = epoch_loss / num_batches if num_batches > 0 else 0
                total_loss += avg_epoch_loss

                logger.info(f"[CST-Transformer] Epoch {epoch + 1}/{epochs}, Loss: {avg_epoch_loss:.4f}")

            self.is_trained = True
            avg_loss = total_loss / epochs

            logger.info(f"[CST-Transformer] Training completed. Average loss: {avg_loss:.4f}")

            return {
                'success': True,
                'epochs_trained': epochs,
                'final_loss': avg_loss,
                'training_samples': len(features),
                'model_status': 'trained'
            }

        except Exception as e:
            logger.error(f"[CST-Transformer] Training failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'model_status': 'training_failed'
            }

    async def predict_hotspots(self, hours_ahead: int = 2) -> List[Dict[str, Any]]:
        """
        Predict future hotspots using the trained model
        """
        if not self.is_trained:
            logger.warning("[CST-Transformer] Model not trained, using mock predictions")
            return await self._generate_mock_predictions(hours_ahead)

        try:
            self.model.eval()
            predictions = []

            # Get recent data for prediction
            current_features = await self._get_current_features()

            if len(current_features) == 0:
                return await self._generate_mock_predictions(hours_ahead)

            # Normalize features
            current_features = (current_features - current_features.mean(axis=0)) / (current_features.std(axis=0) + 1e-8)

            # Create input sequence
            if len(current_features) < 24:
                # Pad if needed
                padding = np.zeros((24 - len(current_features), current_features.shape[1]))
                current_features = np.vstack([padding, current_features])

            input_tensor = torch.FloatTensor(current_features[-24:]).unsqueeze(0).to(self.device)

            with torch.no_grad():
                for hour in range(hours_ahead):
                    # Get prediction
                    prediction = self.model(input_tensor)

                    # Extract hotspot locations (top predictions)
                    hotspot_prob = prediction['hotspot_probability'].item()

                    if hotspot_prob > 0.7:  # High confidence threshold
                        location = prediction['location'].squeeze().cpu().numpy()
                        confidence = prediction['confidence'].item()
                        time_window = prediction['time_window_minutes'].item()

                        predictions.append({
                            'location': {
                                'lat': float(location[0]),
                                'lon': float(location[1])
                            },
                            'hotspot_probability': hotspot_prob,
                            'confidence': confidence,
                            'time_window_minutes': max(15, int(time_window)),  # Min 15 minutes
                            'prediction_time': (datetime.utcnow() + timedelta(hours=hour + 1)).isoformat(),
                            'model_type': 'CST-Transformer',
                            'data_sources': ['NCRP', 'CFCFRMS', 'I4C']
                        })

                    # Update input for next prediction (simplified)
                    # In practice, would incorporate the prediction as new input

            return predictions

        except Exception as e:
            logger.error(f"[CST-Transformer] Prediction failed: {str(e)}")
            return await self._generate_mock_predictions(hours_ahead)

    async def _get_current_features(self) -> np.ndarray:
        """
        Get current feature vector for prediction
        """
        # Similar to prepare_training_data but for recent time window
        try:
            ncrp_data = await ncrp_integration.get_complaints_batch(limit=100, offset=0)
            suspicious_txns = await bank_integration.get_suspicious_transactions(hours_back=24)

            features = []
            for hour_offset in range(24):
                timestamp = datetime.utcnow() - timedelta(hours=hour_offset)
                feature_vector = await self._extract_features(timestamp, ncrp_data, suspicious_txns, [])
                if feature_vector:
                    features.append(feature_vector)

            return np.array(features) if features else np.array([])

        except Exception as e:
            logger.error(f"[CST-Transformer] Error getting current features: {str(e)}")
            return np.array([])

    async def _generate_mock_predictions(self, hours_ahead: int) -> List[Dict[str, Any]]:
        """
        Generate mock predictions when model is not available
        """
        mock_predictions = []

        # High-risk locations for demo
        high_risk_locations = [
            {'lat': 28.6139, 'lon': 77.2090, 'name': 'Delhi'},
            {'lat': 19.0760, 'lon': 72.8777, 'name': 'Mumbai'},
            {'lat': 12.9716, 'lon': 77.5946, 'name': 'Bangalore'},
            {'lat': 13.0827, 'lon': 80.2707, 'name': 'Chennai'},
            {'lat': 22.5726, 'lon': 88.3639, 'name': 'Kolkata'}
        ]

        for hour in range(hours_ahead):
            # Randomly select 1-3 locations
            num_predictions = random.randint(1, 3)
            selected_locations = random.sample(high_risk_locations, num_predictions)

            for location in selected_locations:
                mock_predictions.append({
                    'location': {
                        'lat': location['lat'] + random.uniform(-0.05, 0.05),
                        'lon': location['lon'] + random.uniform(-0.05, 0.05)
                    },
                    'hotspot_probability': random.uniform(0.75, 0.95),
                    'confidence': random.uniform(0.80, 0.95),
                    'time_window_minutes': random.choice([30, 45, 60]),
                    'prediction_time': (datetime.utcnow() + timedelta(hours=hour + 1)).isoformat(),
                    'model_type': 'CST-Transformer-Mock',
                    'data_sources': ['NCRP', 'CFCFRMS', 'I4C'],
                    'region': location['name']
                })

        return mock_predictions

    async def save_model(self, filepath: str) -> bool:
        """
        Save trained model to disk
        """
        try:
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'is_trained': self.is_trained
            }, filepath)

            logger.info(f"[CST-Transformer] Model saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"[CST-Transformer] Error saving model: {str(e)}")
            return False

    async def load_model(self, filepath: str) -> bool:
        """
        Load trained model from disk
        """
        try:
            checkpoint = torch.load(filepath, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.is_trained = checkpoint['is_trained']

            logger.info(f"[CST-Transformer] Model loaded from {filepath}")
            return True

        except Exception as e:
            logger.error(f"[CST-Transformer] Error loading model: {str(e)}")
            return False

# Global service instance
cst_transformer_service = CSTTransformerService()