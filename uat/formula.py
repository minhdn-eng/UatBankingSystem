"""Tính giá trị công thức dạng chuỗi, ví dụ 'KQ200/(KQ20+KQ50)' hay 'CLOSE(CD270)'.

Dùng cây cú pháp (ast) thay cho eval(): chỉ cho phép + - * / và ngoặc,
không thể chạy mã lạ nằm trong file công thức.
"""
from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable, Optional

import settings
from uat.models import InputValue, Report

_FUNCTION_PATTERN = re.compile(r"(CLOSE|OPEN)\(\s*([A-Za-z]+\d+)\s*\)")
_CODE_PATTERN = re.compile(r"[A-Z]+\d+(?:__(?:CLOSE|OPEN))?")
_BINARY_OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub,
                     ast.Mult: operator.mul, ast.Div: operator.truediv}


class MissingValueError(Exception):
    """Báo cáo không có số liệu cho mã dòng cần dùng."""


@dataclass(frozen=True)
class FormulaResult:
    value: Optional[Decimal]
    filled_formula: str   # công thức đã thay số, để soi khi sai
    note: str = ""
    inputs: tuple = ()    # các InputValue đã dùng


def evaluate_formula(formula: str, report: Optional[Report], field: str) -> FormulaResult:
    if report is None:
        return FormulaResult(None, "", "Không có BCTC cho kỳ này")

    expression = _rewrite_functions(formula)
    resolve = _make_resolver(report, field)
    filled = _fill_values(expression, resolve)
    inputs = collect_inputs(expression, report, field)
    try:
        tree = ast.parse(expression, mode="eval")
        return FormulaResult(_evaluate_node(tree.body, resolve, formula), filled, "", inputs)
    except MissingValueError as error:
        return FormulaResult(None, filled, str(error), inputs)
    except (ZeroDivisionError, InvalidOperation):
        return FormulaResult(None, filled, "Chia cho 0", inputs)


def collect_inputs(expression: str, report: Report, field: str) -> tuple:
    """Bóc tách các số liệu đầu vào mà công thức dùng, giữ thứ tự, bỏ trùng.
    'KQ200/CD400' -> (InputValue('KQ200', 'value1', 345...), InputValue('CD400', ...))"""
    found = {}
    for name in _CODE_PATTERN.findall(expression):
        code, column = _locate(name, field)
        found.setdefault((code, column), report.value(code, column))
    return tuple(InputValue(code, column, value) for (code, column), value in found.items())


def _rewrite_functions(formula: str) -> str:
    """CLOSE(CD270) -> CD270__CLOSE để ast đọc được như một biến."""
    return _FUNCTION_PATTERN.sub(lambda m: f"{m.group(2).upper()}__{m.group(1)}", formula.strip())


def _locate(name: str, field: str) -> tuple[str, str]:
    """'CD270__CLOSE' -> ('CD270', 'value1') | 'CD270' -> ('CD270', field)"""
    code, _, function = name.partition("__")
    column = {"CLOSE": settings.CLOSE_FIELD, "OPEN": settings.OPEN_FIELD}.get(function, field)
    return code, column


def _make_resolver(report: Report, field: str) -> Callable[[str], Decimal]:
    def resolve(name: str) -> Decimal:
        code, column = _locate(name, field)
        value = report.value(code, column)
        if value is None:
            raise MissingValueError(f"Thiếu {code}.{column}")
        return value
    return resolve


def _fill_values(expression: str, resolve: Callable[[str], Decimal]) -> str:
    def replace(match):
        try:
            return f"{resolve(match.group(0)):,}"
        except MissingValueError:
            return f"[{match.group(0)}?]"
    return _CODE_PATTERN.sub(replace, expression)


def _evaluate_node(node, resolve: Callable[[str], Decimal], formula: str) -> Decimal:
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_node(node.left, resolve, formula)
        right = _evaluate_node(node.right, resolve, formula)
        return _BINARY_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate_node(node.operand, resolve, formula)
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Decimal(str(node.value))
    if isinstance(node, ast.Name):
        return resolve(node.id)
    raise ValueError(f"Công thức có cú pháp không hỗ trợ: {formula}")
