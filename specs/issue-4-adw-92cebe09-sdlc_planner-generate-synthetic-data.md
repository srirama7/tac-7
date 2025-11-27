# Feature: Synthetic Data Generation

## Feature Description
This feature implements LLM-powered synthetic data generation for existing database tables. Users can click a "Generate Data" button next to any table in the Available Tables section to automatically generate 10 new synthetic rows that match the patterns, constraints, and characteristics of existing data. The LLM analyzes sampled rows and table schema to understand data types, value ranges, relationships between columns, and common patterns like emails, phone numbers, and addresses, then generates realistic synthetic data that maintains consistency with the existing dataset.

## User Story
As a developer or data analyst
I want to quickly generate synthetic data rows that match my existing table patterns
So that I can expand my datasets for testing and development without manually creating data

## Problem Statement
Users currently need to manually create or find additional test data when they want to expand their datasets for development and testing purposes. This is time-consuming and error-prone, as manually created data may not match the patterns, formats, and relationships present in the existing data. There is no automated way to generate realistic synthetic data that respects the schema and patterns of existing tables.

## Solution Statement
Implement an LLM-based data generation system that analyzes existing table data and schema to generate synthetic rows. The solution adds a "Generate Data" button next to each table's CSV export button in the Available Tables section. When clicked, the system samples 10 random existing rows, sends them along with the table schema to an LLM with a specialized prompt, and generates 10 new synthetic rows that match the data patterns. The generated rows are then inserted into the table using proper SQL validation and security constraints, and the user receives immediate feedback via a success notification.

## Relevant Files
Use these files to implement the feature:

- `app/server/server.py` - Main FastAPI server with API endpoint definitions. This is where we'll add the new `/api/generate-data` POST endpoint that handles the synthetic data generation request.

- `app/server/core/llm_processor.py` - Contains LLM interaction functions for OpenAI and Anthropic. We'll add new functions `generate_synthetic_data_with_openai()` and `generate_synthetic_data_with_anthropic()` that send the schema and sample data to the LLM with a specialized prompt for data generation.

- `app/server/core/sql_processor.py` - Handles safe SQL query execution. We'll add logic to sample random rows from a table and insert generated rows using the existing safe execution patterns.

- `app/server/core/sql_security.py` - Provides SQL injection protection and safe query execution. We'll use the existing `execute_query_safely()`, `validate_identifier()`, and `check_table_exists()` functions to ensure all SQL operations are secure.

- `app/server/core/data_models.py` - Pydantic models for request/response validation. We'll add `GenerateDataRequest` (containing table_name) and `GenerateDataResponse` (containing rows_generated, table_name, error) models.

- `app/client/src/main.ts` - Main frontend TypeScript file with UI initialization and event handlers. We'll add the "Generate Data" button to the table display function and implement the click handler with loading state.

- `app/client/src/api/client.ts` - API client methods for backend communication. We'll add a `generateSyntheticData(tableName: string)` method that calls the new backend endpoint.

- `app/client/src/types.d.ts` - TypeScript type definitions matching backend models. We'll add `GenerateDataRequest` and `GenerateDataResponse` interfaces.

- `app/client/src/style.css` - Application styling. We'll add styling for the "Generate Data" button to match the existing UI design patterns.

### New Files

- `app/server/core/data_generator.py` - New module containing the core synthetic data generation logic. This will include functions to sample rows, format prompts for the LLM, parse LLM responses, and validate generated data against the schema.

- `app/server/tests/test_data_generator.py` - Unit tests for the data generation functionality, testing sampling logic, LLM prompt formatting, response parsing, and data validation.

- `.claude/commands/e2e/test_synthetic_data_generation.md` - E2E test file that validates the complete synthetic data generation workflow from button click to successful data insertion and UI feedback.

## Implementation Plan

### Phase 1: Foundation
First, establish the core data generation infrastructure on the backend. Create the new `data_generator.py` module with functions to sample random rows from a table, format the schema and sample data for LLM consumption, and parse/validate LLM responses. Add the necessary Pydantic models for request/response handling. This phase focuses on building the reusable components that will power the feature without touching the API or UI yet.

### Phase 2: Core Implementation
Implement the LLM integration for synthetic data generation by adding specialized functions to `llm_processor.py` that send properly formatted prompts to OpenAI and Anthropic. The prompts must instruct the LLM to analyze data patterns (types, ranges, formats, relationships, null handling) and return valid JSON arrays of new row objects. Add the `/api/generate-data` endpoint to the FastAPI server that orchestrates the entire flow: validate table name, sample existing rows, call LLM, parse response, insert new rows, and return success/error status. Implement proper error handling and logging throughout.

