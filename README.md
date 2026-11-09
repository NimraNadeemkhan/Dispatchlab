# Dispatchlab

A warehouse robot fleet simulator in Python. It tests one question: **does battery- and distance-aware dispatch outperform first-come, first-served dispatch, and when?**

> **Status:** work in progress (week 1 build). Results will be added once the comparison has been run.

---

## The question

Warehouses and delivery zones run fleets of robots. The hard part is deciding which robot takes which order, when to charge, and how to avoid blocked aisles. DispatchLab simulates that problem on a 2D grid and compares two dispatch strategies under identical conditions.

| Strategy | How it assigns an order |
|---|---|
| **Naive** | Gives the order to the next free robot (first come, first served) |
| **Smart** | Scores each robot on distance to the pickup and remaining battery, then picks the best |

## How the comparison will be kept fair

- Both strategies run on the **same seeded sequence of orders**.
- Each scenario is **repeated over many runs** and averaged, not judged from a single run.
- Results will report **orders per hour, average delivery time, and energy wasted**, including cases where the gap is small or the smart strategy loses.

## What's in the simulation

- A grid warehouse with shelves, a pickup zone, a drop-off bay, and a charging dock
- Four robots that carry orders, drain battery as they move, and return to charge
- Obstacles that block aisles, with robots recalculating a route around them
- An order queue, including sudden surges of orders

## Progress

| Milestone | Goal | Status |
|---|---|---|
| 1 | Draw a grid and move one robot | Done |
| 2 | Block an aisle and reroute around it | Done |
| 3 | Four robots, battery drain, charging dock | Next |
| 4 | Order queue, naive and smart dispatch, metrics | Planned |
| 5 | Run the comparison and write up results | Planned |

## Run it

Requires Python 3.9 or newer.

```bash
git clone https://github.com/NimraNadeemkhan/dispatchlab.git
cd dispatchlab
pip install -r requirements.txt
python milestones/milestone1/step2.py
```

You should see a robot move across a 10x10 grid from the green start square to the red goal.

## Project structure

```text
dispatchlab/
|-- README.md
|-- requirements.txt
|-- milestones/        # step-by-step learning history
|   `-- milestone1/    # grid drawing and one moving robot
|-- src/               # the simulation (added as it is built)
|-- results/           # comparison outputs (added after the runs)
`-- docs/              # screenshots and notes
```

## Design decisions and limitations

- It is a **simplified 2D grid simulation**, not a model of a real warehouse or real robot hardware.
- The battery model uses **simple assumed drain rates**, not measured values.
- Robot-to-robot conflicts are handled with a basic wait-or-reroute rule. Full deadlock avoidance is out of scope for the first version.
- Fleet-management systems such as Open-RMF solve the same kind of problem at a much larger scale. This project is a learning-scale version of the idea.

## Possible next steps

- A* pathfinding in place of the first search method
- A heat-aware mode where hot conditions change battery drain and dispatch choices
- A browser-based version of the simulation

## About

Built by Nimra Nadeem, a Business Systems Engineer based in the UAE, as a first step toward robotics and logistics automation work.

## License

MIT
