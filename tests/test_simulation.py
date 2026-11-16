import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from simulation import (NUM_ORDERS, SURGE_SIZE, SURGE_TICK, find_path,
                        make_orders, obstacles, run_simulation)


def order_tuples(orders):
    result = []
    for order in orders:
        result.append((order.id, order.arrival, order.pickup, order.dropoff))
    return result


def test_path_goes_around_wall():
    path = find_path((0, 1), (9, 1))
    assert path[0] == (0, 1)
    assert path[-1] == (9, 1)
    for cell in path:
        assert cell not in obstacles
    for i in range(len(path) - 1):
        step = abs(path[i][0] - path[i + 1][0]) + abs(path[i][1] - path[i + 1][1])
        assert step == 1
    assert len(path) - 1 > 8


def test_same_seed_gives_same_orders():
    first = order_tuples(make_orders(7, False))
    second = order_tuples(make_orders(7, False))
    other = order_tuples(make_orders(8, False))
    assert first == second
    assert first != other


def test_surge_orders_arrive_together():
    orders = make_orders(3, True)
    at_surge = 0
    for order in orders:
        if order.arrival == SURGE_TICK:
            at_surge = at_surge + 1
    assert len(orders) == NUM_ORDERS
    assert at_surge >= SURGE_SIZE


def test_every_order_is_delivered_and_battery_stays_valid():
    for seed in range(1, 6):
        for surge in [False, True]:
            orders = make_orders(seed, surge)
            for strategy in ["naive", "smart"]:
                result = run_simulation(strategy, orders)
                assert result["completed"] == NUM_ORDERS
                assert result["min_battery"] >= 0


def test_runs_are_repeatable():
    orders = make_orders(4, True)
    first = run_simulation("smart", orders)
    second = run_simulation("smart", orders)
    assert first["avg_time"] == second["avg_time"]
    assert first["worst_time"] == second["worst_time"]
    assert first["empty"] == second["empty"]


tests_to_run = [
    test_path_goes_around_wall,
    test_same_seed_gives_same_orders,
    test_surge_orders_arrive_together,
    test_every_order_is_delivered_and_battery_stays_valid,
    test_runs_are_repeatable,
]

for test in tests_to_run:
    test()
    print("passed:", test.__name__)

print("All", len(tests_to_run), "tests passed")
