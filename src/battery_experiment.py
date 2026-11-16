import csv
import os

from simulation import make_orders, run_simulation

NUM_SEEDS = 30
WEIGHTS_TO_TEST = [0, 0.1, 0.5, 1.0, 2.0]


def average(values):
    return sum(values) / len(values)


scenarios = ["normal", "surge"]
rows = []

for scenario in scenarios:
    naive_times = []
    for seed in range(1, NUM_SEEDS + 1):
        orders = make_orders(seed, scenario == "surge")
        r = run_simulation("naive", orders)
        naive_times.append(r["avg_time"])
        rows.append([scenario, "naive", "-", seed, round(r["avg_time"], 2),
                     r["worst_time"], r["empty"], ""])

    for weight in WEIGHTS_TO_TEST:
        for seed in range(1, NUM_SEEDS + 1):
            orders = make_orders(seed, scenario == "surge")
            r = run_simulation("smart", orders, battery_weight=weight)
            wins = 1 if r["avg_time"] < naive_times[seed - 1] else 0
            rows.append([scenario, "smart", weight, seed, round(r["avg_time"], 2),
                         r["worst_time"], r["empty"], wins])

os.makedirs("results", exist_ok=True)
with open("results/weight_experiment.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["scenario", "strategy", "battery_weight", "seed",
                     "avg_delivery_time", "worst_delivery_time", "empty_energy",
                     "beat_naive"])
    writer.writerows(rows)

print("Battery weight experiment,", NUM_SEEDS, "seeds per setting")
print()
for scenario in scenarios:
    print("Scenario:", scenario)

    times = []
    worsts = []
    empties = []
    for row in rows:
        if row[0] == scenario and row[1] == "naive":
            times.append(row[4])
            worsts.append(row[5])
            empties.append(row[6])
    print("  naive          | avg time:", round(average(times), 1),
          "| worst:", round(average(worsts), 1),
          "| empty energy:", round(average(empties), 1))

    for weight in WEIGHTS_TO_TEST:
        times = []
        worsts = []
        empties = []
        wins = 0
        for row in rows:
            if row[0] == scenario and row[1] == "smart" and row[2] == weight:
                times.append(row[4])
                worsts.append(row[5])
                empties.append(row[6])
                wins = wins + row[7]
        print("  smart weight", weight, "| avg time:", round(average(times), 1),
              "| worst:", round(average(worsts), 1),
              "| empty energy:", round(average(empties), 1),
              "| beat naive:", wins, "of", NUM_SEEDS)
    print()

print("Saved results/weight_experiment.csv")
