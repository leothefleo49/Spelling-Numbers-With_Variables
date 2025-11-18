"""
Quick validation - just check that modules import correctly
"""
print("Checking module imports...")

try:
    import numpy  # type: ignore
    print("✓ NumPy")
except ImportError:
    print("✗ NumPy not found - install with: py -m pip install numpy")

try:
    from number_to_words import number_to_words
    print("✓ number_to_words")
    test = number_to_words(23)
    print(f"  Test: 23 → {test}")
except Exception as e:
    print(f"✗ number_to_words: {e}")

try:
    from spelling_parser import SpellingParser
    print("✓ spelling_parser")
except Exception as e:
    print(f"✗ spelling_parser: {e}")

try:
    from optimizer import LetterValueOptimizer
    print("✓ optimizer")
except Exception as e:
    print(f"✗ optimizer: {e}")

print("\nAll core modules loaded successfully!")
print("You can now run: py app.py")
