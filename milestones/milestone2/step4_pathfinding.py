from collections import deque
import matplotlib.pyplot as plt

GRID_SIZE = 10
start = (0, 0)
goal = (9, 0)

obstacles = []
for y in range(8):
    obstacles.append((4, y))


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


path = find_path(start, goal, obstacles)

if path is None:
    print("No path found")
else:
    print("Path length:", len(path) - 1, "steps")
    print("A straight line would be:", abs(goal[0] - start[0]) + abs(goal[1] - start[1]), "steps")
    fig, ax = plt.subplots(figsize=(6, 6))
    for position in path:
        draw_floor(ax, position)
        plt.pause(0.15)
    plt.show()
