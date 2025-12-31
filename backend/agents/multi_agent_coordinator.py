"""
Multi-Agent Coordinator - Orchestrates all 5 agents working together
This is the main entry point for the agent system
"""
import logging
import asyncio
from typing import Dict, List, Any
from datetime import datetime

from .scout_agent import ScoutAgent
from .analyst_agent import AnalystAgent
from .predictor_agent import PredictorAgent
from .coordinator_agent import CoordinatorAgent
from .communicator_agent import CommunicatorAgent

logger = logging.getLogger(__name__)


class MultiAgentCoordinator:
    """Coordinates multiple AI agents working together on crisis response"""

    def __init__(self, gemini_client):
        self.gemini = gemini_client

        # Initialize all 5 agents
        logger.info("🚀 Initializing Multi-Agent System...")

        self.scout = ScoutAgent(gemini_client)
        self.analyst = AnalystAgent(gemini_client)
        self.predictor = PredictorAgent(gemini_client)
        self.coordinator = CoordinatorAgent(gemini_client)
        self.communicator = CommunicatorAgent(gemini_client)

        self.agents = {
            "scout": self.scout,
            "analyst": self.analyst,
            "predictor": self.predictor,
            "coordinator": self.coordinator,
            "communicator": self.communicator
        }

        self.collaboration_log: List[Dict] = []
        self.last_run = None
        self.run_count = 0

        logger.info("✅ Multi-Agent System ready - 5 agents online")

    async def analyze_situation(self, events: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Run all agents in sequence to analyze a crisis situation

        This is the main orchestration method that coordinates:
        Scout → Analyst → Predictor → Coordinator → Communicator

        Args:
            events: Dictionary with 'weather' and 'social' event lists

        Returns:
            Complete multi-agent analysis result
        """
        start_time = datetime.utcnow()
        self.run_count += 1

        logger.info(f"🎯 Multi-Agent Analysis #{self.run_count} starting...")

        try:
            # Clear collaboration log for this run
            self.collaboration_log = []

            # STEP 1: Scout Agent - Initial detection
            logger.info("1️⃣ Scout Agent scanning events...")
            scout_result = await self.scout.analyze(events)
            self._log_collaboration(self.scout.message_history[-1] if self.scout.message_history else None)

            # Check if Scout found anything critical
            if scout_result['status'] == 'normal':
                logger.info("✅ Scout: All normal - no critical events detected")
                return {
                    "status": "normal",
                    "agents_run": ["scout"],
                    "collaboration_log": self.collaboration_log,
                    "summary": "All systems normal - routine monitoring",
                    "run_time_seconds": (datetime.utcnow() - start_time).total_seconds()
                }

            # STEP 2: Analyst Agent - Deep analysis
            logger.info("2️⃣ Analyst Agent investigating crisis...")
            weather_events = events.get('weather', [])
            social_events = events.get('social', [])
            all_events = weather_events + social_events

            analyst_result = await self.analyst.analyze(all_events, scout_result['analysis'])
            self._log_collaboration(self.analyst.message_history[-1] if self.analyst.message_history else None)

            # STEP 3: Predictor Agent - Forecast timeline
            if analyst_result['analysis'].get('requires_prediction', True):
                logger.info("3️⃣ Predictor Agent generating forecast...")
                predictor_result = await self.predictor.analyze(all_events, analyst_result)
                self._log_collaboration(self.predictor.message_history[-1] if self.predictor.message_history else None)
            else:
                logger.info("⏭️ Prediction not required")
                predictor_result = {"status": "skipped", "predictions": {}}

            # STEP 4: Coordinator Agent - Make decisions
            logger.info("4️⃣ Coordinator Agent making decisions...")
            coordinator_result = await self.coordinator.analyze(scout_result, analyst_result, predictor_result)
            self._log_collaboration(self.coordinator.message_history[-1] if self.coordinator.message_history else None)

            # STEP 5: Communicator Agent - Generate alert
            logger.info("5️⃣ Communicator Agent drafting alert...")
            communicator_result = await self.communicator.analyze(coordinator_result, analyst_result, predictor_result)
            self._log_collaboration(self.communicator.message_history[-1] if self.communicator.message_history else None)

            # Compile complete result
            end_time = datetime.utcnow()
            run_time = (end_time - start_time).total_seconds()

            result = {
                "status": "analysis_complete",
                "run_id": self.run_count,
                "timestamp": end_time.isoformat(),
                "run_time_seconds": run_time,

                # Individual agent results
                "scout": scout_result,
                "analyst": analyst_result,
                "predictor": predictor_result,
                "coordinator": coordinator_result,
                "communicator": communicator_result,

                # Summary
                "severity": scout_result.get('analysis', {}).get('severity', 0),
                "crisis_type": analyst_result.get('analysis', {}).get('crisis_type', 'unknown'),
                "response_level": coordinator_result.get('decision', {}).get('response_level', 'advisory'),
                "alert_ready": communicator_result.get('status') == 'alert_ready',

                # Agent collaboration chat
                "collaboration_log": self.collaboration_log,

                # Agent status
                "agents": {
                    agent_id: agent.to_dict()
                    for agent_id, agent in self.agents.items()
                }
            }

            self.last_run = result

            logger.info(f"✅ Multi-Agent Analysis complete in {run_time:.2f}s")
            logger.info(f"   Severity: {result['severity']}/100")
            logger.info(f"   Response: {result['response_level'].upper()}")
            logger.info(f"   Alert: {'READY' if result['alert_ready'] else 'N/A'}")

            return result

        except Exception as e:
            logger.error(f"❌ Multi-Agent Coordinator error: {e}")
            raise

    def _log_collaboration(self, message):
        """Log agent collaboration message"""
        if message:
            self.collaboration_log.append(message.to_dict())

    def get_status(self) -> Dict[str, Any]:
        """Get current status of all agents"""
        return {
            "system_status": "online",
            "agents": {
                agent_id: agent.to_dict()
                for agent_id, agent in self.agents.items()
            },
            "last_run": self.last_run.get('timestamp') if self.last_run else None,
            "total_runs": self.run_count,
            "collaboration_log_size": len(self.collaboration_log)
        }

    def get_collaboration_history(self, limit: int = 50) -> List[Dict]:
        """Get recent collaboration messages"""
        return self.collaboration_log[-limit:]
