from collections import deque
import matplotlib.pyplot as plt

GRID_SIZE = 10

obstacles = []
for y in range(8):
    obstacles.append((4, y))


class Robot:
    def __init__(self, name, position, goal, color):
        self.name = name
        self.position = position
        self.goal = goal
        self.color = color
        self.battery = 100
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
    labels = []
    for robot in robots:
        ax.plot(robot.goal[0] + 0.5, robot.goal[1] + 0.5, "*",
                color=robot.color, markersize=20)
        ax.plot(robot.position[0] + 0.5, robot.position[1] + 0.5, "o",
                color=robot.color, markersize=18)
        ax.text(robot.position[0] + 0.5, robot.position[1] + 0.5, robot.name,
                color="white", ha="center", va="center", fontsize=8)
        labels.append(robot.name + ": " + str(robot.battery) + "%")
    ax.set_xlabel("   ".join(labels))


robots = [
    Robot("R1", (0, 1), (9, 1), "blue"),
    Robot("R2", (0, 3), (9, 3), "orange"),
    Robot("R3", (0, 5), (9, 5), "green"),
    Robot("R4", (0, 7), (9, 7), "purple"),
]

for robot in robots:
    robot.path = find_path(robot.position, robot.goal, obstacles)

longest = 0
for robot in robots:
    if len(robot.path) > longest:
        longest = len(robot.path)

fig, ax = plt.subplots(figsize=(7, 7))
draw_floor(ax, robots, 0)
plt.pause(0.5)

collisions = 0
for step in range(1, longest):
    for robot in robots:
        if step < len(robot.path):
            robot.move_to(robot.path[step])

    for i in range(len(robots)):
        for j in range(i + 1, len(robots)):
            if robots[i].position == robots[j].position:
                collisions = collisions + 1
                print("Step", step, ":", robots[i].name, "and", robots[j].name,
                      "share cell", robots[i].position)

    draw_floor(ax, robots, step)
    plt.pause(0.15)

print("Steps taken:", longest - 1)
for robot in robots:
    print(robot.name, "finished with battery:", robot.battery)
print("Total collisions:", collisions)
plt.show()
