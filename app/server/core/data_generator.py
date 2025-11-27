"""
Core data generation module for synthetic data creation.
Handles sampling, validation, and insertion of LLM-generated data.
"""

import json
import sqlite3
import logging
from typing import List, Dict, Any
from .sql_security import (
    validate_identifier,
    check_table_exists,
    execute_query_safely,
    escape_identifier,
)

logger = logging.getLogger(__name__)


def sample_random_rows(
    conn: sqlite3.Connection, table_name: str, sample_size: int = 10
) -> List[Dict[str, Any]]:
    """
    Sample random rows from a table for use as examples in data generation.

    Args:
        conn: SQLite connection object
        table_name: Name of the table to sample from
        sample_size: Number of rows to sample (default: 10)

    Returns:
        List[Dict[str, Any]]: List of row dictionaries

    Raises:
        SQLSecurityError: If table name is invalid
        ValueError: If table doesn't exist or has no data
    """
    # Validate table name
    validate_identifier(table_name, "table")

    # Check table exists
    if not check_table_exists(conn, table_name):
        raise ValueError(f"Table '{table_name}' does not exist")

    # Check if table has any data
    cursor = execute_query_safely(
        conn,
        "SELECT COUNT(*) FROM {table}",
        identifier_params={"table": table_name},
    )
    row_count = cursor.fetchone()[0]

    if row_count == 0:
        raise ValueError("Table must have at least 1 row to generate synthetic data")

    # Sample random rows (up to sample_size, but may be less if table is small)
    actual_sample_size = min(sample_size, row_count)

    cursor = execute_query_safely(
        conn,
        "SELECT * FROM {table} ORDER BY RANDOM() LIMIT ?",
        params=(actual_sample_size,),
        identifier_params={"table": table_name},
    )

    # Get column names
    columns = [description[0] for description in cursor.description]

    # Convert rows to dictionaries
    rows = []
    for row in cursor.fetchall():
        row_dict = {columns[i]: row[i] for i in range(len(columns))}
        rows.append(row_dict)

    return rows


def format_data_generation_prompt(
    table_name: str, schema: List[Dict[str, Any]], sample_rows: List[Dict[str, Any]]
) -> str:
    """
    Format a prompt for the LLM to generate synthetic data.

    Args:
        table_name: Name of the table
        schema: List of column information dictionaries with 'name' and 'type'
        sample_rows: Sample rows from the table

    Returns:
        str: Formatted prompt for the LLM
    """
    # Format schema information
    schema_text = "\n".join(
        [f"  - {col['name']}: {col['type']}" for col in schema]
    )

    # Format sample data
    sample_text = json.dumps(sample_rows, indent=2, default=str)

    prompt = f"""You are a synthetic data generator. Your task is to generate 10 new realistic data rows for the table "{table_name}" that match the patterns, formats, and characteristics of the existing data.

Table Schema:
{schema_text}

Sample Existing Rows:
{sample_text}

Instructions:
1. Analyze the sample data carefully to understand:
   - Data types (strings, numbers, dates, booleans, nulls)
   - Value ranges and distributions
   - Common patterns (emails, phone numbers, addresses, names, etc.)
   - Relationships between columns
   - Which fields can be null vs required
   - Format conventions (date formats, number precision, text casing)

2. Generate exactly 10 new rows that:
   - Match the data types and formats from the schema
   - Follow the same patterns as the sample data
   - Are realistic and diverse
   - Maintain consistency with the existing data
   - Use appropriate null values where the sample data shows nulls

3. Return ONLY a valid JSON array of 10 objects, where each object has keys matching the exact column names from the schema.

4. Do not include any explanatory text, markdown formatting, or code blocks - return only the raw JSON array.

Generate the 10 new rows now:"""

    return prompt


