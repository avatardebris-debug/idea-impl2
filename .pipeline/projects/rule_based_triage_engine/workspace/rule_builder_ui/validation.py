"""RuleForm — validates rule data from user input before saving."""

from __future__ import annotations

VALID_FIELDS = {"subject", "from", "body", "has_attachment", "priority_header"}
VALID_OPERATORS = {"contains", "not_contains", "equals", "regex", "is_empty", "gt", "lt"}
VALUE_OPERATORS = {"contains", "not_contains", "equals", "regex"}
VALID_ACTION_TYPES = {"tag", "route", "archive", "flag", "set_priority", "assign_category", "notify", "auto_resolve", "escalate"}


class RuleForm:
    """Validates rule data from user input before saving.

    Validates required fields (name, conditions, actions), checks that
    conditions have valid field/operator combinations, ensures values are
    present for operators that require them, validates action types, and
    validates priority is an integer between 0 and 100.

    Attributes:
        data: The raw rule dictionary passed for validation.
        errors: A list of error messages. Empty list means the rule is valid.
    """

    def __init__(self, data: dict) -> None:
        self.data: dict = data
        self.errors: list[str] = []
        self._run_validation()

    def _run_validation(self) -> None:
        """Run all validation checks."""
        self._validate_name(self.data)
        self._validate_conditions(self.data)
        self._validate_actions(self.data)
        self._validate_priority(self.data)

    def is_valid(self) -> bool:
        """Return True if there are no validation errors."""
        return len(self.errors) == 0

    @classmethod
    def validate(cls, rule_dict: dict) -> list[str]:
        """Validate a rule dictionary and return a list of error messages.

        Args:
            rule_dict: A dictionary representing a rule with fields like
                       'name', 'conditions', 'actions', 'priority', 'enabled'.

        Returns:
            A list of error messages. An empty list means the rule is valid.
        """
        form = cls(rule_dict)
        form._validate_name(rule_dict)
        form._validate_conditions(rule_dict)
        form._validate_actions(rule_dict)
        form._validate_priority(rule_dict)
        return form.errors

    def _validate_name(self, rule_dict: dict) -> None:
        """Validate the rule name field."""
        name = rule_dict.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            self.errors.append("Rule name is required and must be a non-empty string.")

    def _validate_conditions(self, rule_dict: dict) -> None:
        """Validate the conditions field."""
        conditions = rule_dict.get("conditions")

        if conditions is None:
            self.errors.append("Conditions are required.")
            return

        if not isinstance(conditions, list):
            self.errors.append("Conditions must be a list.")
            return

        # Allow empty conditions list
        if len(conditions) == 0:
            return

        for i, cond in enumerate(conditions):
            if not isinstance(cond, dict):
                self.errors.append(f"Condition {i} must be a dictionary.")
                continue

            self._validate_condition_field(cond, i)
            self._validate_condition_operator(cond, i)
            self._validate_condition_value(cond, i)

    def _validate_condition_field(self, cond: dict, index: int) -> None:
        """Validate the field of a condition."""
        field = cond.get("field")
        if not field or not isinstance(field, str) or field not in VALID_FIELDS:
            self.errors.append(
                f"Condition {index}: field must be one of {sorted(VALID_FIELDS)}. Got '{field}'."
            )

    def _validate_condition_operator(self, cond: dict, index: int) -> None:
        """Validate the operator of a condition."""
        operator = cond.get("operator")
        if not operator or not isinstance(operator, str) or operator not in VALID_OPERATORS:
            self.errors.append(
                f"Condition {index}: operator must be one of {sorted(VALID_OPERATORS)}. Got '{operator}'."
            )

    def _validate_condition_value(self, cond: dict, index: int) -> None:
        """Validate the value of a condition."""
        operator = cond.get("operator")
        value = cond.get("value")

        if operator in VALUE_OPERATORS:
            if value is None or (isinstance(value, str) and value.strip() == ""):
                self.errors.append(
                    f"Condition {index}: value is required for operator '{operator}'."
                )

    def _validate_actions(self, rule_dict: dict) -> None:
        """Validate the actions field."""
        actions = rule_dict.get("actions")

        if actions is None:
            self.errors.append("Actions are required.")
            return

        if not isinstance(actions, list):
            self.errors.append("Actions must be a list.")
            return

        # Allow empty actions list
        if len(actions) == 0:
            return

        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                self.errors.append(f"Action {i} must be a dictionary.")
                continue

            action_type = action.get("type")
            if not action_type or not isinstance(action_type, str) or action_type not in VALID_ACTION_TYPES:
                self.errors.append(
                    f"Action {i}: type must be one of {sorted(VALID_ACTION_TYPES)}. Got '{action_type}'."
                )

            # Only require target for certain action types
            if action_type in ("tag", "route", "notify"):
                target = action.get("target") or action.get("value")
                if not target or not isinstance(target, str) or not target.strip():
                    self.errors.append(
                        f"Action {i}: target is required for action type '{action_type}'."
                    )

    def _validate_priority(self, rule_dict: dict) -> None:
        """Validate the priority field."""
        priority = rule_dict.get("priority")
        if priority is not None:
            if not isinstance(priority, int) or isinstance(priority, bool):
                self.errors.append("Priority must be an integer between 0 and 100.")
            elif priority < 0 or priority > 100:
                self.errors.append("Priority must be an integer between 0 and 100.")
