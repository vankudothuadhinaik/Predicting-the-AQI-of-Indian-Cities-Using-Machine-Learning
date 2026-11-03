import csv
import tempfile
import unittest
from pathlib import Path

from evaluate_baseline import evaluate, load_series


class BaselineEvaluationTests(unittest.TestCase):
    def write_csv(self, rows):
        temporary = tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8", suffix=".csv", delete=False)
        self.addCleanup(lambda: Path(temporary.name).unlink(missing_ok=True))
        with temporary:
            writer = csv.DictWriter(temporary, fieldnames=["ID_Date", "AQI"])
            writer.writeheader()
            writer.writerows(rows)
        return Path(temporary.name)

    def test_chronological_persistence_metrics_are_deterministic(self):
        path = self.write_csv([
            {"ID_Date": f"A_1_2024-01-0{i}", "AQI": value}
            for i, value in [(1, 10), (2, 12), (3, 15), (4, 14), (5, 18)]
        ])
        result = evaluate(load_series(path), test_fraction=0.4)
        self.assertEqual(result["test_rows"], 2)
        self.assertEqual(result["test_start"], "2024-01-04")
        self.assertAlmostEqual(result["mae"], 2.5)
        self.assertAlmostEqual(result["rmse"], (8.5) ** 0.5)
        self.assertEqual(result["per_series"]["A_1"]["test_rows"], 2)
        self.assertEqual(result["per_series"]["A_1"]["test_start"], "2024-01-04")
        self.assertAlmostEqual(result["per_series"]["A_1"]["mae"], 2.5)

    def test_series_are_evaluated_independently(self):
        rows = []
        for series, values in (("A_1", [1, 2, 3]), ("B_2", [10, 10, 10])):
            for day, value in enumerate(values, start=1):
                rows.append({"ID_Date": f"{series}_2024-01-0{day}", "AQI": value})
        result = evaluate(load_series(self.write_csv(rows)), test_fraction=0.34)
        self.assertEqual(result["series"], 2)
        self.assertEqual(result["test_rows"], 2)
        self.assertEqual(result["per_series"]["A_1"]["test_rows"], 1)
        self.assertEqual(result["per_series"]["B_2"]["test_rows"], 1)
        self.assertEqual(result["per_series"]["B_2"]["mae"], 0.0)

    def test_rejects_malformed_id_date(self):
        path = self.write_csv([
            {"ID_Date": "missing-date", "AQI": "1"},
            {"ID_Date": "A_1_2024-01-02", "AQI": "2"},
            {"ID_Date": "A_1_2024-01-03", "AQI": "3"},
        ])
        with self.assertRaisesRegex(ValueError, "ID_Date"):
            load_series(path)

    def test_rejects_impossible_calendar_dates(self):
        path = self.write_csv([
            {"ID_Date": "A_1_2024-02-30", "AQI": "1"},
            {"ID_Date": "A_1_2024-03-01", "AQI": "2"},
            {"ID_Date": "A_1_2024-03-02", "AQI": "3"},
        ])
        with self.assertRaises(ValueError):
            load_series(path)

    def test_rejects_duplicate_dates_within_a_series(self):
        path = self.write_csv([
            {"ID_Date": "A_1_2024-01-01", "AQI": "1"},
            {"ID_Date": "A_1_2024-01-01", "AQI": "2"},
            {"ID_Date": "A_1_2024-01-03", "AQI": "3"},
        ])
        with self.assertRaisesRegex(ValueError, "duplicate date"):
            load_series(path)

    def test_rejects_invalid_test_fraction(self):
        path = self.write_csv([
            {"ID_Date": f"A_1_2024-01-0{i}", "AQI": str(i)}
            for i in range(1, 5)
        ])
        with self.assertRaisesRegex(ValueError, "test fraction"):
            evaluate(load_series(path), test_fraction=0.9)

    def test_rejects_non_finite_aqi(self):
        path = self.write_csv([
            {"ID_Date": f"A_1_2024-01-0{i}", "AQI": value}
            for i, value in [(1, "1"), (2, "NaN"), (3, "3")]
        ])
        with self.assertRaisesRegex(ValueError, "finite"):
            load_series(path)



    def test_rejects_duplicate_csv_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "train.csv"
            path.write_text(
                "ID_Date,AQI,AQI\nA_1_2024-01-01,1,2\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate column names"):
                load_series(path)

    def test_rejects_surplus_fields_with_source_line_number(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "train.csv"
            path.write_text(
                "ID_Date,AQI\n"
                "A_1_2024-01-01,1\n"
                "A_1_2024-01-02,2,unexpected\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "line 3.*more fields"):
                load_series(path)

    def test_invalid_calendar_date_includes_source_line_number(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "train.csv"
            path.write_text(
                "ID_Date,AQI\n"
                "A_1_2024-02-30,1\n"
                "A_1_2024-03-01,2\n"
                "A_1_2024-03-02,3\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "line 2.*invalid calendar date"):
                load_series(path)

    def test_rejects_malformed_quoted_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "train.csv"
            path.write_text(
                'ID_Date,AQI\nA_1_2024-01-01,"1\n',
                encoding="utf-8",
            )
            with self.assertRaises(csv.Error):
                load_series(path)

if __name__ == "__main__":
    unittest.main()
