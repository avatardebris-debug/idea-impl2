"""Tests for the response generator."""

import os
import tempfile
import textwrap
import unittest

from supportagent.models import DraftResponse, Ticket, TicketCategory, TicketSource
from supportagent.response_generator import ResponseGenerator, ResponseGeneratorError


class TestResponseGenerator(unittest.TestCase):
    """Tests for ResponseGenerator."""

    def setUp(self):
        """Set up test fixtures."""
        self.ticket = Ticket(
            ticket_id="test-001",
            source=TicketSource.EMAIL,
            subject="Billing Issue",
            body="I was charged twice for my subscription.",
            category=TicketCategory.BILLING,
            priority_score=7.5,
            created_at="2024-01-15T10:30:00+00:00",
        )

    def test_generate_response_with_default_template(self):
        """Test generating a response with the default template."""
        generator = ResponseGenerator()
        draft = generator.generate_response(
            self.ticket,
            template_name="general_response",
            tone="professional",
            team="billing_team",
        )

        self.assertIsInstance(draft, DraftResponse)
        self.assertEqual(draft.ticket.ticket_id, "test-001")
        self.assertEqual(draft.tone, "professional")
        self.assertEqual(draft.template_used, "general_response")
        self.assertEqual(draft.team, "billing_team")
        self.assertIn("Hello", draft.content)
        self.assertIn("Best regards", draft.content)

    def test_generate_response_with_billing_template(self):
        """Test generating a response with the billing template."""
        generator = ResponseGenerator()
        draft = generator.generate_response(
            self.ticket,
            template_name="billing_response",
            tone="professional",
            team="billing_team",
        )

        self.assertIn("billing", draft.content.lower())
        self.assertIn("test-001", draft.content)

    def test_generate_response_with_empathetic_tone(self):
        """Test generating a response with empathetic tone."""
        generator = ResponseGenerator()
        draft = generator.generate_response(
            self.ticket,
            template_name="general_response",
            tone="empathetic",
            team="billing_team",
        )

        self.assertIn("I understand", draft.content.lower())
        self.assertIn("Best regards", draft.content)

    def test_generate_response_with_friendly_tone(self):
        """Test generating a response with friendly tone."""
        generator = ResponseGenerator()
        draft = generator.generate_response(
            self.ticket,
            template_name="general_response",
            tone="friendly",
            team="billing_team",
        )

        self.assertIn("Hi there", draft.content.lower())
        self.assertIn("Cheers", draft.content.lower())

    def test_generate_response_with_formal_tone(self):
        """Test generating a response with formal tone."""
        generator = ResponseGenerator()
        draft = generator.generate_response(
            self.ticket,
            template_name="general_response",
            tone="formal",
            team="billing_team",
        )

        self.assertIn("Dear", draft.content.lower())
        self.assertIn("Sincerely", draft.content.lower())

    def test_generate_response_with_technical_tone(self):
        """Test generating a response with technical tone."""
        generator = ResponseGenerator()
        draft = generator.generate_response(
            self.ticket,
            template_name="general_response",
            tone="technical",
            team="billing_team",
        )

        self.assertIn("Hello", draft.content.lower())
        self.assertIn("Best regards", draft.content)

    def test_generate_response_with_custom_template(self):
        """Test generating a response with a custom template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_yaml = textwrap.dedent("""\
                templates:
                  custom_template: |
                    Dear {subject},
                    
                    We have received your request regarding {body}.
                    
                    Our team will review this shortly.
                    
                    Best regards,
                    Support Team
            """)
            tones_yaml = textwrap.dedent("""\
                tone_styles:
                  professional:
                    greeting: "Hello"
                    closing: "Best regards"
                    formality: "medium"
            """)
            
            templates_path = os.path.join(tmpdir, "templates.yaml")
            tones_path = os.path.join(tmpdir, "tone_styles.yaml")
            
            with open(templates_path, "w") as f:
                f.write(templates_yaml)
            with open(tones_path, "w") as f:
                f.write(tones_yaml)
            
            generator = ResponseGenerator(config_dir=tmpdir)
            draft = generator.generate_response(
                self.ticket,
                template_name="custom_template",
                tone="professional",
                team="custom_team",
            )

            self.assertIn("Dear", draft.content)
            self.assertIn("Best regards", draft.content)

    def test_list_templates(self):
        """Test listing available templates."""
        generator = ResponseGenerator()
        templates = generator.list_templates()
        self.assertIn("general_response", templates)
        self.assertIn("billing_response", templates)

    def test_list_tone_styles(self):
        """Test listing available tone styles."""
        generator = ResponseGenerator()
        tones = generator.list_tone_styles()
        self.assertIn("professional", tones)
        self.assertIn("empathetic", tones)

    def test_generate_response_with_missing_template(self):
        """Test generating a response with a missing template raises an error."""
        generator = ResponseGenerator()
        with self.assertRaises(ResponseGeneratorError):
            generator.generate_response(
                self.ticket,
                template_name="nonexistent_template",
                tone="professional",
                team="billing_team",
            )

    def test_generate_response_with_missing_tone(self):
        """Test generating a response with a missing tone raises an error."""
        generator = ResponseGenerator()
        with self.assertRaises(ResponseGeneratorError):
            generator.generate_response(
                self.ticket,
                template_name="general_response",
                tone="nonexistent_tone",
                team="billing_team",
            )

    def test_generate_response_with_different_ticket(self):
        """Test generating a response with a different ticket."""
        ticket2 = Ticket(
            ticket_id="test-002",
            source=TicketSource.CHAT,
            subject="Technical Issue",
            body="My server is down.",
            category=TicketCategory.TECHNICAL,
            priority_score=9.0,
            created_at="2024-01-15T11:00:00+00:00",
        )
        
        generator = ResponseGenerator()
        draft = generator.generate_response(
            ticket2,
            template_name="general_response",
            tone="professional",
            team="technical_team",
        )

        self.assertIn("test-002", draft.content)
        self.assertIn("Technical Issue", draft.content)
        self.assertIn("technical_team", draft.team)

    def test_generate_response_with_account_template(self):
        """Test generating a response with the account template."""
        ticket = Ticket(
            ticket_id="test-003",
            source=TicketSource.EMAIL,
            subject="Account Update",
            body="I need to update my email address.",
            category=TicketCategory.ACCOUNT,
            priority_score=5.0,
            created_at="2024-01-15T12:00:00+00:00",
        )
        
        generator = ResponseGenerator()
        draft = generator.generate_response(
            ticket,
            template_name="account_response",
            tone="professional",
            team="account_team",
        )

        self.assertIn("account", draft.content.lower())
        self.assertIn("test-003", draft.content)

    def test_generate_response_with_escalation_template(self):
        """Test generating a response with the escalation template."""
        ticket = Ticket(
            ticket_id="test-004",
            source=TicketSource.EMAIL,
            subject="Escalation Request",
            body="I need to escalate this issue.",
            category=TicketCategory.ESCALATION,
            priority_score=9.5,
            created_at="2024-01-15T13:00:00+00:00",
        )
        
        generator = ResponseGenerator()
        draft = generator.generate_response(
            ticket,
            template_name="escalation_response",
            tone="professional",
            team="escalation_team",
        )

        self.assertIn("escalation", draft.content.lower())
        self.assertIn("test-004", draft.content)


if __name__ == "__main__":
    unittest.main()
