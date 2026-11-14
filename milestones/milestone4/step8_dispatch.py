import random
from collections import deque

GRID_SIZE = 10
DOCK = (3, 9)
LOW_BATTERY = 50
STATIONS = [(0, 1), (0, 3), (0, 5), (0, 7), (9, 1), (9, 3), (9, 5), (9, 7)]
START_POSITIONS = [(0, 1), (0, 5), (9, 1), (9, 5)]
NUM_ORDERS = 30
LAST_ARRIVAL = 150
MAX_TICKS = 1000

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


def make_orders(seed):
    rng = random.Random(seed)
    arrivals = []
    for i in range(NUM_ORDERS):
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
        stats["energy"] = stats["energy"] + 1
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
    stats = {"energy": 0, "empty": 0}
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
    for order in orders:
        if order.id in done_times:
            total_time = total_time + (done_times[order.id] - order.arrival)

    return {
        "completed": len(done_times),
        "avg_time": total_time / len(done_times),
        "finished_at": tick,
        "energy": stats["energy"],
        "empty": stats["empty"],
    }


seeds = [1, 2, 3, 4, 5]
totals = {"naive": [0, 0, 0], "smart": [0, 0, 0]}

print("seed | strategy | done | avg delivery time | finished at | empty energy")
for seed in seeds:
    orders = make_orders(seed)
    for strategy in ["naive", "smart"]:
        r = run_simulation(strategy, orders)
        print(seed, "|", strategy, "|", r["completed"], "|", round(r["avg_time"], 1),
              "|", r["finished_at"], "|", r["empty"])
        totals[strategy][0] = totals[strategy][0] + r["avg_time"]
        totals[strategy][1] = totals[strategy][1] + r["finished_at"]
        totals[strategy][2] = totals[strategy][2] + r["empty"]

print()
print("AVERAGE over", len(seeds), "seeds")
for strategy in ["naive", "smart"]:
    n = len(seeds)
    print(strategy, "| avg delivery time:", round(totals[strategy][0] / n, 1),
          "| finished at:", round(totals[strategy][1] / n, 1),
          "| empty energy:", round(totals[strategy][2] / n, 1))
