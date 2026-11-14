import csv
import os
import random
from collections import deque

import matplotlib.pyplot as plt

GRID_SIZE = 10
DOCK = (3, 9)
LOW_BATTERY = 50
STATIONS = [(0, 1), (0, 3), (0, 5), (0, 7), (9, 1), (9, 3), (9, 5), (9, 7)]
START_POSITIONS = [(0, 1), (0, 5), (9, 1), (9, 5)]
NUM_ORDERS = 30
LAST_ARRIVAL = 150
SURGE_SIZE = 15
SURGE_TICK = 50
MAX_TICKS = 1000
NUM_SEEDS = 30

obstacles = []
for y in range(8):
    obstacles.append((4, y))


class Order:
    def __init__(self, order_id, arrival, pickup, dropoff):
        self.id = order_id
        self.arrival = arrival
        self.pickup = pickup
        self.dropoff = dropoff


class Robot:
    def __init__(self, name, position):
        self.name = name
        self.position = position
        self.battery = 100
        self.state = "idle"
        self.path = []
        self.order = None


def find_path(start, goal):
    queue = deque([start])
    came_from = {start: None}

    while queue:
        current = queue.popleft()
        if current == goal:
            break
        x, y = current
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            neighbor = (x + dx, y + dy)
            if neighbor[0] < 0 or neighbor[0] >= GRID_SIZE:
                continue
            if neighbor[1] < 0 or neighbor[1] >= GRID_SIZE:
                continue
            if neighbor in obstacles:
                continue
            if neighbor in came_from:
                continue
            came_from[neighbor] = current
            queue.append(neighbor)

    path = []
    cell = goal
    while cell is not None:
        path.append(cell)
        cell = came_from[cell]
    path.reverse()
    return path


distance_cache = {}


def distance(a, b):
    key = (a, b)
    if key not in distance_cache:
        distance_cache[key] = len(find_path(a, b)) - 1
    return distance_cache[key]


def make_orders(seed, surge):
    rng = random.Random(seed)
    arrivals = []
    for i in range(NUM_ORDERS):
        if surge and i >= NUM_ORDERS - SURGE_SIZE:
            arrivals.append(SURGE_TICK)
        else:
            arrivals.append(rng.randint(0, LAST_ARRIVAL))
    arrivals.sort()

    orders = []
    for i in range(NUM_ORDERS):
        pickup = rng.choice(STATIONS)
        dropoff = rng.choice(STATIONS)
        while dropoff == pickup:
            dropoff = rng.choice(STATIONS)
        orders.append(Order(i, arrivals[i], pickup, dropoff))
    return orders


def can_do(robot, order):
    cost = (distance(robot.position, order.pickup)
            + distance(order.pickup, order.dropoff)
            + distance(order.dropoff, DOCK))
    return robot.battery >= cost


def score(robot, order):
    return distance(robot.position, order.pickup) + (100 - robot.battery) * 0.1


def choose_robot(strategy, order, robots):
    candidates = []
    for robot in robots:
        if robot.state == "idle" and can_do(robot, order):
            candidates.append(robot)

    if len(candidates) == 0:
        return None

    if strategy == "naive":
        return candidates[0]

    best = candidates[0]
    for robot in candidates:
        if score(robot, order) < score(best, order):
            best = robot
    return best


def send(robot, target, state):
    robot.state = state
    robot.path = find_path(robot.position, target)[1:]


def arrive(robot, tick, done_times):
    if robot.state == "to_pickup":
        send(robot, robot.order.dropoff, "to_dropoff")
    elif robot.state == "to_dropoff":
        done_times[robot.order.id] = tick
        robot.order = None
        robot.state = "idle"
    elif robot.state == "to_dock":
        robot.state = "charging"


def step_robot(robot, stats, tick, done_times):
    if robot.state == "idle":
        return

    if robot.state == "charging":
        robot.battery = min(100, robot.battery + 10)
        if robot.battery == 100:
            robot.state = "idle"
        return

    if len(robot.path) > 0:
        robot.position = robot.path.pop(0)
        robot.battery = robot.battery - 1
        if robot.state != "to_dropoff":
            stats["empty"] = stats["empty"] + 1

    if len(robot.path) == 0:
        arrive(robot, tick, done_times)


