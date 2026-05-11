"""Workflow orchestrator for the support agent pipeline.

Orchestrates the full workflow:
1. Ingest ticket
2. Classify (hybrid ML + LLM)
3. Route to team/agent
4. Generate response
5. Quality check and deliver
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from supportagent.advanced_classifier import (
    ClassificationResult,
    HybridClassifier,
)
from supportagent.llm_adapters import LLMConfig, LLMProvider
from supportagent.response_generator import GeneratedResponse, ResponseGenerator
from supportagent.smart_router import (
    Priority,
    RoutingResult,
    RoutingStrategy,
    SmartRouter,
)

logger = logging.getLogger(__name__)


@dataclass
class SupportTicket:
    """Represents a customer support ticket."""

    id: str
    customer_name: str
    customer_email: str
    subject: str
    body: str
    category: Optional[str] = None
    priority: Optional[Priority] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return f"{self.subject}\n\n{self.body}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "subject": self.subject,
            "body": self.body,
            "category": self.category,
            "priority": self.priority.value if self.priority else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SupportTicket:
        priority = None
        if data.get("priority"):
            priority = Priority(data["priority"])
        return cls(
            id=data["id"],
            customer_name=data["customer_name"],
            customer_email=data["customer_email"],
            subject=data["subject"],
            body=data["body"],
            category=data.get("category"),
            priority=priority,
            metadata=data.get("metadata", {}),
        )


@dataclass
class WorkflowResult:
    """Result of the full workflow execution."""

    ticket_id: str
    classification: Optional[ClassificationResult] = None
    routing: Optional[RoutingResult] = None
    response: Optional[GeneratedResponse] = None
    status: str = "pending"
    execution_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "classification": (
                self.classification.to_dict() if self.classification else None
            ),
            "routing": self.routing.to_dict() if self.routing else None,
            "response": self.response.to_dict() if self.response else None,
            "status": self.status,
            "execution_time": self.execution_time,
            "errors": self.errors,
            "metadata": self.metadata,
        }

    @property
    def is_successful(self) -> bool:
        return self.status == "completed" and not self.errors

    @property
    def needs_human_review(self) -> bool:
        if self.classification and self.classification.needs_review:
            return True
        if self.response and self.response.quality_score < 0.5:
            return True
        return False


class SupportWorkflow:
    """Orchestrates the full support ticket workflow."""

    def __init__(
        self,
        classifier: Optional[HybridClassifier] = None,
        router: Optional[SmartRouter] = None,
        response_generator: Optional[ResponseGenerator] = None,
        llm_config: Optional[LLMConfig] = None,
    ):
        self.classifier = classifier or HybridClassifier(
            llm_config=llm_config or LLMConfig(provider=LLMProvider.MOCK)
        )
        self.router = router or SmartRouter()
        self.response_generator = response_generator or ResponseGenerator(
            llm_config=llm_config or LLMConfig(provider=LLMProvider.MOCK)
        )

    def execute(
        self,
        ticket: SupportTicket,
        auto_route: bool = True,
        auto_generate: bool = True,
        use_llm: bool = True,
    ) -> WorkflowResult:
        """Execute the full workflow for a ticket.

        Args:
            ticket: The support ticket to process.
            auto_route: Whether to automatically route the ticket.
            auto_generate: Whether to automatically generate a response.
            use_llm: Whether to use LLM for classification.

        Returns:
            WorkflowResult with the full processing result.
        """
        start_time = time.time()
        result = WorkflowResult(ticket_id=ticket.id)

        try:
            # Step 1: Classify
            logger.info(f"Classifying ticket {ticket.id}")
            classification = self.classifier.classify(
                ticket.text, use_llm=use_llm
            )
            result.classification = classification
            ticket.category = classification.category
            logger.info(
                f"Classified as {classification.category} "
                f"(confidence: {classification.confidence:.2f})"
            )

            # Step 2: Determine priority
            if not ticket.priority:
                ticket.priority = self._determine_priority(ticket)

            # Step 3: Route
            if auto_route:
                logger.info(f"Routing ticket {ticket.id}")
                routing = self.router.route(classification, ticket.priority)
                result.routing = routing
                logger.info(
                    f"Routed to {routing.agent_name} "
                    f"(team: {routing.team_name})"
                )

            # Step 4: Generate response
            if auto_generate:
                logger.info(f"Generating response for ticket {ticket.id}")
                response = self.response_generator.generate(
                    classification,
                    customer_name=ticket.customer_name,
                    order_id=ticket.metadata.get("order_id"),
                    use_llm=use_llm,
                )
                result.response = response
                logger.info(
                    f"Response generated (quality: {response.quality_score:.2f})"
                )

            result.status = "completed"

        except Exception as e:
            logger.error(f"Error processing ticket {ticket.id}: {e}")
            result.errors.append(str(e))
            result.status = "error"

        result.execution_time = time.time() - start_time
        result.metadata["priority"] = (
            ticket.priority.value if ticket.priority else None
        )

        return result

    def execute_batch(
        self,
        tickets: List[SupportTicket],
        **kwargs,
    ) -> List[WorkflowResult]:
        """Execute workflow for a batch of tickets."""
        return [self.execute(ticket, **kwargs) for ticket in tickets]

    def _determine_priority(self, ticket: SupportTicket) -> Priority:
        """Determine ticket priority based on content."""
        text = ticket.text.lower()

        urgent_keywords = [
            "urgent",
            "immediately",
            "asap",
            "emergency",
            "critical",
            "down",
            "broken",
            "not working",
        ]
        high_keywords = [
            "important",
            "concerned",
            "frustrated",
            "angry",
            "complaint",
        ]
        low_keywords = [
            "question",
            "wondering",
            "curious",
            "information",
            "general",
        ]

        urgent_count = sum(1 for kw in urgent_keywords if kw in text)
        high_count = sum(1 for kw in high_keywords if kw in text)
        low_count = sum(1 for kw in low_keywords if kw in text)

        if urgent_count >= 2 or ("down" in text or "emergency" in text):
            return Priority.URGENT
        elif urgent_count >= 1 or high_count >= 2:
            return Priority.HIGH
        elif low_count >= 2:
            return Priority.LOW
        return Priority.MEDIUM

    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        return {
            "classifier": {
                "type": type(self.classifier).__name__,
            },
            "router": {
                "type": type(self.router).__name__,
                "strategy": self.router.strategy.value,
            },
            "response_generator": {
                "type": type(self.response_generator).__name__,
            },
        }


class WorkflowPipeline:
    """Pipeline that processes tickets through multiple stages."""

    def __init__(
        self,
        workflow: Optional[SupportWorkflow] = None,
        llm_config: Optional[LLMConfig] = None,
    ):
        self.workflow = workflow or SupportWorkflow(llm_config=llm_config)
        self._history: List[WorkflowResult] = []

    def process(self, ticket: SupportTicket, **kwargs) -> WorkflowResult:
        """Process a single ticket through the pipeline."""
        result = self.workflow.execute(ticket, **kwargs)
        self._history.append(result)
        return result

    def process_from_file(
        self, filepath: str, **kwargs
    ) -> List[WorkflowResult]:
        """Process tickets from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        if isinstance(data, list):
            tickets = [SupportTicket.from_dict(t) for t in data]
        elif isinstance(data, dict):
            tickets = [SupportTicket.from_dict(data)]
        else:
            raise ValueError(f"Invalid data format: {type(data)}")

        return self.process_batch(tickets, **kwargs)

    def process_batch(
        self, tickets: List[SupportTicket], **kwargs
    ) -> List[WorkflowResult]:
        """Process a batch of tickets."""
        results = self.workflow.execute_batch(tickets, **kwargs)
        self._history.extend(results)
        return results

    def get_history(self) -> List[WorkflowResult]:
        """Get the processing history."""
        return self._history

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all processed tickets."""
        if not self._history:
            return {"total": 0}

        total = len(self._history)
        completed = sum(1 for r in self._history if r.is_successful)
        errors = sum(1 for r in self._history if r.status == "error")
        needs_review = sum(1 for r in self._history if r.needs_human_review)

        # Category distribution
        categories: Dict[str, int] = {}
        for r in self._history:
            if r.classification:
                cat = r.classification.category
                categories[cat] = categories.get(cat, 0) + 1

        # Average execution time
        avg_time = (
            sum(r.execution_time for r in self._history) / total
            if total > 0
            else 0
        )

        return {
            "total": total,
            "completed": completed,
            "errors": errors,
            "needs_review": needs_review,
            "avg_execution_time": avg_time,
            "category_distribution": categories,
        }


def create_default_pipeline(
    llm_provider: LLMProvider = LLMProvider.MOCK,
    routing_strategy: RoutingStrategy = RoutingStrategy.HYBRID,
) -> WorkflowPipeline:
    """Create a default pipeline configuration."""
    llm_config = LLMConfig(provider=llm_provider)

    workflow = SupportWorkflow(llm_config=llm_config)

    return WorkflowPipeline(workflow=workflow)
