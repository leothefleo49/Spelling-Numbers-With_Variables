# Spelling Numbers with Variables Calculator

> 🔢 **AI-powered genetic algorithm solver** that finds optimal letter values to "solve" number spellings with modern glassmorphism UI and real-time optimization tracking.

[![Download Latest Release](https://img.shields.io/github/v/release/leothefleo49/Spelling-Numbers-With_Variables?style=for-the-badge&logo=github)](https://github.com/leothefleo49/Spelling-Numbers-With_Variables/releases/latest)
[![Platform Support](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue?style=for-the-badge)](#)
[![Python](https://img.shields.io/badge/Python-3.7%2B-green?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](./LICENSE)

---

## 📥 Quick Start

```bash
# Clone the repository
git clone https://github.com/leothefleo49/Spelling-Numbers-With_Variables.git
cd Spelling-Numbers-With_Variables

# Install dependencies
pip install -r requirements.txt

# Launch the new modern app
python run_modern.py
```

---

## ✨ Features

### Core Capabilities
- **🚀 High-Performance Solver**: Uses SciPy's L-BFGS-B algorithm with analytical gradients for lightning-fast optimization.
- **⚡ Vectorized Evaluation**: Pre-compiled number structures allow for rapid fitness calculation.
- **🎨 Modern UI**: Built with CustomTkinter for a sleek, native-feeling dark mode interface.
- **📊 Real-Time Visualization**: Watch the error drop in real-time with live logs and results.
- **🔍 Interactive Explorer**: Test any number to see how its value is calculated with the current letter variables.

### Technical Improvements
- **Refactored Architecture**: Clean `src/core` and `src/ui` separation.
- **Gradient-Based Optimization**: Replaced slow genetic algorithm with deterministic gradient descent for better convergence.
- **Optimized Parser**: Pre-compiles spelling rules into mathematical terms for O(1) evaluation.

---

## 🎨 User Interface

### Modern Design Elements
- ✨ **Glassmorphism Effects**: Translucent cards with backdrop blur
- 🎯 **iOS-Style Toggles**: Smooth animated switches replacing checkboxes
- 🌓 **Dark/Light Themes**: Instant theme switching without losing state
- 📱 **Responsive Layout**: Scrollable panels adapting to any screen size
- ⚙️ **Collapsible Sections**: Organized configuration with contextual tooltips
- 🎬 **Smooth Animations**: Progress bars, hover effects, and state transitions

### Setup Tab
Configure your optimization:
- Number range selection with quick presets (0-10, -100 to 100, etc.)
- Population size and generation limits
- Evaluation mode selector (Product/Linear)
- Advanced options with modern toggle switches
- Real-time input validation

### Solving Tab
Watch optimization in action:
- Live generation counter and timer
- Solved numbers / Total numbers ratio
- Best fitness (total error) score
- Animated progress bar
- Scrolling console log with emoji indicators (⚡ 🎯 ✅)
- Stop button with graceful shutdown

### Results Tab
Explore your solution:
- Summary statistics card
- Letter values grid (A-Z) with 4-decimal precision
- Sortable results table with filtering
- Interactive number explorer
- Detailed calculation explanations
- Export to text file

---

## 🚀 How It Works

### The Problem

Inspired by [Stand-up Maths' YouTube video](https://www.youtube.com/watch?v=LNS1fabDkeA), this app solves the challenge:

> Find values for letters A-Z such that when you spell out a number, the calculated value equals the number itself.

**Example**: If we find values where `O × N × E = 1`, then "ONE" is "solved" because its spelling evaluates to 1.

### Number Parsing Rules

The parser intelligently applies operations based on component magnitudes:

#### Multiplication (Smallest → Largest)
```
300 → "THREE HUNDRED"
Components: THREE (3), HUNDRED (100)
Calculation: (T×H×R×E×E) × (H×U×N×D×R×E×D)
```

#### Addition (Largest → Smallest)
```
23 → "TWENTY-THREE"  
Components: TWENTY (20), THREE (3)
Calculation: (T×W×E×N×T×Y) + (T×H×R×E×E)
```

#### Negative Handling
```
-45 → "NEGATIVE FORTY-FIVE"
Constraint: N×E×G×A×T×I×V×E = -1
Calculation: (-1) × [(F×O×R×T×Y) + (F×I×V×E)]
```

### Optimization Engine

**Hybrid Solver Architecture**:

1. **Analytic Initialization** (Linear Mode):
   - Constructs letter-count matrix A and target vector b
   - Solves least-squares system: A × x = b
   - Provides instant baseline solution
   - Seeds population for genetic refinement

2. **Genetic Algorithm** (Product Mode):
   - Tournament selection (size 5)
   - Uniform crossover with averaging
   - Gradient-aware mutation (small/medium/large)
   - Elite preservation (top 10%)
   - Multi-pass hill-climbing

3. **Adaptive Strategies**:
   - Auto-increasing decimal precision on stagnation
   - Dynamic hint-range narrowing near convergence
   - CPU usage throttling for background processing

---

## 📊 Usage Examples

### Quick Test (Learning)
```
Range: -10 to 10 (21 numbers)
Population: 50
Generations: 50
Time: ~30 seconds
Expected: 5-10 solved numbers
```

### Standard Test (Typical)
```
Range: -100 to 100 (201 numbers)
Population: 100  
Generations: 100
Time: ~5 minutes
Expected: 15-30 solved numbers
```

### Comprehensive Test (Research)
```
Range: -1000 to 1000 (2001 numbers)
Population: 200
Generations: 200
Time: ~45 minutes
Expected: 40-80 solved numbers
```

### Linear Mode (Fast Baseline)
```
Any range
Evaluation Mode: Linear
Instant results with ~2-5 solved numbers
Use as starting point for product refinement
```

---

## 🛠️ Technical Details

### Architecture

```
app_modern.py          # Modern UI with glassmorphism
optimizer.py           # Hybrid genetic/analytic solver
spelling_parser.py     # Number parsing and evaluation
number_to_words.py     # Integer to English conversion
logger_setup.py        # Centralized error logging
```

### Dependencies

```txt
numpy>=1.24.0          # Matrix operations for analytic solver
psutil>=5.9.0          # CPU usage monitoring (optional)
```

### Mathematical Foundation

**Fitness Function**:
```python
fitness = Σ(spelled_value - target_number)² for all numbers in range
```

**Gradient Approximation** (Hill-Climbing):
```python
∂fitness/∂letter[i] ≈ (f(x + ε) - f(x - ε)) / (2ε)
```

**Least-Squares Solver** (Linear Mode):
```python
A × x = b
where A[i,j] = count of letter j in number i
      b[i] = target value of number i
      x = optimal letter values (minimize ||Ax - b||²)
```

---

## 🎯 Optimization Tips

1. **Start with Linear Mode** to get instant baseline, then switch to Product mode for refinement
2. **Use Auto Decimal** (enabled by default) - it adapts precision automatically
3. **Smaller ranges converge faster** - test with -50 to 50 before expanding
4. **Population > 100** recommended for ranges over 500 numbers
5. **Monitor the log** - stagnation (no improvement for 20+ generations) suggests convergence
6. **Export early** - save promising solutions before experimenting with parameters

---

## 🐛 Troubleshooting

### Optimization Never Completes
- ✅ Use smaller range first (-10 to 10)
- ✅ Reduce population size (try 50)
- ✅ Enable Auto Decimal
- ✅ Check CPU usage isn't set too low

### Low Solved Count
- ✅ Increase generations (try 200+)
- ✅ Increase population (try 150-200)
- ✅ Try Linear mode first for baseline
- ✅ Longer ranges need more iterations

### UI Not Updating
- ✅ Check error.log for exceptions
- ✅ Ensure numpy is installed
- ✅ Restart the app
- ✅ Try smaller test range first

### Theme Toggle Glitches
- ✅ Fixed in v1.0.0+ - updates without destroying state
- ✅ Update to latest version

---

## 📁 Project Structure

```
Spelling_Numbers_With_Variables_Calculator/
├── app_modern.py              # Main application (modern UI)
├── optimizer.py               # Genetic algorithm + analytic solver
├── spelling_parser.py         # Number parsing engine
├── number_to_words.py         # Integer to English text
├── logger_setup.py            # Error logging configuration
├── requirements.txt           # Python dependencies
├── launch.py                  # Simple launcher script
├── run.py                     # Alternative launcher
├── validate.py                # Dependency checker
├── test_all.py                # Test suite
├── error.log                  # Runtime logs (auto-generated)
└── README.md                  # This file
```

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Areas for Contribution**:
- Additional parsing rules (fractions, decimals)
- Parallel processing improvements
- UI enhancements and themes
- Alternative optimization algorithms
- Unit test coverage
- Documentation improvements

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) file for details.

**Summary**: Free to use, modify, and distribute with attribution.

---

## 🙏 Acknowledgments

- **Inspiration**: [Stand-up Maths - "Spelling Numbers with Variables"](https://www.youtube.com/watch?v=LNS1fabDkeA) by Matt Parker
- **Genetic Algorithm**: Inspired by classical evolutionary computation research
- **Least-Squares Solver**: Based on linear algebra fundamentals
- **UI Design**: Modern glassmorphism trends and iOS design patterns
- **Number-to-Words**: English language rules for integer representation

---

## 📞 Support & Community

- **Issues**: [GitHub Issues](https://github.com/leothefleo49/Spelling-Numbers-With_Variables/issues)
- **Discussions**: [GitHub Discussions](https://github.com/leothefleo49/Spelling-Numbers-With_Variables/discussions)
- **Email**: [leothefleo49@gmail.com](mailto:leothefleo49@gmail.com)

---

## 🎓 Educational Use

This project is ideal for:
- Learning genetic algorithms
- Understanding optimization heuristics
- Exploring numerical parsing
- Studying UI/UX design patterns
- Teaching Python best practices

Feel free to use in academic settings with attribution.

---

## 🔮 Future Roadmap

- [ ] Export to CSV/JSON formats
- [ ] Visualization of letter value evolution over generations
- [ ] Parallel multi-threaded evaluation
- [ ] Web-based version (React + FastAPI)
- [ ] Command-line interface option
- [ ] Preset letter value templates
- [ ] Multi-objective optimization (solved count + error minimization)
- [ ] Support for other languages (Spanish, French, etc.)

---

## 💖 Support Development

If you find this project useful, consider:

- ⭐ **Star the repository** on GitHub
- 🐛 **Report bugs** or suggest features
- 📢 **Share** with others interested in optimization
- 💰 **Sponsor** via [GitHub Sponsors](https://github.com/sponsors/leothefleo49)

Every contribution helps maintain and improve this project!

---

Made with ❤️ by [leothefleo49](https://github.com/leothefleo49) | Inspired by Stand-up Maths
