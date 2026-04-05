import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from csv_loader import CSVLoader
from schema_manager import SchemaManager


class CSVLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.tmp_path = Path(self.temp_dir.name)
        self.db_path = self.tmp_path / "test.db"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_csv(self, name: str, text: str) -> Path:
        path = self.tmp_path / name
        path.write_text(text, encoding="utf-8")
        return path

    def read_rows(self, sql: str) -> list[tuple]:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(sql).fetchall()

    def test_load_csv_creates_table_and_inserts_rows(self) -> None:
        # A brand-new CSV should create a table and load all rows

        loader = CSVLoader(str(self.db_path), schema_manager=SchemaManager(str(self.db_path)))
        csv_path = self.write_csv("products.csv", "name,price\napple,1.2\nbanana,0.8\n")

        result = loader.load_csv(str(csv_path), table_name="products", if_exists="replace")

        self.assertTrue(result.success)
        self.assertEqual(result.rows_inserted, 2)
        self.assertEqual(self.read_rows('SELECT name, price FROM products ORDER BY id'), [("apple", 1.2), ("banana", 0.8)])

    def test_append_matching_schema_adds_rows(self) -> None:
        # If schemas match, append should keep old rows and add new ones

        loader = CSVLoader(str(self.db_path), schema_manager=SchemaManager(str(self.db_path)))
        first_csv = self.write_csv("products_1.csv", "name,price\napple,1.2\n")
        second_csv = self.write_csv("products_2.csv", "name,price\nbanana,0.8\n")

        loader.load_csv(str(first_csv), table_name="products", if_exists="replace")
        result = loader.load_csv(str(second_csv), table_name="products", if_exists="append")

        self.assertTrue(result.success)
        self.assertEqual(self.read_rows('SELECT name FROM products ORDER BY id'), [("apple",), ("banana",)])

    def test_append_conflict_can_rename_table(self) -> None:
        # If schemas do not match, choosing rename should preserve both tables
        
        loader = CSVLoader(str(self.db_path), schema_manager=SchemaManager(str(self.db_path)))
        first_csv = self.write_csv("products_1.csv", "name,price\napple,1.2\n")
        second_csv = self.write_csv("products_2.csv", "name,qty\nbanana,3\n")

        loader.load_csv(str(first_csv), table_name="products", if_exists="replace")
        with patch("builtins.input", return_value="rename"):
            result = loader.load_csv(str(second_csv), table_name="products", if_exists="append")

        self.assertTrue(result.success)
        self.assertEqual(result.table_name, "products_new")
        self.assertEqual(
            self.read_rows("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"),
            [("products",), ("products_new",)],
        )