### Phase 3: Integration
Build the frontend components to expose this functionality to users. Add the "Generate Data" button to each table in the Available Tables section, positioned to the left of the CSV export button. Implement the click handler with proper loading states (disable button, show loading indicator), call the backend API, and display success notifications showing how many rows were added. Add the corresponding API client method and TypeScript types. Create comprehensive E2E tests that validate the entire user workflow. Integrate with existing testing infrastructure and ensure all validation commands pass.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Backend Data Models
- Add `GenerateDataRequest` model to `app/server/core/data_models.py` with `table_name` field
- Add `GenerateDataResponse` model with `rows_generated`, `table_name`, and optional `error` fields
- Ensure models follow existing Pydantic patterns with proper Field descriptions and validation

### Step 2: Create Core Data Generator Module
- Create new file `app/server/core/data_generator.py`
- Implement `sample_random_rows(conn, table_name, sample_size=10)` function that:
  - Validates table name using `validate_identifier()`
  - Checks table exists using `check_table_exists()`
  - Executes safe SELECT query with RANDOM() ORDER BY and LIMIT to get sample rows
  - Returns list of row dictionaries
- Implement `format_data_generation_prompt(table_name, schema, sample_rows)` function that:
  - Formats table schema with column names and types
  - Includes sample row data
  - Returns formatted prompt string for LLM
- Implement `parse_generated_data(llm_response, schema)` function that:
  - Parses JSON array from LLM response
  - Validates each row has correct columns matching schema
  - Handles basic type validation (strings, numbers, nulls)
  - Returns validated list of row dictionaries or raises exception
- Implement `insert_generated_rows(conn, table_name, rows, schema)` function that:
  - Builds parameterized INSERT statements for each row
  - Uses `execute_query_safely()` with proper value parameters
  - Returns count of successfully inserted rows
  - Handles insertion errors gracefully

### Step 3: Implement LLM Integration for Data Generation
- Add `generate_synthetic_data_with_openai(table_name, schema, sample_rows)` to `app/server/core/llm_processor.py`:
  - Use `format_data_generation_prompt()` to build prompt
  - Send to OpenAI API with instructions to analyze patterns and generate 10 new rows
  - Specify data analysis requirements: data types, value ranges, distributions, column relationships, common patterns (emails, phones, addresses), nullable vs required fields
  - Request JSON array format response with exact column names matching schema
  - Set temperature to 0.7 for creative but consistent generation
  - Parse and return generated data
- Add `generate_synthetic_data_with_anthropic(table_name, schema, sample_rows)`:
  - Implement same logic using Anthropic API
  - Use consistent prompt format and response parsing
- Add routing function `generate_synthetic_data(table_name, schema, sample_rows)` that prioritizes OpenAI then Anthropic based on available API keys

### Step 4: Create API Endpoint
- Add POST endpoint `/api/generate-data` to `app/server/server.py`:
  - Accept `GenerateDataRequest` with table_name
  - Validate table_name using sql_security module
  - Connect to database
  - Call `sample_random_rows()` to get 10 existing rows
  - Get table schema from existing `get_database_schema()` function
  - Call `generate_synthetic_data()` from llm_processor
  - Call `parse_generated_data()` to validate LLM output
  - Call `insert_generated_rows()` to insert into database
  - Commit transaction
  - Return `GenerateDataResponse` with success status and row count
  - Include comprehensive error handling with logging
  - Return errors in response.error field without raising HTTP exceptions for user-friendly messages

### Step 5: Write Backend Unit Tests
- Create `app/server/tests/test_data_generator.py`:
  - Test `sample_random_rows()` with valid table
  - Test `sample_random_rows()` with invalid table name (should raise error)
  - Test `format_data_generation_prompt()` produces expected format
  - Test `parse_generated_data()` with valid JSON response
  - Test `parse_generated_data()` with invalid JSON (should raise error)
  - Test `parse_generated_data()` with missing columns (should raise error)
  - Test `insert_generated_rows()` successfully inserts data
  - Mock database connections and LLM calls appropriately
- Run tests: `cd app/server && uv run pytest tests/test_data_generator.py -v`

