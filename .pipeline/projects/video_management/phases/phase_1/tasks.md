# Phase 1 Tasks

- [ ] Task 1: Database models and field type system
  - What: Define SQLAlchemy models for the videos table with extensible custom fields using JSONB storage. Implement a field type enum (text, date, select, checkbox, number, URL, tags) with validation logic. Create the table metadata model to track which custom fields exist.
  - Files: workspace/backend/app/models.py, workspace/backend/app/schemas.py
  - Done when: Models define Video, TableField, and TableMetadata entities; FieldTypeId enum covers all 7 types; field values are validated against their type constraints (e.g., URL type rejects non-URL strings, date type rejects non-date strings)

- [ ] Task 2: CRUD API endpoints for video records
  - What: Build FastAPI routes for full CRUD on video records: GET /api/videos (list with pagination), GET /api/videos/{id}, POST /api/videos, PUT /api/videos/{id}, DELETE /api/videos/{id}. Include input validation via Pydantic schemas and proper error handling (404, 400, 422).
  - Files: workspace/backend/app/routers/videos.py, workspace/backend/app/main.py, workspace/backend/app/database.py
  - Done when: All 5 CRUD endpoints return correct HTTP status codes; POST/PUT validate field types; GET list supports pagination params (page, page_size); DELETE returns 204; all endpoints have error handling for missing records and invalid input

- [ ] Task 3: Custom field management API
  - What: Build API endpoints for managing custom fields on the videos table: POST /api/tables/{table_id}/fields (add field), GET /api/tables/{table_id}/fields (list fields), DELETE /api/tables/{table_id}/fields/{field_id} (remove field). When a field is added, it becomes visible in the grid. When removed, the data is preserved but the column is hidden.
  - Files: workspace/backend/app/routers/fields.py, workspace/backend/app/services/table_service.py
  - Done when: Adding a field creates it in the database and returns the field definition; listing fields returns all built-in and custom fields with their types; removing a field marks it as deleted without data loss; field creation validates type and name uniqueness

- [ ] Task 4: Grid UI with inline editing, filtering, and sorting
  - What: Build the React frontend grid component that displays video records as a spreadsheet-like table. Features: inline cell editing (double-click to edit), column headers with drag-to-resize, multi-field filter bar (filter by any field with operator selection), column sorting (click header to sort asc/desc), and virtualized rendering for 100+ rows without lag.
  - Files: workspace/frontend/src/components/ContentGrid.tsx, workspace/frontend/src/components/FilterBar.tsx, workspace/frontend/src/components/CellEditor.tsx, workspace/frontend/src/api/videos.ts, workspace/frontend/src/hooks/useVideos.ts
  - Done when: Grid renders 100+ rows smoothly (no layout thrashing); inline editing updates the record via API; filter bar applies multi-field filters with AND logic; clicking column header sorts ascending, clicking again sorts descending; all UI state syncs with backend data

- [ ] Task 5: Sample data seeding and integration tests
  - What: Create a seed script that populates the database with 50+ sample video records across various statuses, tags, and dates. Write backend integration tests covering CRUD operations, field type validation, and custom field management.
  - Files: workspace/backend/scripts/seed.py, workspace/backend/tests/test_videos.py, workspace/backend/tests/test_fields.py
  - Done when: Seed script creates 50+ videos with realistic data (titles, descriptions, statuses like draft/scheduled/published, tags, dates); backend tests cover all CRUD paths, field validation, and custom field CRUD; all tests pass with SQLite in-memory database