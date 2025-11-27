import os
from typing import Dict, Any
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
from core.data_models import QueryRequest

def generate_sql_with_openai(query_text: str, schema_info: Dict[str, Any]) -> str:
    """
    Generate SQL query using OpenAI API
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        client = OpenAI(api_key=api_key)
        
        # Format schema for prompt
        schema_description = format_schema_for_prompt(schema_info)
        
        # Create prompt
        prompt = f"""Given the following database schema:

{schema_description}

Convert this natural language query to SQL: "{query_text}"

Rules:
- Return ONLY the SQL query, no explanations
- Use proper SQLite syntax
- Handle date/time queries appropriately (e.g., "last week" = date('now', '-7 days'))
- Be careful with column names and table names
- If the query is ambiguous, make reasonable assumptions
- For multi-table queries, use proper JOIN conditions to avoid Cartesian products
- Limit results to reasonable amounts (e.g., add LIMIT 100 for large result sets)
- When joining tables, use meaningful relationships between tables
- NEVER include SQL comments (-- or /* */) in the query

SQL Query:"""
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=[
                {"role": "system", "content": "You are a SQL expert. Convert natural language to SQL queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        sql = response.choices[0].message.content.strip()
        
        # Clean up the SQL (remove markdown if present)
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        
        return sql.strip()
        
    except Exception as e:
        raise Exception(f"Error generating SQL with OpenAI: {str(e)}")

def generate_sql_with_anthropic(query_text: str, schema_info: Dict[str, Any]) -> str:
    """
    Generate SQL query using Anthropic API
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        client = Anthropic(api_key=api_key)
        
        # Format schema for prompt
        schema_description = format_schema_for_prompt(schema_info)
        
        # Create prompt
        prompt = f"""Given the following database schema:

{schema_description}

Convert this natural language query to SQL: "{query_text}"

Rules:
- Return ONLY the SQL query, no explanations
- Use proper SQLite syntax
- Handle date/time queries appropriately (e.g., "last week" = date('now', '-7 days'))
- Be careful with column names and table names
- If the query is ambiguous, make reasonable assumptions
- For multi-table queries, use proper JOIN conditions to avoid Cartesian products
- Limit results to reasonable amounts (e.g., add LIMIT 100 for large result sets)
- When joining tables, use meaningful relationships between tables
- NEVER include SQL comments (-- or /* */) in the query

SQL Query:"""
        
        # Call Anthropic API
        response = client.messages.create(
            model="claude-sonnet-4-0",
            max_tokens=500,
            temperature=0.1,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        sql = response.content[0].text.strip()
        
        # Clean up the SQL (remove markdown if present)
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        
        return sql.strip()
        
    except Exception as e:
        raise Exception(f"Error generating SQL with Anthropic: {str(e)}")

def generate_sql_with_gemini(query_text: str, schema_info: Dict[str, Any]) -> str:
    """
    Generate SQL query using Google Gemini API
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Format schema for prompt
        schema_description = format_schema_for_prompt(schema_info)

        # Create prompt
        prompt = f"""Given the following database schema:

{schema_description}

Convert this natural language query to SQL: "{query_text}"

Rules:
- Return ONLY the SQL query, no explanations
- Use proper SQLite syntax
- Handle date/time queries appropriately (e.g., "last week" = date('now', '-7 days'))
- Be careful with column names and table names
- If the query is ambiguous, make reasonable assumptions
- For multi-table queries, use proper JOIN conditions to avoid Cartesian products
- Limit results to reasonable amounts (e.g., add LIMIT 100 for large result sets)
- When joining tables, use meaningful relationships between tables
- NEVER include SQL comments (-- or /* */) in the query

SQL Query:"""

        # Call Gemini API
        response = model.generate_content(prompt)

        sql = response.text.strip()

        # Clean up the SQL (remove markdown if present)
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]

        return sql.strip()

    except Exception as e:
        raise Exception(f"Error generating SQL with Gemini: {str(e)}")

def format_schema_for_prompt(schema_info: Dict[str, Any]) -> str:
    """
    Format database schema for LLM prompt
    """
    lines = []
    
    for table_name, table_info in schema_info.get('tables', {}).items():
        lines.append(f"Table: {table_name}")
        lines.append("Columns:")
        
        for col_name, col_type in table_info['columns'].items():
            lines.append(f"  - {col_name} ({col_type})")
        
        lines.append(f"Row count: {table_info['row_count']}")
        lines.append("")
    
    return "\n".join(lines)

def generate_random_query_with_openai(schema_info: Dict[str, Any]) -> str:
    """
    Generate a random natural language query using OpenAI API
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        client = OpenAI(api_key=api_key)
        
        # Format schema for prompt
        schema_description = format_schema_for_prompt(schema_info)
        
        # Create prompt
        prompt = f"""Given the following database schema:

{schema_description}

Generate an interesting natural language query that someone might ask about this data. 
The query should be:
- Contextually relevant to the table structures and columns
- Natural and conversational
- Maximum two sentences
- Something that would demonstrate the capability of natural language to SQL conversion
- Varied in complexity (sometimes simple, sometimes complex with JOINs or aggregations)
- Do NOT include any SQL syntax, comments, or special characters

Examples of good queries:
- "What are the top 5 products by revenue?"
- "Show me all customers who ordered in the last month."
- "Which employees have the highest average sales? List their names and departments."

Natural language query:"""
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates interesting questions about data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=100
        )
        
        query = response.choices[0].message.content.strip()
        return query
        
    except Exception as e:
        raise Exception(f"Error generating random query with OpenAI: {str(e)}")