### Step 6: Add Frontend TypeScript Types
- Add interfaces to `app/client/src/types.d.ts`:
  - `GenerateDataRequest` with `table_name: string`
  - `GenerateDataResponse` with `rows_generated: number`, `table_name: string`, `error?: string`

### Step 7: Add Frontend API Client Method
- Add `generateSyntheticData(tableName: string)` to `app/client/src/api/client.ts`:
  - Call POST `/api/generate-data` with JSON body containing table_name
  - Return Promise<GenerateDataResponse>
  - Use existing error handling patterns
  - Follow existing API method conventions

### Step 8: Add Generate Data Button to UI
- Modify `displayTables()` function in `app/client/src/main.ts`:
  - Find the section where export button is created (around line 337-348)
  - Create new "Generate Data" button before the export button
  - Add button with class `generate-data-button` and appropriate icon (e.g., "🎲 Generate")
  - Position button to the left of CSV export button using existing flex layout
  - Add title tooltip: "Generate 10 synthetic data rows"
  - Implement onclick handler that:
    - Disables the button immediately
    - Shows loading state with spinner
    - Calls `api.generateSyntheticData(table.name)`
    - On success: shows success notification with "Added X rows to table_name"
    - On error: calls `displayError()` with error message
    - Re-enables button and removes loading state
    - Calls `loadDatabaseSchema()` to refresh table row counts
  - Ensure button styling matches existing UI patterns

### Step 9: Add CSS Styling for Generate Button
- Add styles to `app/client/src/style.css`:
  - Style `.generate-data-button` to match existing button styles
  - Ensure it visually fits between table name and export button
  - Add hover states and loading states consistent with other buttons
  - Use existing CSS variables for colors and spacing

### Step 10: Create E2E Test File
- Create `.claude/commands/e2e/test_synthetic_data_generation.md`:
  - Define User Story for synthetic data generation
  - Define Test Steps:
    1. Navigate to application
    2. Verify initial UI state
    3. Upload sample CSV file to create a table
    4. Verify table appears with initial row count
    5. Take screenshot of table with Generate Data button visible
    6. Click Generate Data button
    7. Verify button shows loading state
    8. Wait for generation to complete (allow sufficient time for LLM call)
    9. Verify success notification appears showing rows added
    10. Verify table row count increased by 10
    11. Take screenshot of success notification
    12. Query the table to verify new rows exist
    13. Verify generated data matches schema and patterns
    14. Take screenshot of generated data in query results
  - Define Success Criteria:
    - Generate Data button appears and is clickable
    - Loading state displays during generation
    - Success notification shows correct count
    - Table row count increases by exactly 10
    - Generated data is valid and matches schema
    - No errors occur during process
    - 3 screenshots captured

### Step 11: Manual Integration Testing
- Start the application using `./scripts/start.sh`
- Upload a sample CSV file (e.g., users.csv)
- Verify Generate Data button appears to the left of CSV export button
- Click Generate Data button
- Verify loading state appears
- Wait for completion and verify success notification
- Verify table row count increased by 10
- Query the table to inspect generated data
- Verify data quality: correct types, realistic values, proper relationships
- Test with different table types (different schemas, data types)
- Test error cases: invalid table, LLM API errors
- Verify all UI states and error messages are user-friendly

### Step 12: Run All Validation Commands
- Execute all validation commands to ensure zero regressions
- Read `.claude/commands/test_e2e.md` and execute the new E2E test file `.claude/commands/e2e/test_synthetic_data_generation.md`
- Run `cd app/server && uv run pytest` - Ensure all backend tests pass including new data generator tests
- Run `cd app/client && bun tsc --noEmit` - Ensure no TypeScript errors
- Run `cd app/client && bun run build` - Ensure frontend builds successfully
- Address any failures immediately before considering feature complete

## Testing Strategy

### Unit Tests
- `test_sample_random_rows_valid_table()` - Verify sampling returns expected number of rows from valid table
- `test_sample_random_rows_invalid_table()` - Verify error handling for non-existent table
- `test_sample_random_rows_security()` - Verify SQL injection protection in table name
- `test_format_data_generation_prompt()` - Verify prompt formatting includes schema and samples
- `test_parse_generated_data_valid_json()` - Verify parsing of valid LLM response
- `test_parse_generated_data_invalid_json()` - Verify error handling for malformed JSON
- `test_parse_generated_data_missing_columns()` - Verify error when columns don't match schema
- `test_parse_generated_data_type_mismatch()` - Verify handling of type inconsistencies
- `test_insert_generated_rows_success()` - Verify successful insertion with correct row count
- `test_insert_generated_rows_duplicate_handling()` - Verify handling of potential constraint violations
- `test_api_endpoint_success_flow()` - Integration test for complete happy path
- `test_api_endpoint_no_existing_data()` - Test behavior when table has less than 10 rows
- `test_api_endpoint_llm_error()` - Test error handling when LLM call fails

