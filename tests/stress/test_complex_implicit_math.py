import unittest
from unittest.mock import patch, MagicMock
from runtime.router import route_tools
from runtime.tools import ALL_TOOLS
from runtime.functions import calculator

class TestComplexImplicitMath(unittest.TestCase):

    def setUp(self):
        pass

    def _check_router_has_calculator(self, query):
        tools = route_tools(query, ALL_TOOLS)
        names = [t.get("function", {}).get("name") for t in tools]
        self.assertIn("calculator", names, f"Query failed to route to calculator: '{query}'")

    def test_tipping_and_percentages(self):
        queries = [
            "What is 15% of 120 dollars",
            "Calculate 20 percent tip on a $45.50 bill",
            "How much is 10% tax on 250",
            "Add 8% tax to 500 dollars",
            "What is the final price of a 50 dollar shirt with 20 percent discount",
            "15 percent gratuity on a 200 dollar check"
        ]
        for q in queries:
            with self.subTest(query=q):
                self._check_router_has_calculator(q)

    @unittest.expectedFailure
    def test_expected_fail_restaurant_bill(self):
        # Memory set statement is matching: "(my|mah)\s+...is"
        self._check_router_has_calculator("If my restaurant bill is $85 and I want to leave an 18% tip, how much should I pay?")

    def test_splitting_and_division(self):
        queries = [
            "Split 4500 dollars evenly between 6 team members",
            "Divide 120 apples among 5 people",
            "If 4 of us share a $100 bill, how much each",
            "Distribute 500 tickets to 20 winners",
            "Share 300 coins between 3 players",
            "We have 5000 dollars budget for 10 people, what is the per person budget",
            "how much does each person pay if the rent is 2400 and there are 3 roommates"
        ]
        for q in queries:
            with self.subTest(query=q):
                self._check_router_has_calculator(q)

    def test_unit_conversions(self):
        queries = [
            "Convert 120 km/h to m/s",
            "Convert 5 miles to feet",
            "What is 100 Celsius in Fahrenheit",
            "Convert 50 lbs to kg",
            "convert 15 inches to cm",
            "how many meters in 5 kilometers",
            "change 200 euros to dollars",
            "what is 45 kilograms in pounds"
        ]
        for q in queries:
            with self.subTest(query=q):
                self._check_router_has_calculator(q)

    def test_arithmetic_sums(self):
        queries = [
            "What is the sum of 45, 92, 118, and 305?",
            "Add 1, 2, 3, 4 and 5 together",
            "Total cost of 12, 45, and 89 dollars",
            "Sum 450 and 800",
            "Subtract 45 from 100",
            "If I have 20 apples and eat 5, how many are left",
            "Multiply 15 by 12",
            "What is 8 times 9",
            "Product of 5 and 6",
            "calculate the difference between 500 and 120"
        ]
        for q in queries:
            with self.subTest(query=q):
                self._check_router_has_calculator(q)

    # ---------------------------------------------------------
    # EXPECTED FAILURES: COMPLEX ENTITY EXTRACTION
    # ---------------------------------------------------------
    @unittest.expectedFailure
    def test_expected_fail_mixed_intent_ram(self):
        # Fails because 'RAM' triggers system_health exclusively
        self._check_router_has_calculator("I have 16 GB of RAM and 11.2 GB is currently used, how many GB are free?")

    def test_expected_fail_time_math_days(self):
        self._check_router_has_calculator("How many seconds are there in 3.5 days?")

    def test_expected_fail_time_math_hours(self):
        self._check_router_has_calculator("How many hours in 4500 minutes?")

    def test_expected_fail_task_math(self):
        # Fails because 'remind' triggers task_add exclusively
        self._check_router_has_calculator("Remind me to add 50 and 80 together")

    @unittest.expectedFailure
    def test_expected_fail_service_math(self):
        # Fails because 'services' triggers service_status
        self._check_router_has_calculator("If I have 10 services running and 3 stop, how many are left?")

    # ---------------------------------------------------------
    # EXPECTED FAILURES: SYMBOLIC ALGEBRA (AST LIMITS)
    # ---------------------------------------------------------
    @unittest.expectedFailure
    def test_expected_fail_symbolic_algebra_1(self):
        # Testing calculator execution itself for symbolic algebra support.
        # Should return an error string, which will fail the float conversion.
        result = calculator("2*x + 4 = 10")
        float(result)

    @unittest.expectedFailure
    def test_expected_fail_symbolic_algebra_2(self):
        result = calculator("derivative(x**2)")
        float(result)

    @unittest.expectedFailure
    def test_expected_fail_symbolic_algebra_3(self):
        result = calculator("x + y = 5")
        float(result)

    # ---------------------------------------------------------
    # AST CALCULATOR LIMITS & PRECISION
    # ---------------------------------------------------------
    @patch("runtime.functions.subprocess.run")
    def test_ast_precision_floats(self, mock_run):
        # Python float precision (0.1 + 0.2 is notoriously 0.30000000000000004)
        result = calculator("0.1 + 0.2")
        self.assertEqual(result, "0.30000000000000004")

    @patch("runtime.functions.subprocess.run")
    def test_ast_large_exponent_blocked(self, mock_run):
        result = calculator("2 ** 2000")
        self.assertTrue(result.startswith("Error:"))
        self.assertIn("Exponent too large", result)

    @patch("runtime.functions.subprocess.run")
    def test_ast_division_by_zero(self, mock_run):
        result = calculator("50 / 0")
        self.assertTrue(result.startswith("Error:"))
        self.assertIn("division by zero", result)

    @patch("runtime.functions.subprocess.run")
    def test_ast_unsupported_operation(self, mock_run):
        # Bitwise shift not in _SAFE_OPERATORS
        result = calculator("1 << 2")
        self.assertTrue(result.startswith("Error:"))
        self.assertIn("Unsupported", result)

    @patch("runtime.functions.subprocess.run")
    def test_ast_scientific_notation(self, mock_run):
        # Verify formatting for large numbers
        result = calculator("10 ** 16")
        self.assertEqual(result, "1e+16")

    @patch("runtime.functions.subprocess.run")
    def test_ast_valid_math_expression(self, mock_run):
        # Test basic math parses correctly and returns stringified numbers
        self.assertEqual(calculator("15 * 12"), "180")
        self.assertEqual(calculator("4500 / 6"), "750")
        self.assertEqual(calculator("100 - 45"), "55")

if __name__ == "__main__":
    unittest.main()
