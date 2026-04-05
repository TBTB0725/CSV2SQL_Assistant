# EC530 Project

## Overview
This project is a small command-line system that loads CSV data into SQLite and lets a user query that data either with direct SQL or with a simple natural-language interface.

The system is built around two flows:

1. Ingestion flow  
   CLI -> CSV Loader -> Schema Manager -> SQLite

2. Query flow  
   CLI -> Query Service -> LLM Adapter -> SQL Validator -> SQLite

## System Overview

### `src/cli.py`
The CLI is the entry point of the program. It accepts user commands and routes them to the appropriate module. It does not directly manipulate the database.

Supported commands:
- `load`
- `tables`
- `schema`
- `sql`
- `ask`
- `exit`

### `src/csv_loader.py`
This module loads CSV files into SQLite.

Responsibilities:
- read CSV files using `pandas.read_csv()`
- normalize table and column names
- ask the schema manager to infer table structure
- create tables manually
- insert rows manually
- handle `fail`, `replace`, and `append`
- handle schema conflicts with `overwrite`, `rename`, or `skip`

### `src/schema_manager.py`
This module is responsible for understanding schema.

Responsibilities:
- list existing tables
- read schema from SQLite using `PRAGMA table_info(...)`
- infer schema from a DataFrame
- generate `CREATE TABLE` SQL
- compare incoming schema with existing schema
- format schema text for the query pipeline

### `src/sql_validator.py`
This module protects the database by validating SQL before execution.

Responsibilities:
- only allow `SELECT`
- reject multi-statement SQL
- reject disallowed keywords such as `DELETE`, `DROP`, and `ALTER`
- reject unknown tables
- reject unknown columns

### `src/llm_adapter.py`
This module provides the natural-language-to-SQL layer.

Right now the project uses a `MockLLMAdapter`, which returns a few fixed SQL examples for demonstration. It is enough to test the full query pipeline, but it is not a real LLM integration.

### `src/query_service.py`
This module coordinates the query flow.

Responsibilities:
- validate and execute direct user SQL
- ask the LLM adapter to generate SQL
- validate LLM-generated SQL
- execute safe queries and return rows

## Design Decisions and Design Choices

### 1. Use a mock natural-language adapter for demonstration
The project includes the natural-language-to-SQL pipeline, but the adapter is intentionally simple. A mock adapter was chosen so the system can be demonstrated and tested without relying on external services.

### 2. Keep validation simple and structural
The validator does not try to fully parse SQL. Instead, it uses a smaller structure-level approach:
- check that the query starts with `SELECT`
- reject dangerous keywords
- check referenced tables
- check referenced columns

### 3. Prefer direct tests over complex test infrastructure
The tests were written in a simple style with temporary databases and direct assertions. This keeps the test code close to the project code and makes it easier to understand what each test is proving.

## How to Run the Project

### 1. Install dependencies
From the project root:

```bash
pip install -r requirements.txt
```

### 2. Start the CLI
Run:

```bash
python src/cli.py
```

### 3. Use the CLI
When the program starts, you will see:

```text
Commands: load, tables, sql, ask, schema, exit
```

Typical usage:

1. Load a CSV file
```text
load
products.csv
products
replace
```

2. List tables
```text
tables
```

3. Show schema
```text
schema
```

4. Run direct SQL
```text
sql
SELECT name, price FROM products;
```

5. Ask a natural-language question
```text
ask
list tables
```

Note: the `ask` command currently uses a mock adapter, so only a few built-in prompts work.

## How to Run Tests
Run all tests from the project root with:

```bash
python -m unittest discover -s tests -v
```

The tests currently cover:
- CSV loading
- schema inference
- `CREATE TABLE` generation
- query execution
- SQL validation rules
