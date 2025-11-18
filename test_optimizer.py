"""
Quick test of the optimizer
"""
from optimizer import LetterValueOptimizer

print("Testing Optimizer on range -5 to 5")
print("=" * 60)

optimizer = LetterValueOptimizer(-5, 5, population_size=30)

def progress_callback(stats):
    if stats['generation'] % 5 == 0:
        print(f"Gen {stats['generation']:3d}: "
              f"Solved {stats['solved_count']:2d}/{stats['total_numbers']:2d}, "
              f"Fitness: {stats['best_fitness']:8.2f}")

best_solution = optimizer.optimize(max_generations=30, callback=progress_callback)

print("\n" + "=" * 60)
print("Best Solution Found:")
print("=" * 60)

for letter, value in sorted(best_solution.items()):
    print(f"{letter}: {value:7.3f}")

details = optimizer.get_solution_details()
print(f"\nSolved {details['solved_count']} out of {details['total_count']} numbers")
