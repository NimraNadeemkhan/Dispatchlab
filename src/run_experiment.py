import csv
import os

import matplotlib.pyplot as plt

from simulation import make_orders, run_simulation

NUM_SEEDS = 30


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
