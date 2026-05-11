"""Smart router for team routing with load balancing and skill matching.

Routes classified tickets to the appropriate team/agent based on:
- Category and subcategory
- Agent skills and availability
- Load balancing
- Priority and SLA
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import yaml

from supportagent.advanced_classifier import ClassificationResult

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Ticket priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RoutingStrategy(Enum):
    """Available routing strategies."""

    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    SKILL_MATCH = "skill_match"
    PRIORITY_FIRST = "priority_first"
    HYBRID = "hybrid"


@dataclass
class Agent:
    """Represents a support agent."""

    id: str
    name: str
    email: str
    skills: List[str] = field(default_factory=list)
    is_available: bool = True
    current_load: int = 0
    max_load: int = 10
    avg_response_time: float = 3600.0  # seconds
    rating: float = 4.5
    team: str = "general"

    @property
    def available_capacity(self) -> int:
        return max(0, self.max_load - self.current_load)

    @property
    def is_overloaded(self) -> bool:
        return self.current_load >= self.max_load

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "skills": self.skills,
            "is_available": self.is_available,
            "current_load": self.current_load,
            "max_load": self.max_load,
            "avg_response_time": self.avg_response_time,
            "rating": self.rating,
            "team": self.team,
        }


@dataclass
class Team:
    """Represents a support team."""

    id: str
    name: str
    agents: List[Agent] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    escalation_threshold: float = 0.8  # Load threshold for escalation

    @property
    def total_load(self) -> int:
        return sum(a.current_load for a in self.agents)

    @property
    def available_agents(self) -> List[Agent]:
        return [a for a in self.agents if a.is_available and not a.is_overloaded]

    @property
    def avg_load(self) -> float:
        if not self.agents:
            return 0
        return self.total_load / len(self.agents)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "agents": [a.to_dict() for a in self.agents],
            "skills": self.skills,
            "total_load": self.total_load,
            "avg_load": self.avg_load,
        }


@dataclass
class RoutingResult:
    """Result of a routing operation."""

    agent_id: str
    agent_name: str
    team_id: str
    team_name: str
    strategy: str
    confidence: float
    estimated_response_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "team_id": self.team_id,
            "team_name": self.team_name,
            "strategy": self.strategy,
            "confidence": self.confidence,
            "estimated_response_time": self.estimated_response_time,
            "metadata": self.metadata,
        }


class TeamRegistry:
    """Manages teams and agents."""

    def __init__(self, config_path: Optional[str] = None):
        self._teams: Dict[str, Team] = {}
        self._agents: Dict[str, Agent] = {}
        self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]):
        """Load team configuration."""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "router_config.yaml"
            )

        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = yaml.safe_load(f) or {}

            for team_id, team_data in data.items():
                if isinstance(team_data, dict):
                    agents_data = team_data.get("agents", [])
                    agents = []
                    for agent_data in agents_data:
                        if isinstance(agent_data, dict):
                            agent = Agent(
                                id=agent_data.get("id", f"{team_id}_agent_{len(agents)}"),
                                name=agent_data.get("name", "Agent"),
                                email=agent_data.get("email", ""),
                                skills=agent_data.get("skills", []),
                                is_available=agent_data.get("is_available", True),
                                current_load=agent_data.get("current_load", 0),
                                max_load=agent_data.get("max_load", 10),
                                avg_response_time=agent_data.get(
                                    "avg_response_time", 3600
                                ),
                                rating=agent_data.get("rating", 4.5),
                                team=team_id,
                            )
                            agents.append(agent)
                            self._agents[agent.id] = agent

                    team = Team(
                        id=team_id,
                        name=team_data.get("name", team_id),
                        agents=agents,
                        skills=team_data.get("skills", []),
                        escalation_threshold=team_data.get(
                            "escalation_threshold", 0.8
                        ),
                    )
                    self._teams[team_id] = team

    def get_team(self, team_id: str) -> Optional[Team]:
        return self._teams.get(team_id)

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)

    def get_all_teams(self) -> List[Team]:
        return list(self._teams.values())

    def get_all_agents(self) -> List[Agent]:
        return list(self._agents.values())

    def add_team(self, team: Team):
        self._teams[team.id] = team
        for agent in team.agents:
            self._agents[agent.id] = agent

    def add_agent(self, agent: Agent):
        self._agents[agent.id] = agent
        team = self._teams.get(agent.team)
        if team:
            team.agents.append(agent)

    def update_agent_load(self, agent_id: str, load_delta: int):
        """Update an agent's current load."""
        agent = self._agents.get(agent_id)
        if agent:
            agent.current_load = max(0, agent.current_load + load_delta)

    def get_team_for_category(self, category: str) -> Optional[str]:
        """Get the recommended team for a category."""
        # Default mapping
        category_team_map = {
            "billing": "billing_team",
            "technical": "technical_team",
            "account": "account_team",
            "general": "general_team",
            "urgent": "escalation_team",
        }
        return category_team_map.get(category)


