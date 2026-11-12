"""Unit test các hàm lõi. Chạy: python -m unittest discover tests"""
import unittest
from decimal import Decimal as D

from uat.calculator import compute_variation, round_value
from uat.comparator import values_match
from uat.formula import evaluate_formula
from uat.models import Report
from uat.text_utils import normalize_name, parse_number

REPORT = Report(path="test", meta={}, items={
    "CD270": {"value1": D("110"), "value2": D("100")},
    "CD400": {"value1": D("40"), "value2": D("0")},
    "KQ200": {"value1": D("10"), "value2": None},
})


class ParseNumberTest(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(parse_number("3,260,961"), D("3260961"))
        self.assertEqual(parse_number("8.53%"), D("8.53"))
        self.assertEqual(parse_number("-62.19%"), D("-62.19"))
        self.assertEqual(parse_number("(1.2%)"), D("-1.2"))
        self.assertIsNone(parse_number("N/A"))
        self.assertIsNone(parse_number(None))


class NormalizeNameTest(unittest.TestCase):
    def test_same_indicator_different_spelling(self):
        self.assertEqual(normalize_name("Tổng nợ / Vốn chủ sở hữu (%)"),
                         normalize_name("Tổng nợ/Vốn chủ sở hữu"))
        self.assertEqual(normalize_name("Tỷ lệ vốn khả dụng %"), normalize_name("Tỷ lệ vốn khả dụng"))


class FormulaTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(evaluate_formula("KQ200/CD400", REPORT, "value1").value, D("0.25"))

    def test_close_open(self):
        result = evaluate_formula("(CLOSE(CD270)-OPEN(CD270))/OPEN(CD270)", REPORT, "value1")
        self.assertEqual(result.value, D("0.1"))

    def test_missing_value(self):
        result = evaluate_formula("KQ200/CD400", REPORT, "value2")
        self.assertIsNone(result.value)
        self.assertIn("Thiếu KQ200.value2", result.note)

    def test_divide_by_zero(self):
        result = evaluate_formula("CD270/CD400", REPORT, "value2")
        self.assertEqual(result.note, "Chia cho 0")

    def test_inputs_are_extracted(self):
        inputs = evaluate_formula("KQ200/CD400", REPORT, "value1").inputs
        self.assertEqual([(i.code, i.column, i.value) for i in inputs],
                         [("KQ200", "value1", D("10")), ("CD400", "value1", D("40"))])

    def test_inputs_close_open_no_duplicate(self):
        inputs = evaluate_formula("(CLOSE(CD270)-OPEN(CD270))/OPEN(CD270)", REPORT, "value1").inputs
        self.assertEqual([(i.code, i.column) for i in inputs],
                         [("CD270", "value1"), ("CD270", "value2")])

    def test_inputs_keep_missing_value(self):
        inputs = evaluate_formula("KQ200/CD400", REPORT, "value2").inputs
        self.assertIsNone(inputs[0].value)

    def test_rejects_code_injection(self):
        with self.assertRaises(ValueError):
            evaluate_formula("__import__('os')", REPORT, "value1")


class CalculationTest(unittest.TestCase):
    def test_round_half_up(self):
        self.assertEqual(round_value(D("0.125"), 2), D("0.13"))
        self.assertEqual(round_value(D("2.5"), 0), D("3"))

    def test_variation(self):
        self.assertEqual(round_value(compute_variation(D("20"), D("15"))[0], 2), D("33.33"))
        self.assertIsNone(compute_variation(D("5"), D("0"))[0])

    def test_values_match_ignores_trailing_zero(self):
        self.assertTrue(values_match(D("100.4012"), D("100.4"), 2))
        self.assertFalse(values_match(D("100.4112"), D("100.4"), 2))


if __name__ == "__main__":
    unittest.main()