def run_simulation(strategy, orders):
    robots = []
    for i in range(4):
        robots.append(Robot("R" + str(i + 1), START_POSITIONS[i]))

    queue = []
    done_times = {}
    stats = {"empty": 0}
    next_order = 0
    tick = 0

    while len(done_times) < len(orders) and tick < MAX_TICKS:
        while next_order < len(orders) and orders[next_order].arrival <= tick:
            queue.append(orders[next_order])
            next_order = next_order + 1

        for robot in robots:
            if robot.state == "idle" and robot.battery < LOW_BATTERY:
                send(robot, DOCK, "to_dock")

        waiting = []
        for order in queue:
            robot = choose_robot(strategy, order, robots)
            if robot is None:
                waiting.append(order)
            else:
                robot.order = order
                send(robot, order.pickup, "to_pickup")
        queue = waiting

        for robot in robots:
            step_robot(robot, stats, tick, done_times)

        tick = tick + 1

    total_time = 0
    worst_time = 0
    for order in orders:
        if order.id in done_times:
            delivery_time = done_times[order.id] - order.arrival
            total_time = total_time + delivery_time
            if delivery_time > worst_time:
                worst_time = delivery_time

    return {
        "completed": len(done_times),
        "avg_time": total_time / len(done_times),
        "worst_time": worst_time,
        "empty": stats["empty"],
    }


def average(values):
    return sum(values) / len(values)


scenarios = ["normal", "surge"]
strategies = ["naive", "smart"]
rows = []

for scenario in scenarios:
    for seed in range(1, NUM_SEEDS + 1):
        orders = make_orders(seed, scenario == "surge")
        for strategy in strategies:
            r = run_simulation(strategy, orders)
            rows.append([scenario, seed, strategy, r["completed"],
                         round(r["avg_time"], 2), r["worst_time"], r["empty"]])

os.makedirs("results", exist_ok=True)
with open("results/results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["scenario", "seed", "strategy", "completed",
                     "avg_delivery_time", "worst_delivery_time", "empty_energy"])
    writer.writerows(rows)

print("Results over", NUM_SEEDS, "seeds per scenario")
print()
summary = {}
for scenario in scenarios:
    print("Scenario:", scenario)
    for strategy in strategies:
        avg_times = []
        worst_times = []
        empties = []
        for row in rows:
            if row[0] == scenario and row[2] == strategy:
                avg_times.append(row[4])
                worst_times.append(row[5])
                empties.append(row[6])
        summary[(scenario, strategy)] = average(avg_times)
        print("  ", strategy, "| avg delivery time:", round(average(avg_times), 1),
              "| worst delivery time:", round(average(worst_times), 1),
              "| empty energy:", round(average(empties), 1))

    smart_wins = 0
    for seed in range(1, NUM_SEEDS + 1):
        naive_time = 0
        smart_time = 0
        for row in rows:
            if row[0] == scenario and row[1] == seed:
                if row[2] == "naive":
                    naive_time = row[4]
                else:
                    smart_time = row[4]
        if smart_time < naive_time:
            smart_wins = smart_wins + 1
    print("   smart had the lower avg delivery time in", smart_wins, "of", NUM_SEEDS, "seeds")
    print()

x_positions = [0, 1]
width = 0.35
fig, ax = plt.subplots(figsize=(6, 4))
naive_values = [summary[("normal", "naive")], summary[("surge", "naive")]]
smart_values = [summary[("normal", "smart")], summary[("surge", "smart")]]
ax.bar([p - width / 2 for p in x_positions], naive_values, width, label="Naive")
ax.bar([p + width / 2 for p in x_positions], smart_values, width, label="Smart")
ax.set_xticks(x_positions)
ax.set_xticklabels(["Normal orders", "Order surge"])
ax.set_ylabel("Average delivery time (steps)")
ax.set_title("Naive vs smart dispatch (" + str(NUM_SEEDS) + " seeds each)")
ax.legend()
plt.tight_layout()
plt.savefig("results/comparison.png", dpi=150)

print("Saved results/results.csv and results/comparison.png")