class SmartRouter:
    """Routes tickets to appropriate agents/teams."""

    def __init__(
        self,
        team_registry: Optional[TeamRegistry] = None,
        strategy: RoutingStrategy = RoutingStrategy.HYBRID,
    ):
        self.registry = team_registry or TeamRegistry()
        self.strategy = strategy
        self._round_robin_index: Dict[str, int] = {}  # team -> index

    def route(
        self,
        classification: ClassificationResult,
        priority: Optional[Priority] = None,
    ) -> RoutingResult:
        """Route a classified ticket to an agent.

        Args:
            classification: The classification result.
            priority: Ticket priority.

        Returns:
            RoutingResult with the assigned agent.
        """
        # Determine target team
        target_team_id = self._get_target_team(classification.category)
        target_team = self.registry.get_team(target_team_id)

        if not target_team:
            # Fallback to any available team
            target_team = self._find_best_team(classification)

        if not target_team:
            return self._create_default_result()

        # Select agent based on strategy
        agent = self._select_agent(target_team, classification, priority)

        if not agent:
            # No available agents, escalate
            return self._create_escalation_result(target_team)

        # Update agent load
        self.registry.update_agent_load(agent.id, 1)

        return RoutingResult(
            agent_id=agent.id,
            agent_name=agent.name,
            team_id=target_team.id,
            team_name=target_team.name,
            strategy=self.strategy.value,
            confidence=self._calculate_routing_confidence(agent, classification),
            estimated_response_time=agent.avg_response_time,
            metadata={
                "team_load": target_team.total_load,
                "agent_capacity": agent.available_capacity,
                "skill_match": self._calculate_skill_match(agent, classification),
            },
        )

    def _get_target_team(self, category: str) -> str:
        """Get the target team for a category."""
        return self.registry.get_team_for_category(category) or "general_team"

    def _find_best_team(
        self, classification: ClassificationResult
    ) -> Optional[Team]:
        """Find the best available team."""
        best_team = None
        min_load = float("inf")

        for team in self.registry.get_all_teams():
            if team.available_agents and team.avg_load < min_load:
                min_load = team.avg_load
                best_team = team

        return best_team

    def _select_agent(
        self,
        team: Team,
        classification: ClassificationResult,
        priority: Optional[Priority],
    ) -> Optional[Agent]:
        """Select the best agent from a team."""
        available = team.available_agents

        if not available:
            return None

        if self.strategy == RoutingStrategy.LEAST_LOADED:
            return min(available, key=lambda a: a.current_load)

        elif self.strategy == RoutingStrategy.SKILL_MATCH:
            return self._best_skill_match(available, classification)

        elif self.strategy == RoutingStrategy.PRIORITY_FIRST:
            # Prioritize agents with best ratings for urgent tickets
            if priority and priority in (Priority.URGENT, Priority.HIGH):
                return max(available, key=lambda a: a.rating)
            return min(available, key=lambda a: a.current_load)

        elif self.strategy == RoutingStrategy.ROUND_ROBIN:
            if team.id not in self._round_robin_index:
                self._round_robin_index[team.id] = 0
            idx = self._round_robin_index[team.id] % len(available)
            self._round_robin_index[team.id] = idx + 1
            return available[idx]

        else:  # HYBRID
            return self._hybrid_select(available, classification, priority)

    def _best_skill_match(
        self, agents: List[Agent], classification: ClassificationResult
    ) -> Agent:
        """Find the agent with the best skill match."""
        def skill_score(agent: Agent) -> float:
            score = 0.0
            for skill in agent.skills:
                if skill.lower() in classification.category.lower():
                    score += 1.0
                for subcat, conf in classification.subcategories.items():
                    if skill.lower() in subcat.lower():
                        score += conf
            return score

        return max(agents, key=skill_score)

    def _hybrid_select(
        self,
        agents: List[Agent],
        classification: ClassificationResult,
        priority: Optional[Priority],
    ) -> Agent:
        """Hybrid selection considering load, skills, and rating."""
        def combined_score(agent: Agent) -> float:
            # Load score (lower load = higher score)
            load_score = 1.0 - (agent.current_load / max(agent.max_load, 1))

            # Skill score
            skill_score = self._calculate_skill_match(agent, classification)

            # Rating score
            rating_score = agent.rating / 5.0

            # Weighted combination
            return load_score * 0.4 + skill_score * 0.4 + rating_score * 0.2

        return max(agents, key=combined_score)

    def _calculate_skill_match(
        self, agent: Agent, classification: ClassificationResult
    ) -> float:
        """Calculate skill match score."""
        if not agent.skills:
            return 0.5  # Neutral

        category_match = any(
            skill.lower() in classification.category.lower()
            for skill in agent.skills
        )

        subcat_match = any(
            skill.lower() in subcat.lower()
            for skill in agent.skills
            for subcat in classification.subcategories.keys()
        )

        if category_match and subcat_match:
            return 1.0
        elif category_match or subcat_match:
            return 0.7
        return 0.3

    def _calculate_routing_confidence(
        self, agent: Agent, classification: ClassificationResult
    ) -> float:
        """Calculate routing confidence."""
        skill_match = self._calculate_skill_match(agent, classification)
        load_factor = agent.available_capacity / max(agent.max_load, 1)
        rating_factor = agent.rating / 5.0

        return min(1.0, (skill_match * 0.5 + load_factor * 0.3 + rating_factor * 0.2))

    def _create_default_result(self) -> RoutingResult:
        """Create a default routing result."""
        return RoutingResult(
            agent_id="unassigned",
            agent_name="Unassigned",
            team_id="unassigned",
            team_name="Unassigned",
            strategy="default",
            confidence=0.0,
            estimated_response_time=7200.0,
            metadata={"reason": "No teams available"},
        )

    def _create_escalation_result(self, team: Team) -> RoutingResult:
        """Create an escalation result."""
        return RoutingResult(
            agent_id="escalation",
            agent_name="Escalation Team",
            team_id=team.id,
            team_name=team.name,
            strategy="escalation",
            confidence=0.5,
            estimated_response_time=1800.0,
            metadata={"reason": "No available agents"},
        )

    def get_team_status(self, team_id: str) -> Dict[str, Any]:
        """Get status of a team."""
        team = self.registry.get_team(team_id)
        if not team:
            return {"error": "Team not found"}

        return {
            "team_id": team.id,
            "team_name": team.name,
            "total_agents": len(team.agents),
            "available_agents": len(team.available_agents),
            "total_load": team.total_load,
            "avg_load": team.avg_load,
            "agents": [a.to_dict() for a in team.agents],
        }

    def get_all_team_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all teams."""
        return {
            team.id: self.get_team_status(team.id)
            for team in self.registry.get_all_teams()
        }
