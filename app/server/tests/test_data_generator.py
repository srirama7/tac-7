"""
Unit tests for synthetic data generation functionality.
"""

import pytest
import sqlite3
import json
from unittest.mock import Mock, patch, MagicMock
from core.data_generator import (
    sample_random_rows,
    format_data_generation_prompt,
    parse_generated_data,
    insert_generated_rows,
)
from core.sql_security import SQLSecurityError


@pytest.fixture
def mock_conn():
    """Create a mock database connection for testing."""
    conn = MagicMock(spec=sqlite3.Connection)
    cursor = MagicMock(spec=sqlite3.Cursor)
    conn.cursor.return_value = cursor
    return conn


def test_sample_random_rows_valid_table():
    """Test sampling rows from a valid table."""
    # Create an in-memory database with test data
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create test table
    cursor.execute(
        """
        CREATE TABLE test_users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT
        )
    """
    )

    # Insert test data
    test_data = [
        (1, "Alice", "alice@example.com"),
        (2, "Bob", "bob@example.com"),
        (3, "Charlie", "charlie@example.com"),
    ]
    cursor.executemany("INSERT INTO test_users VALUES (?, ?, ?)", test_data)
    conn.commit()

    # Sample rows
    result = sample_random_rows(conn, "test_users", sample_size=2)

    # Verify results
    assert len(result) == 2
    assert all(isinstance(row, dict) for row in result)
    assert all("id" in row and "name" in row and "email" in row for row in result)

    conn.close()


def test_sample_random_rows_invalid_table():
    """Test sampling from a non-existent table raises error."""
    conn = sqlite3.connect(":memory:")

    with pytest.raises(ValueError, match="does not exist"):
        sample_random_rows(conn, "nonexistent_table")

    conn.close()