def parse_generated_data(
    llm_response: str, schema: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Parse and validate LLM-generated synthetic data.

    Args:
        llm_response: Raw response from the LLM
        schema: Table schema for validation

    Returns:
        List[Dict[str, Any]]: Validated list of row dictionaries

    Raises:
        ValueError: If response is invalid or doesn't match schema
    """
    # Extract JSON from response (handle cases where LLM adds markdown code blocks)
    response_text = llm_response.strip()

    # Remove markdown code blocks if present
    if response_text.startswith("```"):
        # Find the first newline after ```json or ```
        start_idx = response_text.find("\n")
        if start_idx != -1:
            # Find the closing ```
            end_idx = response_text.rfind("```")
            if end_idx != -1:
                response_text = response_text[start_idx + 1 : end_idx].strip()

    # Parse JSON
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response from LLM: {e}")

    # Validate it's a list
    if not isinstance(data, list):
        raise ValueError("LLM response must be a JSON array of objects")

    # Validate each row
    expected_columns = {col["name"] for col in schema}

    validated_rows = []
    for idx, row in enumerate(data):
        if not isinstance(row, dict):
            raise ValueError(f"Row {idx} is not a JSON object")

        # Check for missing or extra columns
        row_columns = set(row.keys())
        missing_cols = expected_columns - row_columns
        extra_cols = row_columns - expected_columns

        if missing_cols:
            logger.warning(
                f"Row {idx} missing columns: {missing_cols}. Setting to None."
            )
            for col in missing_cols:
                row[col] = None

        if extra_cols:
            logger.warning(f"Row {idx} has extra columns: {extra_cols}. Ignoring.")
            for col in extra_cols:
                del row[col]

        # Basic type validation and conversion
        for col in schema:
            col_name = col["name"]
            col_type = col["type"].upper()
            value = row.get(col_name)

            # Allow nulls
            if value is None:
                continue

            # Type checking and conversion
            try:
                if "INT" in col_type:
                    if not isinstance(value, (int, float)):
                        row[col_name] = int(value)
                elif "REAL" in col_type or "FLOAT" in col_type or "DOUBLE" in col_type:
                    if not isinstance(value, (int, float)):
                        row[col_name] = float(value)
                elif "TEXT" in col_type or "VARCHAR" in col_type or "CHAR" in col_type:
                    if not isinstance(value, str):
                        row[col_name] = str(value)
                # For other types, leave as-is
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Type conversion error for {col_name} in row {idx}: {e}. Using original value."
                )

        validated_rows.append(row)

    return validated_rows


def insert_generated_rows(
    conn: sqlite3.Connection,
    table_name: str,
    rows: List[Dict[str, Any]],
    schema: List[Dict[str, Any]],
) -> int:
    """
    Insert generated rows into the table.

    Args:
        conn: SQLite connection object
        table_name: Name of the table
        rows: List of row dictionaries to insert
        schema: Table schema for column ordering

    Returns:
        int: Number of successfully inserted rows

    Raises:
        SQLSecurityError: If table name is invalid
        ValueError: If insertion fails
    """
    # Validate table name
    validate_identifier(table_name, "table")

    if not rows:
        return 0

    # Get column names in order from schema
    column_names = [col["name"] for col in schema]

    # Build INSERT query
    escaped_table = escape_identifier(table_name)
    escaped_columns = ", ".join([escape_identifier(col) for col in column_names])
    placeholders = ", ".join(["?" for _ in column_names])

    query = f"INSERT INTO {escaped_table} ({escaped_columns}) VALUES ({placeholders})"

    # Insert rows
    inserted_count = 0
    errors = []

    for idx, row in enumerate(rows):
        try:
            # Extract values in the correct column order
            values = [row.get(col_name) for col_name in column_names]

            # Execute insert
            cursor = conn.cursor()
            cursor.execute(query, values)
            inserted_count += 1
        except sqlite3.IntegrityError as e:
            error_msg = f"Row {idx}: Integrity constraint violation: {e}"
            errors.append(error_msg)
            logger.warning(error_msg)
        except sqlite3.Error as e:
            error_msg = f"Row {idx}: Database error: {e}"
            errors.append(error_msg)
            logger.warning(error_msg)

    # Commit the transaction
    conn.commit()

    if inserted_count == 0 and errors:
        raise ValueError(
            f"Failed to insert any rows. Errors: {'; '.join(errors[:3])}"
        )

    if errors and inserted_count < len(rows):
        logger.info(
            f"Inserted {inserted_count}/{len(rows)} rows. Some rows failed due to constraints."
        )

    return inserted_count
