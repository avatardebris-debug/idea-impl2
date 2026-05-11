# Phase 2 Tasks

- [ ] Task 1: RuleForm validation layer
  - What: Build a RuleForm class that validates rule data from user input before saving. Validates required fields (name, conditions, actions), checks that conditions have valid field/operator combinations, ensures values are present for operators that require them (contains, not_contains, equals, regex), validates action types (tag, route, archive, flag), and validates priority is an integer between 0 and 100. Returns a list of error messages (empty list = valid).
  - Files: Create `rule_builder_ui/validation.py`
  - Done when: RuleForm.validate(rule_dict) correctly accepts valid rules, rejects rules with missing name, empty conditions list, invalid operators, missing values for value-requiring operators, invalid action types, and out-of-range priorities. Unit tests cover all validation paths.

- [ ] Task 2: Flask API endpoints
  - What: Build a Flask application (`app.py`) with CRUD API endpoints: GET /rules (returns all rules as JSON), POST /rules (creates a new rule, validates via RuleForm, saves via RuleStore), PUT /rules/<id> (updates an existing rule, validates, saves), DELETE /rules/<id> (removes a rule from store). The app uses RuleStore for persistence and RuleForm for validation. Includes error handling for not-found rules, invalid JSON, and validation failures with appropriate HTTP status codes (400, 404, 500).
  - Files: Create `rule_builder_ui/app.py` and `rule_builder_ui/__init__.py`
  - Done when: All four CRUD endpoints work correctly. POST returns 201 with the created rule. PUT returns 200 with updated rule. DELETE returns 204. GET returns 200 with rule list. Validation errors return 400 with error details. Not-found returns 404. The app can be started with `python -m rule_builder_ui.app`.

- [ ] Task 3: Visual frontend UI
  - What: Build the visual rule builder frontend with: (a) Rule list sidebar showing all rules with name, priority, enabled toggle, and a "duplicate" button per rule. (b) Rule editor panel with rule name input, dynamic condition builder (add/remove conditions with dropdowns for field, operator, value input), dynamic action builder (add/remove actions with type selector dropdown and target input), priority slider (0-100), and enable/disable toggle. (c) Import/export JSON buttons that call the API endpoints. (d) Client-side validation feedback. Uses vanilla JS with fetch API to communicate with the Flask backend.
  - Files: Create `rule_builder_ui/templates/index.html`, `rule_builder_ui/static/css/style.css`, `rule_builder_ui/static/js/app.js`
  - Done when: User can create a new rule via the UI and see it appear in the sidebar. User can edit an existing rule and changes persist to the store. User can delete a rule and it disappears from the sidebar. User can toggle enabled/disabled. User can add/remove conditions and actions dynamically. Import/export JSON works correctly. Duplicate rule creates a copy with a new ID. Validation errors display inline.

- [ ] Task 4: Integration tests for full CRUD lifecycle
  - What: Write integration tests that exercise the full CRUD lifecycle of rules through the Flask test client. Tests cover: creating rules via POST, reading rules via GET, updating rules via PUT, deleting rules via DELETE, validation error responses, import/export round-trip, and duplicate rule creation. Tests verify data consistency between the API and the underlying RuleStore.
  - Files: Create `rule_builder_ui/tests/test_api.py` and `rule_builder_ui/tests/__init__.py`
  - Done when: All integration tests pass. Tests cover: CRUD operations, validation errors (missing name, invalid operator, missing value), not-found errors, import/export round-trip producing identical rule sets, duplicate rule creating a new rule with different ID, and enabled/disabled toggle. Minimum 15 test cases.

- [ ] Task 5: Module packaging and entry point
  - What: Ensure the `rule_builder_ui` module is properly packaged with `__init__.py` exposing key classes (RuleBuilderPanel, RuleForm). Add a `__main__.py` entry point so the app can be run with `python -m rule_builder_ui`. Add a requirements file for dependencies (flask). Ensure the module can be imported and the app can be started without errors.
  - Files: Update `rule_builder_ui/__init__.py`, create `rule_builder_ui/__main__.py`, create `rule_builder_ui/requirements.txt`
  - Done when: `python -m rule_builder_ui` starts the Flask app successfully. `from rule_builder_ui import RuleForm` works. All imports are clean. Dependencies are listed in requirements.txt.