def generate_random_query_with_anthropic(schema_info: Dict[str, Any]) -> str:
    """
    Generate a random natural language query using Anthropic API
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        client = Anthropic(api_key=api_key)
        
        # Format schema for prompt
        schema_description = format_schema_for_prompt(schema_info)
        
        # Create prompt
        prompt = f"""Given the following database schema:

{schema_description}

Generate an interesting natural language query that someone might ask about this data. 
The query should be:
- Contextually relevant to the table structures and columns
- Natural and conversational
- Maximum two sentences
- Something that would demonstrate the capability of natural language to SQL conversion
- Varied in complexity (sometimes simple, sometimes complex with JOINs or aggregations)
- Do NOT include any SQL syntax, comments, or special characters

Examples of good queries:
- "What are the top 5 products by revenue?"
- "Show me all customers who ordered in the last month."
- "Which employees have the highest average sales? List their names and departments."

Natural language query:"""
        
        # Call Anthropic API
        response = client.messages.create(
            model="claude-sonnet-4-0",
            max_tokens=100,
            temperature=0.8,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        query = response.content[0].text.strip()
        return query
        
    except Exception as e:
        raise Exception(f"Error generating random query with Anthropic: {str(e)}")

def generate_random_query_with_gemini(schema_info: Dict[str, Any]) -> str:
    """
    Generate a random natural language query using Google Gemini API
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Format schema for prompt
        schema_description = format_schema_for_prompt(schema_info)

        # Create prompt
        prompt = f"""Given the following database schema:

{schema_description}

Generate an interesting natural language query that someone might ask about this data.
The query should be:
- Contextually relevant to the table structures and columns
- Natural and conversational
- Maximum two sentences
- Something that would demonstrate the capability of natural language to SQL conversion
- Varied in complexity (sometimes simple, sometimes complex with JOINs or aggregations)
- Do NOT include any SQL syntax, comments, or special characters

Examples of good queries:
- "What are the top 5 products by revenue?"
- "Show me all customers who ordered in the last month."
- "Which employees have the highest average sales? List their names and departments."

Natural language query:"""

        # Call Gemini API
        response = model.generate_content(prompt)

        query = response.text.strip()
        return query

    except Exception as e:
        raise Exception(f"Error generating random query with Gemini: {str(e)}")

def generate_random_query(schema_info: Dict[str, Any]) -> str:
    """
    Route to appropriate LLM provider for random query generation
    Priority: 1) Gemini API key exists, 2) OpenAI API key exists, 3) Anthropic API key exists
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    # Check API key availability (Gemini priority)
    if gemini_key:
        return generate_random_query_with_gemini(schema_info)
    elif openai_key:
        return generate_random_query_with_openai(schema_info)
    elif anthropic_key:
        return generate_random_query_with_anthropic(schema_info)
    else:
        raise ValueError("No LLM API key found. Please set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY")

def generate_sql(request: QueryRequest, schema_info: Dict[str, Any]) -> str:
    """
    Route to appropriate LLM provider based on API key availability and request preference.
    Priority: 1) Gemini API key exists, 2) OpenAI API key exists, 3) Anthropic API key exists
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    # Check API key availability first (Gemini priority)
    if gemini_key:
        return generate_sql_with_gemini(request.query, schema_info)
    elif openai_key:
        return generate_sql_with_openai(request.query, schema_info)
    elif anthropic_key:
        return generate_sql_with_anthropic(request.query, schema_info)

    # Fall back to request preference if no keys available
    if request.llm_provider == "gemini":
        return generate_sql_with_gemini(request.query, schema_info)
    elif request.llm_provider == "openai":
        return generate_sql_with_openai(request.query, schema_info)
    else:
        return generate_sql_with_anthropic(request.query, schema_info)

