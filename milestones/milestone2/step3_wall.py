import matplotlib.pyplot as plt

GRID_SIZE = 10
start = (0, 0)
goal = (9, 0)

obstacles = []
for y in range(8):
    obstacles.append((4, y))


def make_path(start, goal):
    path = [start]
    x, y = start
    while x < goal[0]:
        x += 1
        path.append((x, y))
    while y < goal[1]:
        y += 1
        path.append((x, y))
    return path


def draw_floor(ax, robot_pos):
    ax.clear()
    ax.set_xlim(0, GRID_SIZE)
    ax.set_ylim(0, GRID_SIZE)
    ax.set_xticks(range(GRID_SIZE + 1))
    ax.set_yticks(range(GRID_SIZE + 1))
    ax.grid(True)
    ax.set_aspect("equal")
    ax.set_title("Warehouse Floor")
    for ox, oy in obstacles:
        ax.add_patch(plt.Rectangle((ox, oy), 1, 1, color="black"))
    ax.plot(start[0] + 0.5, start[1] + 0.5, "gs", markersize=20)
    ax.plot(goal[0] + 0.5, goal[1] + 0.5, "r*", markersize=25)
    ax.plot(robot_pos[0] + 0.5, robot_pos[1] + 0.5, "bo", markersize=18)


path = make_path(start, goal)

for cell in path:
    if cell in obstacles:
        print("Robot hits wall at", cell)

fig, ax = plt.subplots(figsize=(6, 6))
for position in path:
    draw_floor(ax, position)
    plt.pause(0.3)

plt.show()
