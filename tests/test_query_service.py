import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from csv_loader import CSVLoader
from llm_adapter import BaseLLMAdapter, LLMResponse
from query_service import QueryService
from schema_manager import SchemaManager
from sql_validator import SQLValidator


class StubLLMAdapter(BaseLLMAdapter):
    def __init__(self, response: LLMResponse) -> None:
        self.response = response

    def generate_sql(self, user_query: str, schema_context: str) -> LLMResponse:
        return self.response


class QueryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.tmp_path = Path(self.temp_dir.name)
        self.db_path = self.tmp_path / "test.db"
        self.schema_manager = SchemaManager(str(self.db_path))
        loader = CSVLoader(str(self.db_path), schema_manager=self.schema_manager)
        csv_path = self.tmp_path / "products.csv"
        csv_path.write_text("name,price\napple,1.2\nbanana,0.8\n", encoding="utf-8")
        loader.load_csv(str(csv_path), table_name="products", if_exists="replace")
        self.validator = SQLValidator(self.schema_manager)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_execute_user_sql_returns_rows(self) -> None:
        # Direct user SQL should execute after validation and return rows

        service = QueryService(str(self.db_path), self.schema_manager, self.validator)

        result = service.execute_user_sql("SELECT name FROM products ORDER BY id;")

        self.assertTrue(result.success)
        self.assertEqual(result.rows, [{"name": "apple"}, {"name": "banana"}])

    def test_ask_rejects_bad_llm_sql(self) -> None:
        # Bad SQL from the LLM should be blocked by the validator

        adapter = StubLLMAdapter(LLMResponse(success=True, sql="SELECT revenue FROM products;", explanation="bad sql"))
        service = QueryService(str(self.db_path), self.schema_manager, self.validator, adapter)

        result = service.ask("show revenue")

        self.assertFalse(result.success)
        self.assertIn("rejected by validator", result.error)
        self.assertEqual(result.sql, "SELECT revenue FROM products;")

    def test_ask_executes_valid_llm_sql(self) -> None:
        # Good SQL from the LLM should pass validation and run successfully
        
        adapter = StubLLMAdapter(LLMResponse(success=True, sql="SELECT name FROM products ORDER BY id;", explanation="good sql"))
        service = QueryService(str(self.db_path), self.schema_manager, self.validator, adapter)

        result = service.ask("show products")

        self.assertTrue(result.success)
        self.assertEqual(result.rows, [{"name": "apple"}, {"name": "banana"}])
        self.assertEqual(result.llm_explanation, "good sql")
