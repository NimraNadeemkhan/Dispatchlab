import os

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.lines import Line2D

from simulation import (DOCK, GRID_SIZE, NUM_ORDERS, make_orders, obstacles,
                        run_simulation)

DEMO_SEED = 1
DEMO_SURGE = True

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


def get_snapshot(history, index):
    if index >= len(history):
        index = len(history) - 1
    return history[index]


orders = make_orders(DEMO_SEED, DEMO_SURGE)
naive_history = run_simulation("naive", orders, keep_history=True)["history"]
smart_history = run_simulation("smart", orders, keep_history=True)["history"]

total_frames = max(len(naive_history), len(smart_history))
frame_ticks = list(range(0, total_frames, 2))
for i in range(12):
    frame_ticks.append(total_frames - 1)

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
