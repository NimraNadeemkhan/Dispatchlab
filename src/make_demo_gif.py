import csv
import os
import random
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.lines import Line2D

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


def run_with_history(strategy, orders):
    robots = []
    for i in range(4):
        robots.append(Robot("R" + str(i + 1), START_POSITIONS[i]))

    arrival = {}
    for order in orders:
        arrival[order.id] = order.arrival

    queue = []
    done_times = {}
    stats = {"empty": 0}
    next_order = 0
    tick = 0
    history = []

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

        total = 0
        for order_id in done_times:
            total = total + (done_times[order_id] - arrival[order_id])
        if len(done_times) > 0:
            avg = total / len(done_times)
        else:
            avg = 0

        snapshot_robots = []
        for robot in robots:
            snapshot_robots.append((robot.name, robot.position, robot.state, robot.battery))
        snapshot_waiting = []
        for order in queue:
            snapshot_waiting.append(order.pickup)

        history.append({
            "tick": tick,
            "robots": snapshot_robots,
            "waiting": snapshot_waiting,
            "delivered": len(done_times),
            "avg": avg,
        })

    return history


STATE_COLORS = {
    "idle": "gray",
    "to_pickup": "tab:blue",
    "to_dropoff": "tab:orange",
    "to_dock": "tab:green",
    "charging": "limegreen",
}


def draw_panel(ax, snapshot, title):
    ax.clear()
    ax.set_xlim(0, GRID_SIZE)
    ax.set_ylim(0, GRID_SIZE)
    ax.set_xticks(range(GRID_SIZE + 1))
    ax.set_yticks(range(GRID_SIZE + 1))
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.grid(True, color="lightgray", linewidth=0.5)
    ax.set_aspect("equal")

    for ox, oy in obstacles:
        ax.add_patch(plt.Rectangle((ox, oy), 1, 1, color="black"))
    ax.add_patch(plt.Rectangle(DOCK, 1, 1, color="palegreen"))
    ax.text(DOCK[0] + 0.5, DOCK[1] + 0.5, "Dock", ha="center", va="center", fontsize=7)

    counts = {}
    for cell in snapshot["waiting"]:
        counts[cell] = counts.get(cell, 0) + 1
    for cell in counts:
        ax.add_patch(plt.Rectangle((cell[0] + 0.15, cell[1] + 0.15), 0.7, 0.7,
                                   color="tomato"))
        ax.text(cell[0] + 0.5, cell[1] + 0.5, str(counts[cell]), ha="center",
                va="center", fontsize=8, color="white")

    for name, position, state, battery in snapshot["robots"]:
        ax.plot(position[0] + 0.5, position[1] + 0.5, "o",
                color=STATE_COLORS[state], markersize=17,
                markeredgecolor="black", markeredgewidth=0.8)
        ax.text(position[0] + 0.5, position[1] + 0.5, name, ha="center",
                va="center", fontsize=6, color="white", fontweight="bold")
        ax.text(position[0] + 0.5, position[1] + 0.05, str(battery) + "%", ha="center",
                va="top", fontsize=6)

    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("Delivered: " + str(snapshot["delivered"]) + "/" + str(NUM_ORDERS)
                  + "   Waiting: " + str(len(snapshot["waiting"]))
                  + "   Avg delivery time: " + str(round(snapshot["avg"], 1)),
                  fontsize=9)


DEMO_SEED = 1
DEMO_SURGE = True

orders = make_orders(DEMO_SEED, DEMO_SURGE)
naive_history = run_with_history("naive", orders)
smart_history = run_with_history("smart", orders)

total_frames = max(len(naive_history), len(smart_history))
frame_ticks = list(range(0, total_frames, 2))
for i in range(12):
    frame_ticks.append(total_frames - 1)


def get_snapshot(history, index):
    if index >= len(history):
        index = len(history) - 1
    return history[index]


fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(9.6, 5.4))

legend_items = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor="gray", markeredgecolor="black", markersize=9, label="Idle"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="tab:blue", markeredgecolor="black", markersize=9, label="To pickup"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="tab:orange", markeredgecolor="black", markersize=9, label="Carrying order"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="tab:green", markeredgecolor="black", markersize=9, label="To dock / charging"),
    Line2D([0], [0], marker="s", color="w", markerfacecolor="tomato", markersize=9, label="Waiting orders"),
]
fig.legend(handles=legend_items, loc="lower center", ncol=5, fontsize=8, frameon=False)
fig.suptitle("Same orders, same robots: naive vs smart dispatch (example run, seed "
             + str(DEMO_SEED) + ", order surge)", fontsize=11)
fig.subplots_adjust(bottom=0.14, top=0.88, wspace=0.12)


def update(index):
    draw_panel(ax_left, get_snapshot(naive_history, index), "Naive")
    draw_panel(ax_right, get_snapshot(smart_history, index), "Smart")


animation = FuncAnimation(fig, update, frames=frame_ticks, interval=100)

os.makedirs("docs", exist_ok=True)
animation.save("docs/demo.gif", writer=PillowWriter(fps=10), dpi=70)

print("Naive finished all orders in", len(naive_history), "steps")
print("Smart finished all orders in", len(smart_history), "steps")
print("Final avg delivery time - naive:", round(naive_history[-1]["avg"], 1),
      "| smart:", round(smart_history[-1]["avg"], 1))
print("Saved docs/demo.gif")
