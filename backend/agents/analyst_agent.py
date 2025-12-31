"""
Analyst Agent - Deep analysis of detected crises
Investigates and provides detailed situation assessment
"""
import logging
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentStatus
import json

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """Performs deep analysis on flagged crisis events"""

    def __init__(self, gemini_client):
        super().__init__(
            agent_id="analyst-001",
            name="Analyst",
            role="Crisis Analysis & Impact Assessment",
            gemini_client=gemini_client
        )

    async def analyze(self, events: List[Dict], scout_analysis: Dict) -> Dict[str, Any]:
        """
        Perform deep analysis on critical events

        Args:
            events: List of critical events to analyze
            scout_analysis: Initial analysis from Scout agent

        Returns:
            Detailed analysis with impact assessment
        """
        self.set_status(AgentStatus.WORKING)

        try:
            # Get weather and social events
            weather_events = [e for e in events if e.get('source') in ['tomorrow.io', 'noaa']]
            social_events = [e for e in events if e.get('source') == 'social']

            # Build comprehensive prompt
            prompt = f"""
            CRISIS SITUATION ANALYSIS

            Scout Agent detected: {scout_analysis.get('summary', 'Critical events')}
            Severity Level: {scout_analysis.get('severity', 0)}/100

            WEATHER DATA:
            {json.dumps(weather_events[:3], indent=2)}

            SOCIAL MEDIA REPORTS:
            {json.dumps(social_events[:3], indent=2)}

            Provide detailed analysis:

            1. **Crisis Type**: What type of disaster? (fire, flood, earthquake, etc.)
            2. **Affected Area**: Which location(s) most impacted?
            3. **Population at Risk**: Estimate affected population
            4. **Immediate Hazards**: What are the immediate dangers?
            5. **Secondary Risks**: Potential cascading effects
            6. **Confidence Level**: How confident in this assessment? (0-100%)

            Return JSON:
            {{
                "crisis_type": "<type>",
                "affected_locations": ["<location>"],
                "estimated_population_at_risk": <number>,
                "immediate_hazards": ["<hazard1>", "<hazard2>"],
                "secondary_risks": ["<risk1>"],
                "confidence": <0-100>,
                "analysis_summary": "<2-3 sentence summary>",
                "requires_prediction": <true/false>
            }}
            """

            response_text = await self.ask_gemini(prompt)

            # Parse response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    analysis = json.loads(response_text[json_start:json_end])
                else:
                    # Fallback
                    analysis = {
                        "crisis_type": "multi-hazard",
                        "affected_locations": ["Multiple areas"],
                        "estimated_population_at_risk": 10000,
                        "immediate_hazards": ["Severe weather", "Fire risk"],
                        "secondary_risks": ["Infrastructure damage"],
                        "confidence": 70,
                        "analysis_summary": "Multiple critical events detected requiring immediate response.",
                        "requires_prediction": True
                    }
            except json.JSONDecodeError:
                logger.warning("Analyst: JSON parse failed, using fallback")
                analysis = {
                    "crisis_type": "pending",
                    "affected_locations": ["TBD"],
                    "estimated_population_at_risk": 5000,
                    "immediate_hazards": ["Under investigation"],
                    "secondary_risks": [],
                    "confidence": 50,
                    "analysis_summary": "Analysis in progress",
                    "requires_prediction": True
                }

            # Send message to other agents
            message_content = f"Confirmed {analysis['crisis_type']} affecting {', '.join(analysis['affected_locations'][:2])}"
            message = self.send_message(
                content=message_content,
                priority="high",
                data=analysis
            )

            self.set_status(AgentStatus.ACTIVE)

            return {
                "status": "analysis_complete",
                "analysis": analysis,
                "message": message.to_dict(),
                "events_analyzed": len(events)
            }

        except Exception as e:
            logger.error(f"Analyst Agent error: {e}")
            self.set_status(AgentStatus.ERROR)
            raise
