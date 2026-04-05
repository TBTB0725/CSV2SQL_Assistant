import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from schema_manager import SchemaManager


class SchemaManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.tmp_path = Path(self.temp_dir.name)
        self.db_path = self.tmp_path / "test.db"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_infer_schema_adds_id_and_normalizes_names(self) -> None:
        # Inferred schemas should add the id column and normalize identifiers

        manager = SchemaManager(str(self.db_path))
        df = pd.DataFrame({"Product Name": ["apple"], "Price": [1.5]})

        schema = manager.infer_schema_from_dataframe(df, "Sales Data")

        self.assertEqual(schema.table_name, "Sales_Data")
        self.assertEqual(schema.columns[0].name, "id")
        self.assertTrue(schema.columns[0].is_primary_key)
        self.assertEqual([col.name for col in schema.columns[1:]], ["Product_Name", "Price"])
        self.assertEqual([col.data_type for col in schema.columns[1:]], ["TEXT", "REAL"])

    def test_generate_create_table_sql_uses_autoincrement_id(self) -> None:
        # New-table SQL should include the required autoincrement primary key

        manager = SchemaManager(str(self.db_path))
        df = pd.DataFrame({"name": ["apple"], "qty": [2]})
        schema = manager.infer_schema_from_dataframe(df, "products")

        sql = manager.generate_create_table_sql(schema)

        self.assertIn('"id" INTEGER PRIMARY KEY AUTOINCREMENT', sql)
        self.assertIn('"name" TEXT', sql)
        self.assertIn('"qty" INTEGER', sql)