def test_sample_random_rows_empty_table():
    """Test sampling from an empty table raises error."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create empty table
    cursor.execute(
        """
        CREATE TABLE empty_table (
            id INTEGER PRIMARY KEY,
            value TEXT
        )
    """
    )
    conn.commit()

    with pytest.raises(ValueError, match="must have at least 1 row"):
        sample_random_rows(conn, "empty_table")

    conn.close()


def test_sample_random_rows_security():
    """Test SQL injection protection in table name."""
    conn = sqlite3.connect(":memory:")

    # Test with malicious table name
    with pytest.raises(SQLSecurityError):
        sample_random_rows(conn, "users; DROP TABLE users--")

    conn.close()


def test_format_data_generation_prompt():
    """Test prompt formatting includes schema and samples."""
    table_name = "users"
    schema = [
        {"name": "id", "type": "INTEGER"},
        {"name": "name", "type": "TEXT"},
        {"name": "email", "type": "TEXT"},
    ]
    sample_rows = [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
    ]

    prompt = format_data_generation_prompt(table_name, schema, sample_rows)

    # Verify prompt contains key elements
    assert "users" in prompt
    assert "id" in prompt
    assert "name" in prompt
    assert "email" in prompt
    assert "INTEGER" in prompt
    assert "TEXT" in prompt
    assert "Alice" in prompt
    assert "alice@example.com" in prompt
    assert "10 new rows" in prompt or "10 new" in prompt


def test_parse_generated_data_valid_json():
    """Test parsing of valid LLM response."""
    schema = [
        {"name": "id", "type": "INTEGER"},
        {"name": "name", "type": "TEXT"},
        {"name": "email", "type": "TEXT"},
    ]

    llm_response = json.dumps(
        [
            {"id": 3, "name": "Dave", "email": "dave@example.com"},
            {"id": 4, "name": "Eve", "email": "eve@example.com"},
        ]
    )

    result = parse_generated_data(llm_response, schema)

    assert len(result) == 2
    assert result[0]["name"] == "Dave"
    assert result[1]["name"] == "Eve"


def test_parse_generated_data_with_markdown():
    """Test parsing when LLM wraps JSON in markdown code blocks."""
    schema = [
        {"name": "id", "type": "INTEGER"},
        {"name": "name", "type": "TEXT"},
    ]

    llm_response = """```json
[
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
]
```"""

    result = parse_generated_data(llm_response, schema)

    assert len(result) == 2
    assert result[0]["name"] == "Alice"


def test_parse_generated_data_invalid_json():
    """Test error handling for malformed JSON."""
    schema = [{"name": "id", "type": "INTEGER"}]

    llm_response = "This is not valid JSON"

    with pytest.raises(ValueError, match="Invalid JSON"):
        parse_generated_data(llm_response, schema)


def test_parse_generated_data_not_array():
    """Test error when response is not a JSON array."""
    schema = [{"name": "id", "type": "INTEGER"}]

    llm_response = json.dumps({"id": 1, "name": "Alice"})

    with pytest.raises(ValueError, match="must be a JSON array"):
        parse_generated_data(llm_response, schema)


def test_parse_generated_data_missing_columns():
    """Test handling when columns are missing from generated data."""
    schema = [
        {"name": "id", "type": "INTEGER"},
        {"name": "name", "type": "TEXT"},
        {"name": "email", "type": "TEXT"},
    ]

    # Missing 'email' column
    llm_response = json.dumps([{"id": 1, "name": "Alice"}])

    result = parse_generated_data(llm_response, schema)

    assert len(result) == 1
    assert result[0]["id"] == 1
    assert result[0]["name"] == "Alice"
    assert result[0]["email"] is None  # Should be filled with None


def test_parse_generated_data_type_conversion():
    """Test type conversion for numeric columns."""
    schema = [
        {"name": "id", "type": "INTEGER"},
        {"name": "price", "type": "REAL"},
    ]

    # LLM returns string values
    llm_response = json.dumps([{"id": "123", "price": "45.67"}])

    result = parse_generated_data(llm_response, schema)

    assert len(result) == 1
    assert isinstance(result[0]["id"], int)
    assert isinstance(result[0]["price"], float)


def test_insert_generated_rows_success():
    """Test successful insertion of generated rows."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create test table
    cursor.execute(
        """
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT,
            value INTEGER
        )
    """
    )
    conn.commit()

    schema = [
        {"name": "id", "type": "INTEGER"},
        {"name": "name", "type": "TEXT"},
        {"name": "value", "type": "INTEGER"},
    ]

    rows = [
        {"id": 1, "name": "Alice", "value": 100},
        {"id": 2, "name": "Bob", "value": 200},
    ]

    inserted_count = insert_generated_rows(conn, "test_table", rows, schema)

    assert inserted_count == 2

    # Verify data was inserted
    cursor.execute("SELECT * FROM test_table ORDER BY id")
    result = cursor.fetchall()
    assert len(result) == 2
    assert result[0] == (1, "Alice", 100)
    assert result[1] == (2, "Bob", 200)

    conn.close()


def test_insert_generated_rows_empty_list():
    """Test insertion with empty list returns 0."""
    conn = sqlite3.connect(":memory:")
    schema = [{"name": "id", "type": "INTEGER"}]

    inserted_count = insert_generated_rows(conn, "test_table", [], schema)

    assert inserted_count == 0
    conn.close()


def test_insert_generated_rows_constraint_violation():
    """Test handling of constraint violations during insertion."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create table with unique constraint
    cursor.execute(
        """
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE
        )
    """
    )

    # Insert initial data
    cursor.execute("INSERT INTO test_table VALUES (1, 'test@example.com')")
    conn.commit()

    schema = [
        {"name": "id", "type": "INTEGER"},
        {"name": "email", "type": "TEXT"},
    ]

    # Try to insert duplicate email
    rows = [
        {"id": 2, "email": "test@example.com"},  # Duplicate - will fail
        {"id": 3, "email": "unique@example.com"},  # Should succeed
    ]

    inserted_count = insert_generated_rows(conn, "test_table", rows, schema)

    # Should insert only the non-duplicate row
    assert inserted_count == 1

    # Verify only unique row was inserted
    cursor.execute("SELECT COUNT(*) FROM test_table")
    total_rows = cursor.fetchone()[0]
    assert total_rows == 2  # Original + 1 new row

    conn.close()


def test_insert_generated_rows_security():
    """Test SQL injection protection in table name."""
    conn = sqlite3.connect(":memory:")
    schema = [{"name": "id", "type": "INTEGER"}]
    rows = [{"id": 1}]

    with pytest.raises(SQLSecurityError):
        insert_generated_rows(conn, "table; DROP TABLE users--", rows, schema)

    conn.close()
