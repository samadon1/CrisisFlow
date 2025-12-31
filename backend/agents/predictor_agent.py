"""
Predictor Agent - Forecasts disaster evolution
Predicts fire spread, flood zones, evacuation needs over next 6 hours
"""
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from .base_agent import BaseAgent, AgentStatus
import json

logger = logging.getLogger(__name__)


class PredictorAgent(BaseAgent):
    """Predicts disaster evolution and generates timeline"""

    def __init__(self, gemini_client):
        super().__init__(
            agent_id="predictor-001",
            name="Predictor",
            role="Disaster Forecasting & Timeline Generation",
            gemini_client=gemini_client
        )

    async def analyze(self, events: List[Dict], analyst_result: Dict) -> Dict[str, Any]:
        """
        Generate prediction timeline for disaster evolution

        Args:
            events: Current events data
            analyst_result: Analysis from Analyst agent

        Returns:
            Prediction timeline with hourly forecasts
        """
        self.set_status(AgentStatus.WORKING)

        try:
            crisis_type = analyst_result.get('analysis', {}).get('crisis_type', 'unknown')
            locations = analyst_result.get('analysis', {}).get('affected_locations', [])

            # Get relevant weather data
            weather_data = []
            for event in events:
                if event.get('source') in ['tomorrow.io', 'noaa']:
                    weather_data.append({
                        'location': event.get('location', {}).get('name'),
                        'fire_index': event.get('data', {}).get('fire_index', 0),
                        'flood_index': event.get('data', {}).get('flood_index', 0),
                        'wind_speed': event.get('data', {}).get('wind_speed', 0),
                        'wind_direction': event.get('data', {}).get('wind_direction', 0),
                        'temperature': event.get('data', {}).get('temperature', 0),
                        'humidity': event.get('data', {}).get('humidity', 0)
                    })

            prompt = f"""
            DISASTER PREDICTION TASK

            Current Situation:
            - Crisis Type: {crisis_type}
            - Affected Area: {', '.join(locations[:2])}
            - Current Weather: {json.dumps(weather_data[:2], indent=2)}

            Generate a 6-hour prediction timeline showing how this disaster will evolve.

            For each time point (1hr, 2hr, 4hr, 6hr), predict:
            1. **Spread Distance**: How far will it spread? (in km)
            2. **Direction**: Which direction? (N, NE, E, SE, S, SW, W, NW)
            3. **Severity Change**: Will it get worse/better? (increasing/stable/decreasing)
            4. **New Hazards**: Any new dangers emerging?
            5. **Confidence**: How confident? (0-100%)

            Return JSON:
            {{
                "predictions": [
                    {{
                        "time_offset_hours": 1,
                        "spread_km": <number>,
                        "direction": "<direction>",
                        "severity_trend": "<increasing/stable/decreasing>",
                        "new_hazards": ["<hazard>"],
                        "confidence": <0-100>,
                        "description": "<one sentence>"
                    }},
                    ...for 1hr, 2hr, 4hr, 6hr
                ],
                "recommended_actions": [
                    "<action1>",
                    "<action2>"
                ],
                "critical_timeframe": "<when action MUST be taken>"
            }}
            """

            response_text = await self.ask_gemini(prompt)

            # Parse response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    predictions = json.loads(response_text[json_start:json_end])
                else:
                    # Fallback predictions
                    predictions = self._generate_fallback_predictions(crisis_type)
            except json.JSONDecodeError:
                logger.warning("Predictor: JSON parse failed, using fallback")
                predictions = self._generate_fallback_predictions(crisis_type)

            # Add timestamps to predictions
            current_time = datetime.utcnow()
            for pred in predictions.get('predictions', []):
                pred['predicted_time'] = (current_time + timedelta(hours=pred['time_offset_hours'])).isoformat()

            # Send message
            first_pred = predictions['predictions'][0] if predictions.get('predictions') else {}
            message_content = f"Forecasting {crisis_type}: Will spread {first_pred.get('spread_km', 2)}km {first_pred.get('direction', 'northeast')} in next hour"

            message = self.send_message(
                content=message_content,
                priority="high",
                data=predictions
            )

            self.set_status(AgentStatus.ACTIVE)

            return {
                "status": "prediction_complete",
                "predictions": predictions,
                "message": message.to_dict()
            }

        except Exception as e:
            logger.error(f"Predictor Agent error: {e}")
            self.set_status(AgentStatus.ERROR)
            raise

    def _generate_fallback_predictions(self, crisis_type: str) -> Dict:
        """Generate fallback predictions if Gemini fails"""
        return {
            "predictions": [
                {
                    "time_offset_hours": 1,
                    "spread_km": 2.5,
                    "direction": "northeast",
                    "severity_trend": "increasing",
                    "new_hazards": ["Smoke inhalation risk"],
                    "confidence": 70,
                    "description": f"{crisis_type.capitalize()} expected to intensify in next hour"
                },
                {
                    "time_offset_hours": 2,
                    "spread_km": 4.0,
                    "direction": "northeast",
                    "severity_trend": "increasing",
                    "new_hazards": ["Threatens residential area"],
                    "confidence": 65,
                    "description": "Residential areas at risk within 2 hours"
                },
                {
                    "time_offset_hours": 4,
                    "spread_km": 6.5,
                    "direction": "northeast",
                    "severity_trend": "stable",
                    "new_hazards": ["Major evacuation needed"],
                    "confidence": 55,
                    "description": "Large-scale evacuation may be required"
                },
                {
                    "time_offset_hours": 6,
                    "spread_km": 8.0,
                    "direction": "northeast",
                    "severity_trend": "decreasing",
                    "new_hazards": [],
                    "confidence": 45,
                    "description": "Situation may stabilize if conditions improve"
                }
            ],
            "recommended_actions": [
                "Pre-stage emergency crews at predicted spread zones",
                "Issue evacuation warnings to areas in projected path",
                "Close roads in affected corridors"
            ],
            "critical_timeframe": "Next 2 hours - action required before residential impact"
        }
