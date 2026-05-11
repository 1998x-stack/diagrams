import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from condition_evaluator import evaluate_condition


class TestEvaluateCondition:
    def test_simple_true(self):
        assert evaluate_condition("x > 0", {"x": 1}) is True

    def test_simple_false(self):
        assert evaluate_condition("x > 0", {"x": -1}) is False

    def test_name_error_returns_false(self):
        # undefined_var not in state_dict → NameError → False
        assert evaluate_condition("undefined_var", {}) is False

    def test_syntax_error_returns_false(self):
        assert evaluate_condition("not valid python !!!", {}) is False

    def test_empty_condition_returns_false(self):
        assert evaluate_condition("", {}) is False

    def test_complex_predicate_true(self):
        state = {"inventory": ["pizza"], "oven": "ready"}
        assert evaluate_condition("'pizza' in inventory and oven == 'ready'", state) is True

    def test_complex_predicate_false(self):
        state = {"inventory": [], "oven": "ready"}
        assert evaluate_condition("'pizza' in inventory and oven == 'ready'", state) is False

    def test_zero_is_falsy(self):
        assert evaluate_condition("count", {"count": 0}) is False

    def test_nonempty_list_is_truthy(self):
        assert evaluate_condition("items", {"items": ["a"]}) is True

    def test_exception_in_eval_returns_false(self):
        # Division by zero inside condition
        assert evaluate_condition("1 / 0", {}) is False

    def test_builtins_restricted(self):
        # __import__ should not be accessible
        assert evaluate_condition("__import__('os')", {}) is False
