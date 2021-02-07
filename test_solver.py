import unittest
from app import merit_order_optimizer


class TestMOSolver(unittest.TestCase):
    def test_solver(self):
        costs = [6, 8, 5, 2]
        powers = [3, 4, 7, 9]
        names = ["name_1", "name_2", "name_3", "name_4"]
        load = 18
        opt = merit_order_optimizer(costs, powers, load, names)
        self.assertEqual(
            opt, [(9, "name_4"), (7, "name_3"), (2, "name_1"), (0, "name_2")]
        )

    def test_infeasible(self):
        costs = [6, 8, 5, 2]
        powers = [3, 4, 7, 9]
        names = ["name_1", "name_2", "name_3", "name_4"]
        load = 100
        opt = merit_order_optimizer(costs, powers, load, names)
        self.assertIsNone(opt)


if __name__ == "__main__":
    unittest.main()
