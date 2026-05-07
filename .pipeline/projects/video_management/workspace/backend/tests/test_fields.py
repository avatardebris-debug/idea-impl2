"""Tests for custom field management API."""

import pytest
from app.models import FieldTypeId


class TestFieldEndpoints:
    """Tests for field CRUD endpoints."""

    def test_list_fields(self, sample_table, test_client):
        """Test listing fields for a table."""
        response = test_client.get(f"/api/tables/{sample_table}/fields")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 11  # Built-in fields
        field_names = [f["name"] for f in data["items"]]
        assert "title" in field_names
        assert "description" in field_names

    def test_get_field(self, sample_table, test_client):
        """Test getting a specific field."""
        # Get the list first to find a field ID
        list_response = test_client.get(f"/api/tables/{sample_table}/fields")
        field_id = list_response.json()["items"][0]["id"]

        response = test_client.get(f"/api/tables/{sample_table}/fields/{field_id}")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "field_type" in data

    def test_get_nonexistent_field(self, sample_table, test_client):
        """Test getting a field that doesn't exist."""
        response = test_client.get(f"/api/tables/{sample_table}/fields/nonexistent-id")
        assert response.status_code == 404

    def test_create_field(self, sample_table, test_client):
        """Test creating a custom field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Custom Field",
                "field_type": "text",
                "is_required": False,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Custom Field"
        assert data["field_type"] == "text"
        assert data["is_required"] is False
        assert "id" in data

    def test_create_field_duplicate_name(self, sample_table, test_client):
        """Test that duplicate field names are rejected."""
        # Create first field
        test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={"name": "Duplicate Field", "field_type": "text"},
        )
        # Try to create another with same name
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={"name": "Duplicate Field", "field_type": "text"},
        )
        assert response.status_code == 409

    def test_update_field(self, sample_table, test_client):
        """Test updating a field."""
        # Create a field first
        create_response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={"name": "Original Field", "field_type": "text"},
        )
        field_id = create_response.json()["id"]

        # Update the field
        response = test_client.put(
            f"/api/tables/{sample_table}/fields/{field_id}",
            json={"name": "Updated Field", "is_required": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Field"
        assert data["is_required"] is True

    def test_delete_field(self, sample_table, test_client):
        """Test deleting a field."""
        # Create a field first
        create_response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={"name": "Delete Me Field", "field_type": "text"},
        )
        field_id = create_response.json()["id"]

        # Delete the field
        response = test_client.delete(f"/api/tables/{sample_table}/fields/{field_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = test_client.get(f"/api/tables/{sample_table}/fields/{field_id}")
        assert get_response.status_code == 404

    def test_create_field_with_options(self, sample_table, test_client):
        """Test creating a field with options (for select type)."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Priority Field",
                "field_type": "select",
                "options": ["Low", "Medium", "High"],
                "default_option": "Medium",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "select"
        assert data["options"] == ["Low", "Medium", "High"]
        assert data["default_option"] == "Medium"

    def test_create_field_with_validation(self, sample_table, test_client):
        """Test creating a field with validation rules."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Email Field",
                "field_type": "text",
                "validation": {
                    "pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$",
                    "message": "Invalid email format",
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["validation"]["pattern"] == "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"

    def test_create_field_with_default_value(self, sample_table, test_client):
        """Test creating a field with a default value."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Status Field",
                "field_type": "text",
                "default_value": "active",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["default_value"] == "active"

    def test_list_fields_pagination(self, sample_table, test_client):
        """Test listing fields with pagination."""
        # Create several fields
        for i in range(5):
            test_client.post(
                f"/api/tables/{sample_table}/fields",
                json={"name": f"Field {i}", "field_type": "text"},
            )

        # List fields with pagination
        response = test_client.get(f"/api/tables/{sample_table}/fields?page=1&page_size=3")
        data = response.json()
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert data["total"] >= 5

    def test_create_field_invalid_type(self, sample_table, test_client):
        """Test that invalid field types are rejected."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={"name": "Invalid Field", "field_type": "invalid_type"},
        )
        assert response.status_code == 422

    def test_create_field_missing_name(self, sample_table, test_client):
        """Test that missing field name is rejected."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={"field_type": "text"},
        )
        assert response.status_code == 422

    def test_create_field_with_tags_type(self, sample_table, test_client):
        """Test creating a tags field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Tags Field",
                "field_type": "tags",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "tags"

    def test_create_field_with_url_type(self, sample_table, test_client):
        """Test creating a URL field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "URL Field",
                "field_type": "url",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "url"

    def test_create_field_with_date_type(self, sample_table, test_client):
        """Test creating a date field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Date Field",
                "field_type": "date",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "date"

    def test_create_field_with_number_type(self, sample_table, test_client):
        """Test creating a number field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Number Field",
                "field_type": "number",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "number"

    def test_create_field_with_boolean_type(self, sample_table, test_client):
        """Test creating a boolean field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Boolean Field",
                "field_type": "boolean",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "boolean"

    def test_create_field_with_json_type(self, sample_table, test_client):
        """Test creating a JSON field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "JSON Field",
                "field_type": "json",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "json"

    def test_create_field_with_image_type(self, sample_table, test_client):
        """Test creating an image field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Image Field",
                "field_type": "image",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "image"

    def test_create_field_with_file_type(self, sample_table, test_client):
        """Test creating a file field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "File Field",
                "field_type": "file",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "file"

    def test_create_field_with_email_type(self, sample_table, test_client):
        """Test creating an email field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Email Field",
                "field_type": "email",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "email"

    def test_create_field_with_phone_type(self, sample_table, test_client):
        """Test creating a phone field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Phone Field",
                "field_type": "phone",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "phone"

    def test_create_field_with_address_type(self, sample_table, test_client):
        """Test creating an address field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Address Field",
                "field_type": "address",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "address"

    def test_create_field_with_coordinate_type(self, sample_table, test_client):
        """Test creating a coordinate field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Coordinate Field",
                "field_type": "coordinate",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "coordinate"

    def test_create_field_with_rating_type(self, sample_table, test_client):
        """Test creating a rating field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Rating Field",
                "field_type": "rating",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "rating"

    def test_create_field_with_color_type(self, sample_table, test_client):
        """Test creating a color field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Color Field",
                "field_type": "color",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "color"

    def test_create_field_with_link_type(self, sample_table, test_client):
        """Test creating a link field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Link Field",
                "field_type": "link",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "link"

    def test_create_field_with_money_type(self, sample_table, test_client):
        """Test creating a money field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Money Field",
                "field_type": "money",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "money"

    def test_create_field_with_percentage_type(self, sample_table, test_client):
        """Test creating a percentage field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Percentage Field",
                "field_type": "percentage",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "percentage"

    def test_create_field_with_duration_type(self, sample_table, test_client):
        """Test creating a duration field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Duration Field",
                "field_type": "duration",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "duration"

    def test_create_field_with_time_type(self, sample_table, test_client):
        """Test creating a time field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Time Field",
                "field_type": "time",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "time"

    def test_create_field_with_datetime_type(self, sample_table, test_client):
        """Test creating a datetime field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Datetime Field",
                "field_type": "datetime",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "datetime"

    def test_create_field_with_uuid_type(self, sample_table, test_client):
        """Test creating a UUID field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "UUID Field",
                "field_type": "uuid",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "uuid"

    def test_create_field_with_password_type(self, sample_table, test_client):
        """Test creating a password field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Password Field",
                "field_type": "password",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "password"

    def test_create_field_with_checkbox_type(self, sample_table, test_client):
        """Test creating a checkbox field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Checkbox Field",
                "field_type": "checkbox",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "checkbox"

    def test_create_field_with_radio_type(self, sample_table, test_client):
        """Test creating a radio field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Radio Field",
                "field_type": "radio",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "radio"

    def test_create_field_with_dropdown_type(self, sample_table, test_client):
        """Test creating a dropdown field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Dropdown Field",
                "field_type": "dropdown",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "dropdown"

    def test_create_field_with_multiselect_type(self, sample_table, test_client):
        """Test creating a multiselect field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Multiselect Field",
                "field_type": "multiselect",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "multiselect"

    def test_create_field_with_autocomplete_type(self, sample_table, test_client):
        """Test creating an autocomplete field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"

    def test_create_field_with_autocomplete_with_options(self, sample_table, test_client):
        """Test creating an autocomplete field with options."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "options": ["Option 1", "Option 2", "Option 3"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["options"] == ["Option 1", "Option 2", "Option 3"]

    def test_create_field_with_autocomplete_with_validation(self, sample_table, test_client):
        """Test creating an autocomplete field with validation."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "validation": {
                    "min_length": 3,
                    "max_length": 50,
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["validation"]["min_length"] == 3
        assert data["validation"]["max_length"] == 50

    def test_create_field_with_autocomplete_with_default(self, sample_table, test_client):
        """Test creating an autocomplete field with default."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "default_value": "Default Option",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["default_value"] == "Default Option"

    def test_create_field_with_autocomplete_with_required(self, sample_table, test_client):
        """Test creating an autocomplete field with required."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "is_required": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["is_required"] is True

    def test_create_field_with_autocomplete_with_help_text(self, sample_table, test_client):
        """Test creating an autocomplete field with help text."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "help_text": "Enter a valid option",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["help_text"] == "Enter a valid option"

    def test_create_field_with_autocomplete_with_placeholder(self, sample_table, test_client):
        """Test creating an autocomplete field with placeholder."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "placeholder": "Search...",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["placeholder"] == "Search..."

    def test_create_field_with_autocomplete_with_max_length(self, sample_table, test_client):
        """Test creating an autocomplete field with max length."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "max_length": 100,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["max_length"] == 100

    def test_create_field_with_autocomplete_with_min_length(self, sample_table, test_client):
        """Test creating an autocomplete field with min length."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "min_length": 1,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["min_length"] == 1

    def test_create_field_with_autocomplete_with_pattern(self, sample_table, test_client):
        """Test creating an autocomplete field with pattern."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "pattern": "^[a-zA-Z]+$",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["pattern"] == "^[a-zA-Z]+$"

    def test_create_field_with_autocomplete_with_message(self, sample_table, test_client):
        """Test creating an autocomplete field with message."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "message": "Please enter a valid option",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["message"] == "Please enter a valid option"

    def test_create_field_with_autocomplete_with_options_and_validation(self, sample_table, test_client):
        """Test creating an autocomplete field with options and validation."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "options": ["Option 1", "Option 2"],
                "validation": {
                    "min_length": 1,
                    "max_length": 50,
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["options"] == ["Option 1", "Option 2"]
        assert data["validation"]["min_length"] == 1
        assert data["validation"]["max_length"] == 50

    def test_create_field_with_autocomplete_with_options_and_default(self, sample_table, test_client):
        """Test creating an autocomplete field with options and default."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "options": ["Option 1", "Option 2"],
                "default_value": "Option 1",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["options"] == ["Option 1", "Option 2"]
        assert data["default_value"] == "Option 1"

    def test_create_field_with_autocomplete_with_options_and_required(self, sample_table, test_client):
        """Test creating an autocomplete field with options and required."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "options": ["Option 1", "Option 2"],
                "is_required": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["options"] == ["Option 1", "Option 2"]
        assert data["is_required"] is True

    def test_create_field_with_autocomplete_with_options_and_help_text(self, sample_table, test_client):
        """Test creating an autocomplete field with options and help text."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "options": ["Option 1", "Option 2"],
                "help_text": "Select an option",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["options"] == ["Option 1", "Option 2"]
        assert data["help_text"] == "Select an option"

    def test_create_field_with_autocomplete_with_options_and_placeholder(self, sample_table, test_client):
        """Test creating an autocomplete field with options and placeholder."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "options": ["Option 1", "Option 2"],
                "placeholder": "Choose...",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["options"] == ["Option 1", "Option 2"]
        assert data["placeholder"] == "Choose..."

    def test_create_field_with_autocomplete_with_options_and_max_length(self, sample_table, test_client):
        """Test creating an autocomplete field with options and max length."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "options": ["Option 1", "Option 2"],
                "max_length": 100,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["options"] == ["Option 1", "Option 2"]
        assert data["max_length"] == 100

    def test_create_field_with_autocomplete_with_options_and_min_length(self, sample_table, test_client):
        """Test creating an autocomplete field with options and min length."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "options": ["Option 1", "Option 2"],
                "min_length": 1,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["options"] == ["Option 1", "Option 2"]
        assert data["min_length"] == 1

    def test_create_field_with_autocomplete_with_options_and_pattern(self, sample_table, test_client):
        """Test creating an autocomplete field with options and pattern."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "options": ["Option 1", "Option 2"],
                "pattern": "^[a-zA-Z]+$",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["options"] == ["Option 1", "Option 2"]
        assert data["pattern"] == "^[a-zA-Z]+$"

    def test_create_field_with_autocomplete_with_options_and_message(self, sample_table, test_client):
        """Test creating an autocomplete field with options and message."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "options": ["Option 1", "Option 2"],
                "message": "Please enter a valid option",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["options"] == ["Option 1", "Option 2"]
        assert data["message"] == "Please enter a valid option"

    def test_create_field_with_autocomplete_with_all_options(self, sample_table, test_client):
        """Test creating an autocomplete field with all options."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Autocomplete Field",
                "field_type": "autocomplete",
                "options": ["Option 1", "Option 2"],
                "default_value": "Option 1",
                "is_required": True,
                "help_text": "Select an option",
                "placeholder": "Choose...",
                "max_length": 100,
                "min_length": 1,
                "pattern": "^[a-zA-Z]+$",
                "message": "Please enter a valid option",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "autocomplete"
        assert data["options"] == ["Option 1", "Option 2"]
        assert data["default_value"] == "Option 1"
        assert data["is_required"] is True
        assert data["help_text"] == "Select an option"
        assert data["placeholder"] == "Choose..."
        assert data["max_length"] == 100
        assert data["min_length"] == 1
        assert data["pattern"] == "^[a-zA-Z]+$"
        assert data["message"] == "Please enter a valid option"
