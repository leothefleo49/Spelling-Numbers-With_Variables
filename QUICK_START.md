# Quick Start Guide

## Installation

1. Ensure Python 3.7+ is installed:
   ```
   py --version
   ```

2. Install dependencies:
   ```
   py -m pip install numpy
   ```

## Running the Application

### Option 1: Windows Batch File
```
run.bat
```

### Option 2: Python Script
```
py run.py
```

### Option 3: Direct Launch
```
py app.py
```

## Testing Individual Components

### Test Number Conversion
```
py number_to_words.py
```

### Test Spelling Parser
```
py spelling_parser.py
```

### Test Optimizer (Small Range)
```
py test_optimizer.py
```

### Interactive Demo
```
py demo.py
```

## Using the Application

### Step 1: Configure Your Range
- **Start Range**: The lowest number (can be negative)
- **End Range**: The highest number
- **Population Size**: 50-200 (higher = better but slower)
- **Generations**: 50-200 (higher = better but slower)

### Step 2: Start Calculation
Click "Start Calculation" and watch the progress:
- Generation counter shows current iteration
- Solved count shows how many numbers are solved
- Fitness shows total error (lower is better)
- Progress log shows detailed history

### Step 3: Explore Results
- View the 26 letter values (A-Z)
- Use the Number Explorer to examine specific numbers
- See detailed breakdowns of how each number is calculated
- Export results to a text file

## Recommended Settings for Different Uses

### Quick Test (2-3 minutes)
- Range: -10 to 10
- Population: 50
- Generations: 30

### Standard Run (5-10 minutes)
- Range: -100 to 100
- Population: 100
- Generations: 100

### Comprehensive (30-60 minutes)
- Range: -1000 to 1000
- Population: 200
- Generations: 200

### Custom Challenge
Try to maximize solved numbers in specific ranges:
- 0 to 100 (positive only)
- -50 to 50 (balanced)
- 1 to 1000 (large positive)

## Understanding the Results

### Letter Values
The 26 values found for A-Z. These can be:
- Positive or negative
- Integers or decimals
- Usually between -5 and 5

### Solved Numbers
A number is "solved" when:
- Error < 0.01
- Meaning the spelled value is very close to the target

### Fitness Score
- Lower is better
- Sum of all squared errors
- Includes penalty for NEGATIVE constraint

## Tips for Best Results

1. **Start Small**: Test with a small range first to understand performance
2. **Balance Speed vs Quality**: More population/generations = better results but slower
3. **Export Results**: Save your results before closing the app
4. **Experiment**: Try different ranges to see what patterns emerge
5. **Check NEGATIVE**: The product N×E×G×A×T×I×V×E should be close to -1 for best results

## Troubleshooting

### Application Won't Start
- Check Python installation: `py --version`
- Install NumPy: `py -m pip install numpy`
- Check for error messages in terminal

### Slow Performance
- Reduce population size
- Reduce number of generations
- Use a smaller number range

### Poor Results (Few Solved Numbers)
- Increase population size
- Increase number of generations
- Try a different range (some ranges are harder than others)

### "No Module Named numpy"
```
py -m pip install --upgrade pip
py -m pip install numpy
```

## Files in This Project

- `app.py` - Main GUI application
- `number_to_words.py` - Number to words converter
- `spelling_parser.py` - Parsing and calculation logic
- `optimizer.py` - Genetic algorithm optimizer
- `demo.py` - Interactive demonstration
- `test_optimizer.py` - Quick optimizer test
- `run.py` - Cross-platform launcher
- `run.bat` - Windows launcher
- `README.md` - Full documentation
- `QUICK_START.md` - This file
- `requirements.txt` - Python dependencies

## Example Session

```
1. Launch: py app.py
2. Enter range: -10 to 10
3. Set population: 50
4. Set generations: 30
5. Click "Start Calculation"
6. Wait 2-3 minutes
7. View results
8. Explore number "1" to see if it's solved
9. Export results to file
```

## Advanced Usage

### Custom Letter Values
Edit `spelling_parser.py` to set custom initial values for testing specific hypotheses.

### Different Optimization Algorithms
Modify `optimizer.py` to try different optimization strategies:
- Simulated annealing
- Particle swarm optimization
- Hill climbing
- Random search

### Extended Number Support
Modify `number_to_words.py` to add support for:
- Fractions
- Decimals
- Scientific notation

## Getting Help

If you encounter issues:
1. Check this guide
2. Review README.md for detailed information
3. Run demo.py to verify installation
4. Check Python and NumPy versions

## Credits

Based on the YouTube video "Spelling Numbers with Variables" by Stand-up Maths (Matt Parker).
