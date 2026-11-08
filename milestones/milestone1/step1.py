import matplotlib.pyplot as plt

GRID_SIZE = 10

fig, ax = plt.subplots(figsize=(6, 6))
ax.set_xlim(0, GRID_SIZE)
ax.set_ylim(0, GRID_SIZE)
ax.set_xticks(range(GRID_SIZE + 1))
ax.set_yticks(range(GRID_SIZE + 1))
ax.grid(True)
ax.set_aspect("equal")
ax.set_title("Warehouse Floor")
plt.show()
