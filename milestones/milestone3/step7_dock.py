from collections import deque
import matplotlib.pyplot as plt

GRID_SIZE = 10
DOCK = (0, 9)
LOW_BATTERY = 40

obstacles = []
for y in range(8):
    obstacles.append((4, y))


class Robot:
    def __init__(self, name, position, goal, color, battery):
        self.name = name
        self.position = position
        self.goal = goal
        self.color = color
        self.battery = battery
        self.state = "to_goal"
        self.path = []

    def move_to(self, cell):
        self.position = cell
        self.battery = self.battery - 2


def find_path(start, goal, obstacles):
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

    if goal not in came_from:
        return None

    path = []
    cell = goal
    while cell is not None:
        path.append(cell)
        cell = came_from[cell]
    path.reverse()
    return path


def update_robot(robot, step):
    if robot.state == "done":
        return

    if robot.state == "charging":
        robot.battery = min(100, robot.battery + 10)
        if robot.battery == 100:
            robot.state = "to_goal"
            robot.path = find_path(robot.position, robot.goal, obstacles)[1:]
            print("Step", step, ":", robot.name, "fully charged, back to work")
        return

    if robot.state == "to_goal" and robot.battery < LOW_BATTERY:
        robot.state = "to_dock"
        robot.path = find_path(robot.position, DOCK, obstacles)[1:]
        print("Step", step, ":", robot.name, "battery low (" + str(robot.battery) + "%), heading to dock")

    if len(robot.path) > 0:
        cell = robot.path.pop(0)
        robot.move_to(cell)

    if len(robot.path) == 0:
        if robot.state == "to_dock":
            robot.state = "charging"
            print("Step", step, ":", robot.name, "arrived at dock, charging")
        elif robot.state == "to_goal":
            robot.state = "done"
            print("Step", step, ":", robot.name, "delivered, battery", robot.battery)


def all_done(robots):
    for robot in robots:
        if robot.state != "done":
            return False
    return True


def draw_floor(ax, robots, step):
    ax.clear()
    ax.set_xlim(0, GRID_SIZE)
    ax.set_ylim(0, GRID_SIZE)
    ax.set_xticks(range(GRID_SIZE + 1))
    ax.set_yticks(range(GRID_SIZE + 1))
    ax.grid(True)
    ax.set_aspect("equal")
    ax.set_title("Warehouse Floor - step " + str(step))
    for ox, oy in obstacles:
        ax.add_patch(plt.Rectangle((ox, oy), 1, 1, color="black"))
    ax.add_patch(plt.Rectangle(DOCK, 1, 1, color="lightgreen"))
    ax.text(DOCK[0] + 0.5, DOCK[1] + 0.5, "Dock", ha="center", va="center", fontsize=8)
    labels = []
    for robot in robots:
        ax.plot(robot.goal[0] + 0.5, robot.goal[1] + 0.5, "*",
                color=robot.color, markersize=20)
        ax.plot(robot.position[0] + 0.5, robot.position[1] + 0.5, "o",
                color=robot.color, markersize=18)
        ax.text(robot.position[0] + 0.5, robot.position[1] + 0.5, robot.name,
                color="white", ha="center", va="center", fontsize=8)
        labels.append(robot.name + ": " + str(robot.battery) + "% " + robot.state)
    ax.set_xlabel("   ".join(labels[:2]) + "\n" + "   ".join(labels[2:]))


robots = [
    Robot("R1", (0, 1), (9, 1), "blue", 100),
    Robot("R2", (0, 3), (9, 3), "orange", 70),
    Robot("R3", (0, 5), (9, 5), "green", 45),
    Robot("R4", (0, 7), (9, 7), "purple", 38),
]

for robot in robots:
    robot.path = find_path(robot.position, robot.goal, obstacles)[1:]

fig, ax = plt.subplots(figsize=(7, 7.5))
draw_floor(ax, robots, 0)
plt.pause(0.5)

step = 0
while not all_done(robots) and step < 200:
    step = step + 1
    for robot in robots:
        update_robot(robot, step)
    draw_floor(ax, robots, step)
    plt.pause(0.15)

print("All deliveries finished in", step, "steps")
for robot in robots:
    print(robot.name, "final battery:", robot.battery)
plt.show()
