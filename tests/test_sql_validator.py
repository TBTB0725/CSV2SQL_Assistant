import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from csv_loader import CSVLoader
from schema_manager import SchemaManager
from sql_validator import SQLValidator


class SQLValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.tmp_path = Path(self.temp_dir.name)
        self.db_path = self.tmp_path / "test.db"
        loader = CSVLoader(str(self.db_path), schema_manager=SchemaManager(str(self.db_path)))
        csv_path = self.tmp_path / "products.csv"
        csv_path.write_text("name,price\napple,1.2\nbanana,0.8\n", encoding="utf-8")
        loader.load_csv(str(csv_path), table_name="products", if_exists="replace")
        self.validator = SQLValidator(SchemaManager(str(self.db_path)))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_accepts_valid_select(self) -> None:
        # A normal read-only query should pass validation

        result = self.validator.validate("SELECT name FROM products WHERE price > 1;")
        self.assertTrue(result.is_valid)

    def test_rejects_non_select_query(self) -> None:
        # Write operations should be blocked

        result = self.validator.validate("DELETE FROM products;")
        self.assertFalse(result.is_valid)
        self.assertIn("Only SELECT", result.error)

    def test_rejects_unknown_table(self) -> None:
        # Queries should fail if they reference a table that does not exist

        result = self.validator.validate("SELECT * FROM users;")
        self.assertFalse(result.is_valid)
        self.assertIn("Unknown table", result.error)

    def test_rejects_unknown_column(self) -> None:
        # Queries should fail if they reference a missing column

        result = self.validator.validate("SELECT revenue FROM products;")
        self.assertFalse(result.is_valid)
        self.assertIn("Unknown column", result.error)