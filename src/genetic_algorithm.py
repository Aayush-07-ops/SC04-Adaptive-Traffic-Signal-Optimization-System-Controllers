
import random
import json
from pathlib import Path

import pandas as pd

from benchmark import run_benchmark
from fuzzy_controller import DEFAULT_PARAMS


# ---------------------------------------
# GA CONFIGURATION
# ---------------------------------------

POPULATION_SIZE = 12
GENERATIONS = 8
MUTATION_RATE = 0.20
ELITE_COUNT = 2

SEEDS = [42, 123, 456]


# ---------------------------------------
# CHROMOSOME CREATION
# ---------------------------------------

def create_individual():
    """Generate one random fuzzy parameter set."""

    return {
        "q_low_end": random.randint(25, 55),

        "q_med_left": random.randint(10, 35),
        "q_med_peak": random.randint(35, 65),
        "q_med_right": random.randint(65, 90),

        "q_high_start": random.randint(45, 75),

        "w_short_end": random.randint(90, 180),

        "w_med_left": random.randint(30, 100),
        "w_med_peak": random.randint(100, 190),
        "w_med_right": random.randint(190, 270),

        "w_long_start": random.randint(100, 220),

        "min_green": random.randint(10, 30),
        "max_green": random.randint(40, 70)
    }


# ---------------------------------------
# VALIDATE / REPAIR CHROMOSOME
# ---------------------------------------

def repair(individual):

    p = individual.copy()

    # Queue membership boundaries
    p["q_low_end"] = max(
        20, min(60, p["q_low_end"])
    )

    q_values = sorted([
        p["q_med_left"],
        p["q_med_peak"],
        p["q_med_right"]
    ])

    p["q_med_left"] = max(
        5, min(40, q_values[0])
    )

    p["q_med_peak"] = max(
        p["q_med_left"] + 10,
        min(75, q_values[1])
    )

    p["q_med_right"] = max(
        p["q_med_peak"] + 10,
        min(95, q_values[2])
    )

    p["q_high_start"] = max(
        40, min(85, p["q_high_start"])
    )

    # Waiting-time membership boundaries
    p["w_short_end"] = max(
        60, min(200, p["w_short_end"])
    )

    w_values = sorted([
        p["w_med_left"],
        p["w_med_peak"],
        p["w_med_right"]
    ])

    p["w_med_left"] = max(
        10, min(120, w_values[0])
    )

    p["w_med_peak"] = max(
        p["w_med_left"] + 20,
        min(220, w_values[1])
    )

    p["w_med_right"] = max(
        p["w_med_peak"] + 20,
        min(290, w_values[2])
    )

    p["w_long_start"] = max(
        80, min(250, p["w_long_start"])
    )

    # Green-time constraints
    p["min_green"] = max(
        10, min(30, p["min_green"])
    )

    p["max_green"] = max(
        p["min_green"] + 10,
        min(70, p["max_green"])
    )
    

    return p


# ---------------------------------------
# FITNESS FUNCTION
# ---------------------------------------

def fitness(individual):

    individual = repair(individual)

    scores = []

    for seed in SEEDS:

        result, _ = run_benchmark(
            controller="fuzzy",
            duration=600,
            initial_ns=30,
            initial_ew=6,
            arrival_ns=0.20,
            arrival_ew=0.20,
            service_rate=0.50,
            seed=seed,
            fuzzy_params=individual
        )

        # Lower fitness is better
        score = (
            result["average_wait_sec"]
            + 2.0 * result["vehicles_remaining"]
            + 0.5 * (
                result["max_queue_ns"]
                + result["max_queue_ew"]
            )
        )

        scores.append(score)

    return sum(scores) / len(scores)


# ---------------------------------------
# SELECTION
# ---------------------------------------

def tournament_selection(population, fitnesses):

    candidates = random.sample(
        range(len(population)),
        3
    )

    winner = min(
        candidates,
        key=lambda i: fitnesses[i]
    )

    return population[winner].copy()


# ---------------------------------------
# CROSSOVER
# ---------------------------------------

def crossover(parent1, parent2):

    child = {}

    for key in parent1:

        if random.random() < 0.5:
            child[key] = parent1[key]
        else:
            child[key] = parent2[key]

    return repair(child)


# ---------------------------------------
# MUTATION
# ---------------------------------------

def mutate(individual):

    child = individual.copy()

    for key in child:

        if random.random() < MUTATION_RATE:

            if key.startswith("q_"):
                child[key] += random.randint(-10, 10)

            elif key.startswith("w_"):
                child[key] += random.randint(-30, 30)

            elif key == "min_green":
                child[key] += random.randint(-5, 5)

            elif key == "max_green":
                child[key] += random.randint(-10, 10)

    return repair(child)


# ---------------------------------------
# MAIN GENETIC ALGORITHM
# ---------------------------------------

def run_genetic_algorithm():

    random.seed(42)

    population = [
        repair(create_individual())
        for _ in range(POPULATION_SIZE)
    ]

    best_individual = None
    best_fitness = float("inf")

    history = []

    for generation in range(GENERATIONS):

        print(
            f"\nGeneration {generation + 1}"
            f"/{GENERATIONS}"
        )

        fitnesses = [
            fitness(individual)
            for individual in population
        ]

        generation_best_index = min(
            range(len(population)),
            key=lambda i: fitnesses[i]
        )

        generation_best = population[
            generation_best_index
        ].copy()

        generation_score = fitnesses[
            generation_best_index
        ]

        if generation_score < best_fitness:

            best_fitness = generation_score
            best_individual = generation_best.copy()

        history.append({
            "generation": generation + 1,
            "best_fitness": generation_score,
            "overall_best_fitness": best_fitness
        })

        print("Best fitness:", round(
            generation_score, 2
        ))

        print("Overall best:", round(
            best_fitness, 2
        ))

        # Elitism: keep the best individuals
        ranked = sorted(
            range(len(population)),
            key=lambda i: fitnesses[i]
        )

        new_population = [
            population[i].copy()
            for i in ranked[:ELITE_COUNT]
        ]

        # Create remaining population
        while len(new_population) < POPULATION_SIZE:

            parent1 = tournament_selection(
                population, fitnesses
            )

            parent2 = tournament_selection(
                population, fitnesses
            )

            child = crossover(
                parent1, parent2
            )

            child = mutate(child)

            new_population.append(child)

        population = new_population

    # Save optimized parameters
    results_dir = Path("results")
    results_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output = {
        "best_fitness": best_fitness,
        "parameters": best_individual
    }

    with open(
        results_dir / "ga_best_params.json",
        "w"
    ) as file:

        json.dump(
            output,
            file,
            indent=4
        )

    pd.DataFrame(history).to_csv(
        results_dir / "ga_history.csv",
        index=False
    )

    print("\nOPTIMIZATION COMPLETED")

    print("Best fitness:", round(
        best_fitness, 2
    ))

    print("\nBest parameters:")

    for key, value in best_individual.items():
        print(f"{key}: {value}")

    print(
        "\nSaved to results/ga_best_params.json"
    )

    return best_individual, history


if __name__ == "__main__":

    run_genetic_algorithm()