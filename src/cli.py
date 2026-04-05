from csv_loader import CSVLoader
from llm_adapter import MockLLMAdapter
from query_service import QueryService
from schema_manager import SchemaManager
from sql_validator import SQLValidator


DB_PATH = "example.db"


def print_rows(rows: list[dict]) -> None:
    # Print query results in a simple table format

    if not rows:
        print("(no rows)")
        return

    headers = list(rows[0].keys())
    print(" | ".join(headers))
    print("-" * len(" | ".join(headers)))
    for row in rows:
        print(" | ".join(str(row.get(header, "")) for header in headers))


def main() -> None:
    # Start the CLI and route commands to the project modules
    
    schema_manager = SchemaManager(DB_PATH)
    validator = SQLValidator(schema_manager)
    query_service = QueryService(
        db_path=DB_PATH,
        schema_manager=schema_manager,
        validator=validator,
        llm_adapter=MockLLMAdapter(),
    )
    csv_loader = CSVLoader(DB_PATH, schema_manager=schema_manager)

    print("Simple DB Assistant")
    print("Commands: load, tables, sql, ask, schema, exit")

    while True:
        cmd = input("\nEnter command: ").strip().lower()

        if cmd == "exit":
            print("Goodbye.")
            break

        if cmd == "tables":
            tables = query_service.list_tables()
            if not tables:
                print("No tables found.")
            else:
                print("Tables:")
                for table in tables:
                    print(f"- {table}")
            continue

        if cmd == "schema":
            print(schema_manager.format_schema_for_llm())
            continue

        if cmd == "load":
            csv_path = input("CSV path: ").strip()
            table_name = input("Table name (leave blank to infer): ").strip() or None
            if_exists = input("if_exists [fail/replace/append]: ").strip() or "fail"
            result = csv_loader.load_csv(csv_path=csv_path, table_name=table_name, if_exists=if_exists)

            if result.success:
                print(f"Loaded {result.rows_inserted} rows into table '{result.table_name}'.")
            else:
                print(f"Load failed: {result.error}")
            continue

        if cmd == "sql":
            sql = input("Enter SELECT SQL: ").strip()
            result = query_service.execute_user_sql(sql)

            if result.success:
                print("Query OK.")
                print_rows(result.rows or [])
            else:
                print(f"Rejected / failed: {result.error}")
            continue

        if cmd == "ask":
            user_query = input("Ask in natural language: ").strip()
            result = query_service.ask(user_query, show_generated_sql=True)

            if result.sql:
                print(f"Generated SQL: {result.sql}")
            if result.llm_explanation:
                print(f"Explanation: {result.llm_explanation}")
            if result.success:
                print_rows(result.rows or [])
            else:
                print(f"Failed: {result.error}")
            continue

        print("Unknown command. Use: load, tables, sql, ask, schema, exit")


if __name__ == "__main__":
    main()
