"""
Communicator Agent - Generates public alerts and notifications
"""
import logging
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentStatus
import json

logger = logging.getLogger(__name__)


class CommunicatorAgent(BaseAgent):
    """Generates and drafts public communications and alerts"""

    def __init__(self, gemini_client):
        super().__init__(
            agent_id="communicator-001",
            name="Communicator",
            role="Public Alert Generation & Communications",
            gemini_client=gemini_client
        )

    async def analyze(self, coordinator_decision: Dict, analyst_result: Dict, predictor_result: Dict) -> Dict[str, Any]:
        """
        Generate alert message based on coordinator's decision

        Args:
            coordinator_decision: Coordinator's response decision
            analyst_result: Analyst's crisis assessment
            predictor_result: Predictor's timeline

        Returns:
            Draft alert ready to send
        """
        self.set_status(AgentStatus.WORKING)

        try:
            should_alert = coordinator_decision.get('decision', {}).get('send_alert', False)

            if not should_alert:
                self.set_status(AgentStatus.IDLE)
                return {
                    "status": "no_alert_needed",
                    "message": None
                }

            priority = coordinator_decision.get('decision', {}).get('alert_priority', 'medium')
            response_level = coordinator_decision.get('decision', {}).get('response_level', 'advisory')
            crisis_type = analyst_result.get('analysis', {}).get('crisis_type', 'emergency')
            locations = analyst_result.get('analysis', {}).get('affected_locations', ['affected area'])
            evacuation_zones = coordinator_decision.get('decision', {}).get('evacuation_zones', [])

            predictions = predictor_result.get('predictions', {}).get('predictions', [])
            next_hour = predictions[0] if predictions else {}

            prompt = f"""
            GENERATE PUBLIC EMERGENCY ALERT

            Situation:
            - Crisis: {crisis_type}
            - Response Level: {response_level}
            - Priority: {priority}
            - Location: {', '.join(locations[:2])}
            - Evacuation Zones: {evacuation_zones or 'None'}
            - Next Hour Forecast: {next_hour.get('description', 'Monitoring situation')}

            Create a clear, actionable public alert message:

            Requirements:
            1. Start with alert level ({response_level.upper()})
            2. State the hazard clearly
            3. Specify affected areas
            4. Give specific actions to take
            5. Keep it under 200 words
            6. Use clear, calm language
            7. Include timeframe if evacuation needed

            Return JSON:
            {{
                "alert_title": "<Alert Title>",
                "alert_message": "<Full alert text>",
                "actions_to_take": ["<action1>", "<action2>"],
                "affected_areas": ["<area1>"],
                "valid_until": "<time description>",
                "alert_level": "{response_level}"
            }}
            """

            response_text = await self.ask_gemini(prompt)

            # Parse response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    alert = json.loads(response_text[json_start:json_end])
                else:
                    # Fallback alert
                    alert = self._generate_fallback_alert(crisis_type, response_level, locations, evacuation_zones)
            except json.JSONDecodeError:
                logger.warning("Communicator: JSON parse failed, using fallback")
                alert = self._generate_fallback_alert(crisis_type, response_level, locations, evacuation_zones)

            # Send message
            message = self.send_message(
                content="Alert drafted and ready to send",
                priority=priority,
                data=alert
            )

            self.set_status(AgentStatus.READY)

            return {
                "status": "alert_ready",
                "alert": alert,
                "message": message.to_dict()
            }

        except Exception as e:
            logger.error(f"Communicator Agent error: {e}")
            self.set_status(AgentStatus.ERROR)
            raise

    def _generate_fallback_alert(self, crisis_type: str, response_level: str, locations: List[str], evacuation_zones: List[str] = None) -> Dict:
        """Generate fallback alert"""
        location_str = ', '.join(locations[:2]) if locations else 'affected areas'

        if response_level == 'evacuation':
            title = f"EVACUATION ORDER - {crisis_type.upper()}"
            message = f"IMMEDIATE EVACUATION REQUIRED for {location_str}. {crisis_type.capitalize()} poses imminent danger. Leave immediately and proceed to designated emergency shelters. Follow instructions from emergency personnel."
            actions = ["Evacuate immediately", "Take essential items only", "Follow evacuation routes", "Check on neighbors"]
        elif response_level == 'warning':
            title = f"{crisis_type.upper()} WARNING"
            message = f"Severe {crisis_type} warning issued for {location_str}. Conditions are dangerous. Seek shelter immediately and avoid affected areas. Stay tuned to emergency broadcasts for updates."
            actions = ["Seek shelter now", "Avoid affected areas", "Monitor emergency broadcasts", "Prepare to evacuate if ordered"]
        elif response_level == 'watch':
            title = f"{crisis_type.upper()} WATCH"
            message = f"{crisis_type.capitalize()} watch in effect for {location_str}. Conditions are developing that could become dangerous. Stay alert and be prepared to take action if situation worsens."
            actions = ["Stay alert", "Monitor weather/news", "Prepare emergency supplies", "Review evacuation routes"]
        else:
            title = f"{crisis_type.upper()} ADVISORY"
            message = f"{crisis_type.capitalize()} advisory for {location_str}. Be aware of changing conditions. Exercise caution in affected areas."
            actions = ["Stay informed", "Exercise caution", "Avoid unnecessary travel"]

        return {
            "alert_title": title,
            "alert_message": message,
            "actions_to_take": actions,
            "affected_areas": locations[:3],
            "valid_until": "Until further notice",
            "alert_level": response_level
        }
