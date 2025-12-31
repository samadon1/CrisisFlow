"""
Scout Agent - Monitors events and detects anomalies/patterns
First line of defense in crisis detection
"""
import logging
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentStatus
import json

logger = logging.getLogger(__name__)


class ScoutAgent(BaseAgent):
    """Continuously monitors incoming events and detects patterns"""

    def __init__(self, gemini_client):
        super().__init__(
            agent_id="scout-001",
            name="Scout",
            role="Event Monitoring & Pattern Detection",
            gemini_client=gemini_client
        )
        self.monitored_count = 0

    async def analyze(self, events: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Analyze incoming events for patterns and anomalies

        Args:
            events: Dictionary with 'weather' and 'social' event lists

        Returns:
            Detection results with severity and patterns found
        """
        self.set_status(AgentStatus.ACTIVE)
        self.monitored_count += 1

        try:
            weather_events = events.get('weather', [])
            social_events = events.get('social', [])

            total_events = len(weather_events) + len(social_events)

            # Quick severity check
            critical_events = []

            for event in weather_events:
                fire_index = event.get('data', {}).get('fire_index', 0)
                flood_index = event.get('data', {}).get('flood_index', 0)

                if fire_index > 60 or flood_index > 50:
                    critical_events.append(event)

            for event in social_events:
                urgency = event.get('data', {}).get('urgency', 'low')
                if urgency == 'critical':
                    critical_events.append(event)

            # If critical events found, do deep analysis with Gemini
            if critical_events:
                self.set_status(AgentStatus.WORKING)

                prompt = f"""
                Analyze these {len(critical_events)} critical disaster events:

                {json.dumps(critical_events[:3], indent=2)}

                Identify:
                1. Most severe event and why
                2. Any patterns (geographic clustering, escalating trends)
                3. Recommended priority level (1-100)
                4. One-sentence summary for other agents

                Return JSON:
                {{
                    "severity": <number 0-100>,
                    "pattern_detected": "<pattern description or null>",
                    "priority": <1-100>,
                    "summary": "<one sentence>",
                    "needs_analysis": <true/false>
                }}
                """

                response_text = await self.ask_gemini(prompt)

                # Parse Gemini response
                try:
                    # Extract JSON from response (Gemini might wrap it in markdown)
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        analysis = json.loads(response_text[json_start:json_end])
                    else:
                        # Fallback if JSON parsing fails
                        analysis = {
                            "severity": 75,
                            "pattern_detected": "Critical events detected",
                            "priority": 80,
                            "summary": f"{len(critical_events)} critical events require immediate attention",
                            "needs_analysis": True
                        }
                except json.JSONDecodeError:
                    logger.warning(f"Scout: Failed to parse Gemini JSON, using fallback")
                    analysis = {
                        "severity": 70,
                        "pattern_detected": "Analysis pending",
                        "priority": 75,
                        "summary": f"Detected {len(critical_events)} critical events",
                        "needs_analysis": True
                    }

                # Send message to other agents
                message = self.send_message(
                    content=analysis['summary'],
                    priority="high" if analysis['priority'] > 70 else "normal",
                    data=analysis
                )

                self.set_status(AgentStatus.ACTIVE)

                return {
                    "status": "critical_detected",
                    "events_monitored": total_events,
                    "critical_events": len(critical_events),
                    "analysis": analysis,
                    "message": message.to_dict()
                }

            else:
                # No critical events - routine monitoring
                summary = f"Monitoring {total_events} events - All normal"
                message = self.send_message(summary, priority="low")

                return {
                    "status": "normal",
                    "events_monitored": total_events,
                    "critical_events": 0,
                    "analysis": {
                        "severity": 20,
                        "summary": summary,
                        "needs_analysis": False
                    },
                    "message": message.to_dict()
                }

        except Exception as e:
            logger.error(f"Scout Agent error: {e}")
            self.set_status(AgentStatus.ERROR)
            raise
