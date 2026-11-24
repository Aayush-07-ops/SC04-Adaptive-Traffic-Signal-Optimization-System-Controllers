# SC04 - Adaptive Traffic Signal Optimization System

> Soft Computing Capstone | Team: **[CONTROLLERS]** | Course/Section: **[B.Tech CSE(AI), SECTION 32]**

## One-sentence problem
Given queues, density, waiting time, and emergency direction, choose the next phase and green duration.

## What this project is
A small traffic-junction simulator for **one simple two-phase junction** (North-South = NS, East-West = EW).
The app will choose which direction gets green and for how long, using queue and waiting-time information.

- **User:** a traffic operator studying one simple two-phase junction.
- **Baseline (Step 1):** a fixed-time signal (30 s NS, 30 s EW, alternating).
- **M1 method:** a fuzzy controller compared with the fixed-time signal.
- **M2 method:** Genetic Algorithm (GA) tuning of the controller, emergency and heavy-queue testing, deployed simulator.


These are *first* responsibilities, not permanent silos. Every member must be able to explain all of Step 1.

## Project path (eight steps)
| Step | Stage | What happens | Status |
|---|---|---|---|
| 1 | M1 | Define one simple two-phase junction | **In progress** |
| 2 | M1 | Generate and validate traffic states (10,000+) | Not started |
| 3 | M1 | Build the fixed-time signal and queue updates | Not started |
| 4 | M1 | Build fuzzy phase priority and green duration | Not started |
| 5 | M1 | Create the working junction Product V1 | Not started |
| 6 | M2 | Use GA to tune controller parameters | Not started |
| 7 | M2 | Compare controllers in difficult traffic cases | Not started |
| 8 | M2 | Deploy Product V2 and finish all evidence | Not started |

## Repository layout
```
README.md                  <- you are here
requirements.txt           <- Python packages
docs/STEP-1.md             <- Step 1 project contract
docs/baseline-pseudocode.md
docs/test-cases.md         <- five mandatory cases + one invalid case
docs/product-v1-sketch.png <- Product V1 screen sketch
docs/git-workflow.md       <- commit plan and Git help
docs/faculty-demo-script.md
data/README.md             <- field meanings, units, sources, assumptions
data/sample_input.csv      <- 20 valid starter rows
data/invalid_input.csv     <- deliberately wrong row (kept separate)
src/validate_data.py       <- data validator
src/baseline.py            <- tiny runnable fixed-time baseline
notebooks/  app/  report/  <- used in later steps
results/step1/             <- validation logs, baseline output, screenshots
```

## How to run (from a fresh clone)
```bash
git clone <REPOSITORY-URL>
cd <REPOSITORY-NAME>
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# macOS/Linux:         source .venv/bin/activate
pip install -r requirements.txt

python src/validate_data.py                                         # expect: PASS
python src/validate_data.py --file data/invalid_input.csv --expect-fail   # expect: EXPECTED FAIL
python src/baseline.py                                              # prints baseline decisions
```

## Honest data statement
All Step 1 rows are **hand-written teaching/test values, not real measured traffic data.**
The 10,000+ records required later will come from a reproducible simulator (Step 2) and will be labelled as simulated.

## Step 1 checklist
See `docs/STEP-1.md` -> "Step 1 completion evidence".
