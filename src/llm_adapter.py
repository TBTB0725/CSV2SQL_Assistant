from dataclasses import dataclass


@dataclass
class LLMResponse:
    # Store the result returned by an LLM adapter

    success: bool
    sql: str | None = None
    explanation: str | None = None
    error: str | None = None
    raw_response: str | None = None


class BaseLLMAdapter:
    # Define the interface for turning natural language into SQL

    def generate_sql(self, user_query: str, schema_context: str) -> LLMResponse:
        # Return SQL generated from the user query and schema context.
        raise NotImplementedError


class MockLLMAdapter(BaseLLMAdapter):
    # Return a few hard-coded SQL examples for local testing

    def generate_sql(self, user_query: str, schema_context: str) -> LLMResponse:
        # Convert a small set of fixed prompts into SQL

        query = user_query.lower().strip()

        if "list tables" in query:
            return LLMResponse(
                success=True,
                sql="SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
                explanation="List all tables in the database.",
            )

        if "all products" in query:
            return LLMResponse(
                success=True,
                sql="SELECT * FROM products;",
                explanation="Show all rows from products.",
            )

        if "top 5 products" in query:
            return LLMResponse(
                success=True,
                sql="SELECT product_name, revenue FROM products ORDER BY revenue DESC LIMIT 5;",
                explanation="Show top 5 products by revenue.",
            )

        if "all users" in query:
            return LLMResponse(
                success=True,
                sql="SELECT * FROM users;",
                explanation="Show all users.",
            )

        return LLMResponse(success=False, error="MockLLMAdapter does not know how to answer this query.")