"""
Coordinator Agent - Makes strategic decisions about resource allocation
"""
import logging
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentStatus
import json

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """Coordinates response decisions based on all agent inputs"""

    def __init__(self, gemini_client):
        super().__init__(
            agent_id="coordinator-001",
            name="Coordinator",
            role="Response Coordination & Decision Making",
            gemini_client=gemini_client
        )

    async def analyze(self, scout_result: Dict, analyst_result: Dict, predictor_result: Dict) -> Dict[str, Any]:
        """
        Make coordinated decisions based on all agent inputs

        Args:
            scout_result: Scout agent findings
            analyst_result: Analyst assessment
            predictor_result: Predictor forecast

        Returns:
            Coordinated response recommendations
        """
        self.set_status(AgentStatus.WORKING)

        try:
            severity = scout_result.get('analysis', {}).get('severity', 0)
            crisis_type = analyst_result.get('analysis', {}).get('crisis_type', 'unknown')
            predictions = predictor_result.get('predictions', {})

            prompt = f"""
            EMERGENCY RESPONSE COORDINATION

            Situation Summary:
            - Severity: {severity}/100
            - Crisis Type: {crisis_type}
            - Scout says: {scout_result.get('analysis', {}).get('summary', 'Monitoring')}
            - Analyst says: {analyst_result.get('analysis', {}).get('analysis_summary', 'Under review')}
            - Predictor says: {predictor_result.get('message', {}).get('content', 'Forecasting')}

            Predictions: {json.dumps(predictions.get('predictions', [])[:2], indent=2)}

            As Emergency Coordinator, decide:

            1. **Response Level**: What level of response? (advisory/watch/warning/evacuation)
            2. **Immediate Actions**: Top 3 actions to take NOW
            3. **Resource Needs**: What resources to deploy?
            4. **Evacuation Decision**: Should we evacuate? Which zones?
            5. **Alert Priority**: Should we send public alert? (yes/no)

            Return JSON:
            {{
                "response_level": "<advisory/watch/warning/evacuation>",
                "immediate_actions": ["<action1>", "<action2>", "<action3>"],
                "resources_needed": ["<resource1>", "<resource2>"],
                "evacuation_zones": ["<zone>" or null],
                "send_alert": <true/false>,
                "alert_priority": "<critical/high/medium/low>",
                "coordination_summary": "<2-3 sentence decision rationale>"
            }}
            """

            response_text = await self.ask_gemini(prompt)

            # Parse response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    decision = json.loads(response_text[json_start:json_end])
                else:
                    # Fallback decision
                    decision = self._generate_fallback_decision(severity, crisis_type)
            except json.JSONDecodeError:
                logger.warning("Coordinator: JSON parse failed, using fallback")
                decision = self._generate_fallback_decision(severity, crisis_type)

            # Send message
            message_content = f"Recommend {decision['response_level'].upper()} level response"
            if decision.get('send_alert'):
                message_content += f" with {decision['alert_priority']} priority alert"

            message = self.send_message(
                content=message_content,
                priority=decision.get('alert_priority', 'medium'),
                data=decision
            )

            self.set_status(AgentStatus.READY)

            return {
                "status": "decision_made",
                "decision": decision,
                "message": message.to_dict()
            }

        except Exception as e:
            logger.error(f"Coordinator Agent error: {e}")
            self.set_status(AgentStatus.ERROR)
            raise

    def _generate_fallback_decision(self, severity: int, crisis_type: str) -> Dict:
        """Generate fallback decision"""
        if severity >= 80:
            response_level = "evacuation"
            alert = True
            priority = "critical"
        elif severity >= 60:
            response_level = "warning"
            alert = True
            priority = "high"
        elif severity >= 40:
            response_level = "watch"
            alert = True
            priority = "medium"
        else:
            response_level = "advisory"
            alert = False
            priority = "low"

        return {
            "response_level": response_level,
            "immediate_actions": [
                "Deploy emergency response teams",
                "Notify local authorities",
                "Monitor situation closely"
            ],
            "resources_needed": ["Fire crews", "EMS units", "Communication systems"],
            "evacuation_zones": ["Zone 7", "Zone 8"] if severity >= 80 else None,
            "send_alert": alert,
            "alert_priority": priority,
            "coordination_summary": f"Based on {severity}/100 severity for {crisis_type}, recommending {response_level} level response."
        }