### Edge Cases
- **Empty tables** - Table exists but has 0 rows: Should return error message "Table must have at least 1 row to generate synthetic data"
- **Tables with less than 10 rows** - Sample all available rows and still generate 10 new rows
- **Complex data types** - Tables with JSON, dates, timestamps: LLM should infer and maintain correct formats
- **Nullable columns** - Generated data should respect NULL distribution from sample data
- **Unique constraints** - Generated data might violate constraints: Handle with graceful error messaging
- **Very large tables** - Sampling should use RANDOM() efficiently without scanning entire table
- **LLM API failures** - Network errors, rate limits, timeouts: Return user-friendly error messages
- **Invalid LLM responses** - Non-JSON or incorrect format: Parse errors should be caught and reported clearly
- **Concurrent generation requests** - Multiple users generating data simultaneously: Database transactions should handle correctly
- **Special characters in data** - Data with quotes, newlines, unicode: Should be properly escaped and inserted

## Acceptance Criteria
- Generate Data button appears to the left of CSV export button for every table in Available Tables section
- Clicking Generate Data button triggers LLM-based synthetic data generation
- Button shows loading state (disabled with spinner) during generation
- System samples up to 10 random existing rows from the table
- System sends table schema and sampled data to LLM with specialized prompt
- LLM analyzes data patterns including types, ranges, distributions, relationships, formats, and null handling
- LLM returns 10 new synthetic rows in valid JSON format matching table schema
- System validates and inserts generated rows using SQL security constraints
- Success notification displays showing "Added 10 rows to [table_name]"
- Table row count updates immediately to reflect new data
- Generated data quality matches existing patterns (realistic emails, phone numbers, dates, etc.)
- All SQL operations use existing security validation (no SQL injection vulnerabilities)
- Feature works with both OpenAI and Anthropic LLM providers
- Error messages are user-friendly and actionable
- Loading states provide clear feedback to users
- All existing tests continue to pass (zero regressions)
- New E2E test validates complete user workflow
- Backend unit tests achieve >80% code coverage for new modules

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

Read `.claude/commands/test_e2e.md`, then read and execute your new E2E `.claude/commands/e2e/test_synthetic_data_generation.md` test file to validate this functionality works.

- `cd app/server && uv run pytest` - Run server tests to validate the feature works with zero regressions
- `cd app/client && bun tsc --noEmit` - Run frontend tests to validate the feature works with zero regressions
- `cd app/client && bun run build` - Run frontend build to validate the feature works with zero regressions

## Notes

### LLM Prompt Engineering
The prompt sent to the LLM should:
- Clearly specify the output format (JSON array of objects)
- Include exact column names and types from schema
- Provide sample rows to demonstrate patterns
- Instruct to analyze: data types, value ranges, distributions, relationships, common formats (emails, phones, addresses), nullable fields
- Request realistic and diverse data while maintaining consistency
- Specify to return exactly 10 rows
- Emphasize matching the sample data patterns closely

### Security Considerations
- All table name inputs must be validated using `validate_identifier()`
- All SQL queries must use `execute_query_safely()` with parameterized queries
- Never concatenate user input into SQL strings
- LLM responses must be validated before insertion to prevent malicious data injection
- Use existing SQL security patterns from `core/sql_security.py`

### Performance Considerations
- Sampling uses `ORDER BY RANDOM() LIMIT 10` which is efficient for SQLite
- LLM API calls may take 2-10 seconds - UI must show clear loading states
- Consider adding timeout handling for LLM calls (30 second max)
- Database insertions use transactions for atomicity
- No need to optimize for very large tables in v1 (SQLite handles efficiently)

### Future Enhancements (Not in Scope)
- Allow users to specify number of rows to generate (currently fixed at 10)
- Add option to preview generated data before inserting
- Support for generating data with referential integrity across multiple tables
- Ability to specify custom constraints or patterns for generation
- Batch generation for very large synthetic datasets
- Export generated data separately without inserting into table
- Progress indicator for long-running generations
