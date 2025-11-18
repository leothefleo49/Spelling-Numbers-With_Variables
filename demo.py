"""
Demo script to show how the spelling calculator works
"""
from number_to_words import number_to_words
from spelling_parser import SpellingParser

print("=" * 70)
print("SPELLING NUMBERS WITH VARIABLES - DEMO")
print("=" * 70)
print()

# Demo 1: Number to words conversion
print("DEMO 1: Converting Numbers to Words")
print("-" * 70)

demo_numbers = [1, 5, 23, 100, 300, -1, -45, 1234]
for num in demo_numbers:
    print(f"{num:6d} → {number_to_words(num)}")

print()
input("Press Enter to continue...")
print()

# Demo 2: Parsing with default letter values (all = 1.0)
print("DEMO 2: Parsing with Default Letter Values (all letters = 1.0)")
print("-" * 70)

parser = SpellingParser()

test_cases = [
    (1, "Simple number"),
    (23, "Addition example (TWENTY + THREE)"),
    (100, "Multiplication example (ONE × HUNDRED)"),
    (-1, "Negative number"),
]

for num, description in test_cases:
    spelling = number_to_words(num)
    value, explanation = parser.calculate_spelled_value(spelling)
    error = (value - num) ** 2
    
    print(f"\n{num}: {spelling}")
    print(f"Description: {description}")
    print(f"Calculation: {explanation}")
    print(f"Target: {num}, Spelled Value: {value:.2f}, Error: {error:.2f}")

print()
input("Press Enter to continue...")
print()

# Demo 3: Custom letter values
print("DEMO 3: Custom Letter Values")
print("-" * 70)
print()
print("Let's try to solve ONE = 1")
print("We need O × N × E = 1")
print()

# Custom values that solve ONE = 1
custom_values = {chr(65 + i): 1.0 for i in range(26)}
custom_values['O'] = 2.0
custom_values['N'] = 0.5
custom_values['E'] = 1.0

parser.set_letter_values(custom_values)

spelling = number_to_words(1)
value, explanation = parser.calculate_spelled_value(spelling)

print(f"Letter values: O=2.0, N=0.5, E=1.0")
print(f"Spelling: {spelling}")
print(f"Calculation: O × N × E = 2.0 × 0.5 × 1.0 = {value:.2f}")
print(f"Target: 1")
print(f"Success: {abs(value - 1) < 0.01}")

print()
print("=" * 70)
print("Now you understand the concept!")
print("The full application uses AI to find optimal letter values")
print("that solve as many numbers as possible in your chosen range.")
print("=" * 70)
print()
print("To run the full application:")
print("  - Windows: run.bat")
print("  - Linux/Mac: python3 run.py")
print("  - Or directly: py app.py (Windows) / python3 app.py (Linux/Mac)")
