# Spelling Numbers with Variables Calculator

An interactive application that finds optimal numerical values for each letter of the alphabet (A-Z) to "solve" number spellings within a specified range.

## Concept

Based on the YouTube video "Spelling Numbers with Variables" by Stand-up Maths, this app defines a "solved" number as one where the calculated value from its letters equals the number itself.

For example, if we find letter values where `O × N × E = 1`, then the number "ONE" is solved.

## Features

### Core Functionality

1. **Number-to-Words Conversion**: Converts any integer to its English word representation
   - Example: 23 → "TWENTY-THREE"
   - Example: -45 → "NEGATIVE FORTY-FIVE"
   - Example: 300 → "THREE HUNDRED"

2. **Smart Parsing with Multiplication & Addition Rules**:
   - **Multiplication Rule** (smallest-to-largest): "THREE HUNDRED" → (T×H×R×E×E) × (H×U×N×D×R×E×D)
   - **Addition Rule** (largest-to-smallest): "TWENTY-THREE" → (T×W×E×N×T×Y) + (T×H×R×E×E)

3. **AI Optimization Solver**:
   - Uses genetic algorithm to find 26 letter values
   - Minimizes total error across entire number range
   - Supports negative numbers (with NEGATIVE = -1 constraint)

4. **Interactive UI**:
   - Input screen for range configuration
   - Real-time progress monitoring during optimization
   - Results explorer to examine individual numbers
   - Export functionality for results

## Installation

### Requirements

- Python 3.7 or higher
- NumPy

### Setup

1. Install Python dependencies:
```bash
pip install numpy
```

2. Run the application:
```bash
python app.py
```

## Usage

### 1. Setup Screen

- **Start Range**: Enter the minimum number (e.g., -100)
- **End Range**: Enter the maximum number (e.g., 100)
- **Population Size**: Genetic algorithm population (higher = better results but slower)
- **Generations**: Number of optimization iterations (higher = better results but slower)
- Click "Start Calculation" to begin

### 2. Solving Screen

Watch the optimization progress in real-time:
- Generation counter
- Number of solved numbers
- Total fitness (error) score
- Detailed progress log
- Progress bar

You can stop the optimization at any time.

### 3. Results Screen

#### Letter Values Panel
View the optimal values found for each letter (A-Z)

#### Number Explorer
- Enter any number from your range
- See detailed breakdown:
  - Full spelling
  - Component breakdown with letter values
  - Step-by-step calculation
  - Final result vs target
  - Solved status

#### Export Results
Save all results to a text file for later analysis

## How It Works

### Number Parsing

The parser identifies components of a number spelling and applies rules:

**Example: 23 ("TWENTY-THREE")**
```
Components: TWENTY (20), THREE (3)
Rule: Largest-to-smallest → Addition
Calculation: (T×W×E×N×T×Y) + (T×H×R×E×E)
```

**Example: 300 ("THREE HUNDRED")**
```
Components: THREE (3), HUNDRED (100)
Rule: Smallest-to-largest → Multiplication
Calculation: (T×H×R×E×E) × (H×U×N×D×R×E×D)
```

### Optimization Algorithm

The genetic algorithm:
1. Creates a population of random letter value sets
2. Evaluates fitness (sum of squared errors)
3. Selects best performers
4. Creates new generation through crossover and mutation
5. Repeats until convergence or max generations

The algorithm encourages `N×E×G×A×T×I×V×E = -1` for handling negative numbers.

## File Structure

```
Spelling_Numbers_With_Variables_Calculator/
├── app.py                 # Main GUI application
├── number_to_words.py     # Number-to-words converter
├── spelling_parser.py     # Parsing and calculation logic
├── optimizer.py           # Genetic algorithm optimizer
├── README.md              # This file
└── requirements.txt       # Python dependencies
```

## Examples

### Quick Test (Small Range)
- Range: -10 to 10
- Population: 50
- Generations: 50
- Time: ~1-2 minutes

### Standard Test (Medium Range)
- Range: -100 to 100
- Population: 100
- Generations: 100
- Time: ~5-10 minutes

### Comprehensive Test (Large Range)
- Range: -1000 to 1000
- Population: 200
- Generations: 200
- Time: ~30-60 minutes

## Tips

1. **Start small**: Test with a small range first to understand the app
2. **Population size**: 100-200 is usually sufficient
3. **Generations**: More generations = better results but diminishing returns after ~200
4. **Negative numbers**: The optimizer automatically handles the NEGATIVE constraint
5. **Export results**: Save results before closing the app

## Technical Details

### Error Function
For each number N in the range:
```
error = (spelled_value - N)²
```

Total fitness = sum of all errors

### Genetic Algorithm Parameters
- **Selection**: Tournament selection (size 5)
- **Crossover**: Uniform crossover with averaging
- **Mutation**: Multi-level (small/medium/large adjustments)
- **Elitism**: Top 10% preserved each generation

### Letter Value Constraints
- Range: -5 to 5 (can be adjusted)
- Type: Floating-point numbers
- Initial: Random uniform distribution

## Known Limitations

- Large ranges (>10,000 numbers) may take significant time
- No guarantee of finding perfect solution (NP-hard problem)
- Negative handling assumes product of NEGATIVE letters ≈ -1

## Credits

Inspired by the Stand-up Maths video "Spelling Numbers with Variables" by Matt Parker.

## License

This project is for educational purposes.