def generate_synthetic_data_with_gemini(
    table_name: str,
    schema: Dict[str, str],
    sample_rows: list,
    num_rows: int = 10
) -> list:
    """
    Generate synthetic data rows using Google Gemini API
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Format schema and sample data for prompt
        schema_str = "\n".join([f"  - {col}: {dtype}" for col, dtype in schema.items()])
        sample_str = "\n".join([str(row) for row in sample_rows[:5]])

        prompt = f"""Analyze the following table schema and sample data, then generate {num_rows} new synthetic rows that match the patterns.

Table: {table_name}

Schema:
{schema_str}

Sample existing rows:
{sample_str}

Requirements:
- Generate exactly {num_rows} new rows
- Match the data types exactly as specified in the schema
- Follow patterns observed in the sample data (formats, ranges, distributions)
- For text fields, generate realistic values matching the context (emails, names, addresses, etc.)
- For numeric fields, stay within reasonable ranges based on sample data
- For date fields, use proper date formats
- Ensure data is diverse but realistic
- Do NOT duplicate exact values from sample data

Return ONLY a valid JSON array of objects with the exact column names from the schema.
Example format:
[
  {{"column1": "value1", "column2": 123}},
  {{"column1": "value2", "column2": 456}}
]

JSON array:"""

        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Clean up JSON response
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        import json
        return json.loads(result_text.strip())

    except Exception as e:
        raise Exception(f"Error generating synthetic data with Gemini: {str(e)}")

def generate_synthetic_data_with_openai(
    table_name: str,
    schema: Dict[str, str],
    sample_rows: list,
    num_rows: int = 10
) -> list:
    """
    Generate synthetic data rows using OpenAI API
    """
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        client = OpenAI(api_key=api_key)

        schema_str = "\n".join([f"  - {col}: {dtype}" for col, dtype in schema.items()])
        sample_str = "\n".join([str(row) for row in sample_rows[:5]])

        prompt = f"""Analyze the following table schema and sample data, then generate {num_rows} new synthetic rows that match the patterns.

Table: {table_name}

Schema:
{schema_str}

Sample existing rows:
{sample_str}

Requirements:
- Generate exactly {num_rows} new rows
- Match the data types exactly as specified in the schema
- Follow patterns observed in the sample data
- Generate realistic values
- Ensure data is diverse but realistic
- Do NOT duplicate exact values from sample data

Return ONLY a valid JSON array of objects with the exact column names from the schema."""

        response = client.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=[
                {"role": "system", "content": "You are a data generation expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        result_text = response.choices[0].message.content.strip()

        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        import json
        return json.loads(result_text.strip())

    except Exception as e:
        raise Exception(f"Error generating synthetic data with OpenAI: {str(e)}")

def generate_synthetic_data_with_anthropic(
    table_name: str,
    schema: Dict[str, str],
    sample_rows: list,
    num_rows: int = 10
) -> list:
    """
    Generate synthetic data rows using Anthropic API
    """
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        client = Anthropic(api_key=api_key)

        schema_str = "\n".join([f"  - {col}: {dtype}" for col, dtype in schema.items()])
        sample_str = "\n".join([str(row) for row in sample_rows[:5]])

        prompt = f"""Analyze the following table schema and sample data, then generate {num_rows} new synthetic rows that match the patterns.

Table: {table_name}

Schema:
{schema_str}

Sample existing rows:
{sample_str}

Requirements:
- Generate exactly {num_rows} new rows
- Match the data types exactly as specified in the schema
- Follow patterns observed in the sample data
- Generate realistic values
- Ensure data is diverse but realistic
- Do NOT duplicate exact values from sample data

Return ONLY a valid JSON array of objects with the exact column names from the schema."""

        response = client.messages.create(
            model="claude-sonnet-4-0",
            max_tokens=2000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        result_text = response.content[0].text.strip()

        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        import json
        return json.loads(result_text.strip())

    except Exception as e:
        raise Exception(f"Error generating synthetic data with Anthropic: {str(e)}")

def generate_synthetic_data(
    table_name: str,
    schema: Dict[str, str],
    sample_rows: list,
    num_rows: int = 10
) -> list:
    """
    Route to appropriate LLM provider for synthetic data generation.
    Priority: 1) Gemini, 2) OpenAI, 3) Anthropic
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if gemini_key:
        return generate_synthetic_data_with_gemini(table_name, schema, sample_rows, num_rows)
    elif openai_key:
        return generate_synthetic_data_with_openai(table_name, schema, sample_rows, num_rows)
    elif anthropic_key:
        return generate_synthetic_data_with_anthropic(table_name, schema, sample_rows, num_rows)
    else:
        raise ValueError("No LLM API key found. Please set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY")