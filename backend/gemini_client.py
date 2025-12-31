"""
Google Gemini AI Client for CrisisFlow
Generates intelligent situation reports from disaster data
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
import google.generativeai as genai
from config import logger, GOOGLE_API_KEY

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Alert prompt template
ALERT_PROMPT_TEMPLATE = """
You are CrisisFlow AI, a disaster response intelligence system. Analyze the following real-time data and generate a comprehensive situation report.

## CURRENT CONDITIONS

### Weather Risk Data (Last 30 minutes)
{weather_data}

### Social Media Signals (Last 30 minutes)
{social_data}

### Aggregated Hotspots
{hotspot_data}

## YOUR TASK

Generate a response in the following JSON format:
{{
    "situation_report": "A 2-3 sentence summary of the current situation, highlighting the most critical threats and their locations.",
    "recommended_actions": [
        {{
            "priority": "critical",
            "action": "Specific actionable recommendation",
            "reason": "Why this action is needed"
        }},
        {{
            "priority": "high",
            "action": "Second recommendation",
            "reason": "Why this action is needed"
        }},
        {{
            "priority": "moderate",
            "action": "Third recommendation",
            "reason": "Why this action is needed"
        }}
    ],
    "risk_summary": {{
        "fire": "low|moderate|high|critical",
        "flood": "low|moderate|high|critical",
        "overall": "low|moderate|high|critical"
    }},
    "predictions": [
        {{
            "timeframe": "+2H",
            "event": "Description of predicted event",
            "probability": 85,
            "severity": "critical|high|moderate|low"
        }},
        {{
            "timeframe": "+4H",
            "event": "Description of predicted event",
            "probability": 70,
            "severity": "critical|high|moderate|low"
        }},
        {{
            "timeframe": "+6H",
            "event": "Description of predicted event",
            "probability": 65,
            "severity": "critical|high|moderate|low"
        }}
    ],
    "resource_dispatch": [
        {{
            "resource": "Emergency Response Teams",
            "quantity": 5,
            "priority": "critical",
            "deployment_location": "Specific area or grid",
            "reason": "Why needed"
        }},
        {{
            "resource": "Medical Units",
            "quantity": 3,
            "priority": "high",
            "deployment_location": "Specific area or grid",
            "reason": "Why needed"
        }},
        {{
            "resource": "Evacuation Vehicles",
            "quantity": 8,
            "priority": "high",
            "deployment_location": "Specific area or grid",
            "reason": "Why needed"
        }}
    ],
    "evacuation_zones": [
        {{
            "location": "Specific neighborhood or coordinates",
            "radius_miles": 3,
            "priority": "immediate|high|moderate",
            "estimated_population": 5000,
            "primary_threat": "fire|flood|wind",
            "evacuation_routes": ["Route 1 North", "Highway 50 East"]
        }}
    ]
}}

IMPORTANT:
- Use ONLY the data provided above for predictions, resource calculations, and evacuation zones
- Base predictions on observed trends (e.g., if fire index is rising, predict escalation)
- Calculate resource quantities based on event counts and severity levels
- Identify evacuation zones from critical/high risk areas in the data
- Estimate population realistically based on urban/rural location context
- Be specific about locations using the actual location names from the data
- Prioritize life safety in all recommendations
"""

class GeminiClient:
    def __init__(self):
        """Initialize Gemini client"""
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("Gemini AI client initialized")

    def format_weather_data(self, weather_events: List[Dict]) -> str:
        """Format weather events for the prompt"""
        if not weather_events:
            return "No recent weather risk data available."

        # Group by location
        by_location = {}
        for event in weather_events[-10:]:  # Last 10 events
            loc_name = event.get("location", {}).get("name", "Unknown")
            if loc_name not in by_location:
                by_location[loc_name] = []
            by_location[loc_name].append(event)

        # Format for prompt
        lines = []
        for location, events in by_location.items():
            latest = events[-1]
            data = latest.get("data", {})
            lines.append(f"- **{location}**: Fire Index={data.get('fire_index', 0)}, "
                        f"Flood Index={data.get('flood_index', 0)}, "
                        f"Risk Level={latest.get('risk_level', 'unknown')}, "
                        f"Temp={data.get('temperature', 0)}°C, "
                        f"Humidity={data.get('humidity', 0)}%")

        return "\n".join(lines)

    def format_social_data(self, social_events: List[Dict]) -> str:
        """Format social events for the prompt"""
        if not social_events:
            return "No recent social media reports."

        # Group by category and urgency
        critical_events = []
        high_events = []
        other_events = []

        for event in social_events[-20:]:  # Last 20 events
            data = event.get("data", {})
            urgency = data.get("urgency", "low")
            text = data.get("text", "")[:100]  # Truncate long texts
            category = data.get("category", "unknown")

            event_str = f"[{category}] {text}"

            if urgency == "critical":
                critical_events.append(event_str)
            elif urgency == "high":
                high_events.append(event_str)
            else:
                other_events.append(event_str)

        lines = []
        if critical_events:
            lines.append(f"**CRITICAL ({len(critical_events)} reports):**")
            for event in critical_events[:5]:
                lines.append(f"  - {event}")

        if high_events:
            lines.append(f"**HIGH ({len(high_events)} reports):**")
            for event in high_events[:5]:
                lines.append(f"  - {event}")

        if not lines:
            lines.append(f"**OTHER ({len(other_events)} reports)**")

        return "\n".join(lines)

    def format_hotspot_data(self, hotspots: List[Dict]) -> str:
        """Format hotspot data for the prompt"""
        if not hotspots:
            return "No significant hotspots detected."

        lines = []
        for hotspot in hotspots[:5]:  # Top 5 hotspots
            lines.append(f"- Grid ({hotspot['grid_lat']}, {hotspot['grid_lon']}): "
                        f"Risk={hotspot['risk_level']}, "
                        f"Fire Avg={hotspot['avg_fire_index']}, "
                        f"Flood Avg={hotspot['avg_flood_index']}, "
                        f"Social Reports={hotspot['social_count']}")

        return "\n".join(lines)

    async def generate_alert(self,
                            weather_events: List[Dict],
                            social_events: List[Dict],
                            hotspots: List[Dict],
                            focus_area: Optional[Dict] = None) -> Dict:
        """Generate AI situation report and recommendations"""
        try:
            # Format data for prompt
            weather_str = self.format_weather_data(weather_events)
            social_str = self.format_social_data(social_events)
            hotspot_str = self.format_hotspot_data(hotspots)

            # Build prompt
            prompt = ALERT_PROMPT_TEMPLATE.format(
                weather_data=weather_str,
                social_data=social_str,
                hotspot_data=hotspot_str
            )

            logger.info("Generating AI alert with Gemini...")

            # Generate response
            response = self.model.generate_content(prompt)

            # Parse JSON response
            response_text = response.text

            # Clean up response (sometimes Gemini adds markdown formatting)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            # Parse JSON
            alert_data = json.loads(response_text.strip())

            # Add metadata
            alert_data["alert_id"] = str(uuid.uuid4())
            alert_data["generated_at"] = datetime.now(timezone.utc).isoformat()

            # Add focus area if provided
            if focus_area:
                alert_data["focus_area"] = focus_area

            logger.info("AI alert generated successfully")
            return alert_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            # Return a fallback response
            return self._create_fallback_alert(weather_events, social_events, hotspots)

        except Exception as e:
            logger.error(f"Error generating AI alert: {e}")
            # Return a fallback response
            return self._create_fallback_alert(weather_events, social_events, hotspots)

    def _create_fallback_alert(self,
                               weather_events: List[Dict],
                               social_events: List[Dict],
                               hotspots: List[Dict]) -> Dict:
        """Create a fallback alert if AI generation fails"""
        # Analyze data manually
        critical_count = sum(1 for h in hotspots if h.get("risk_level") == "critical")
        high_count = sum(1 for h in hotspots if h.get("risk_level") == "high")

        # Determine overall risk
        if critical_count > 0:
            overall_risk = "critical"
        elif high_count > 2:
            overall_risk = "high"
        elif high_count > 0:
            overall_risk = "moderate"
        else:
            overall_risk = "low"

        # Calculate average indices
        fire_indices = [e.get("data", {}).get("fire_index", 0) for e in weather_events if e]
        flood_indices = [e.get("data", {}).get("flood_index", 0) for e in weather_events if e]

        avg_fire = sum(fire_indices) / len(fire_indices) if fire_indices else 0
        avg_flood = sum(flood_indices) / len(flood_indices) if flood_indices else 0

        # Determine specific risks
        fire_risk = "critical" if avg_fire > 70 else "high" if avg_fire > 50 else "moderate" if avg_fire > 30 else "low"
        flood_risk = "critical" if avg_flood > 70 else "high" if avg_flood > 50 else "moderate" if avg_flood > 30 else "low"

        return {
            "alert_id": str(uuid.uuid4()),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "situation_report": f"Automated analysis detected {critical_count} critical and {high_count} high-risk areas. "
                              f"Average fire index is {avg_fire:.1f} and flood index is {avg_flood:.1f}. "
                              f"Emergency response may be required in affected areas.",
            "recommended_actions": [
                {
                    "priority": 1,
                    "action": "Monitor critical risk areas closely",
                    "reason": f"{critical_count} areas showing critical risk levels"
                },
                {
                    "priority": 2,
                    "action": "Prepare emergency response teams",
                    "reason": f"{len(social_events)} social media reports indicate ground-level impacts"
                },
                {
                    "priority": 3,
                    "action": "Issue public warnings for high-risk zones",
                    "reason": "Preventive measures can reduce casualties"
                }
            ],
            "risk_summary": {
                "fire": fire_risk,
                "flood": flood_risk,
                "overall": overall_risk
            },
            "fallback": True
        }

    async def answer_question(self, question: str, context: Dict) -> str:
        """
        Answer a specific question about the crisis situation
        Uses Gemini to provide context-aware responses
        """
        try:
            # Extract context data
            events = context.get("events", {})
            weather_events = events.get("weather", [])
            social_events = events.get("social", [])
            hotspots = context.get("hotspots", [])
            stats = context.get("stats", {})

            # Build context summary
            context_summary = f"""
CURRENT SITUATION CONTEXT:

Weather Events: {len(weather_events)} total
- {self.format_weather_data(weather_events)}

Social Reports: {len(social_events)} total
- {self.format_social_data(social_events)}

Hotspots: {len(hotspots)} active
- {self.format_hotspot_data(hotspots)}

QUESTION: {question}

Provide a clear, concise answer based ONLY on the data above. Be specific about locations, numbers, and risks. If you don't have enough information, say so and suggest what data would be needed.
"""

            logger.info(f"Sending Q&A request to Gemini for question: {question}")

            response = await asyncio.to_thread(
                self.model.generate_content,
                context_summary
            )

            answer = response.text

            logger.info(f"Gemini Q&A response generated successfully")

            return answer

        except Exception as e:
            logger.error(f"Error in Gemini Q&A: {e}")
            # Return a helpful fallback response
            return f"I'm having trouble accessing the AI service right now. However, based on the current data: we're monitoring {len(weather_events)} weather events and {len(social_events)} social media reports across {len(hotspots)} hotspot areas. Please check the other tabs for detailed information, or try asking your question again."

# Global client instance
gemini_client = GeminiClient()