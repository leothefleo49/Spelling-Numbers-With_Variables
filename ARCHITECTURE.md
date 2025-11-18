# System Architecture

## Application Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE (app.py)                  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Setup Tab  │  │ Solving Tab  │  │ Results Tab  │         │
│  │              │  │              │  │              │         │
│  │ - Range      │  │ - Progress   │  │ - Letters    │         │
│  │ - Population │  │ - Stats      │  │ - Explorer   │         │
│  │ - Gens       │  │ - Log        │  │ - Export     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                  │                  │                 │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OPTIMIZATION ENGINE                           │
│                      (optimizer.py)                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │         Genetic Algorithm Loop                        │      │
│  │                                                       │      │
│  │  1. Initialize Population (random letter values)     │      │
│  │           │                                           │      │
│  │           ▼                                           │      │
│  │  2. Evaluate Fitness ──► calculate_fitness()         │      │
│  │           │                      │                    │      │
│  │           │                      ▼                    │      │
│  │           │              ┌──────────────┐            │      │
│  │           │              │ For each N:  │            │      │
│  │           │              │ Get spelling │            │      │
│  │           │              │ Calculate    │            │      │
│  │           │              │ Error²       │            │      │
│  │           │              └──────────────┘            │      │
│  │           ▼                                           │      │
│  │  3. Selection (tournament)                           │      │
│  │           │                                           │      │
│  │           ▼                                           │      │
│  │  4. Crossover (combine parents)                      │      │
│  │           │                                           │      │
│  │           ▼                                           │      │
│  │  5. Mutation (random changes)                        │      │
│  │           │                                           │      │
│  │           ▼                                           │      │
│  │  6. Elitism (keep best 10%)                          │      │
│  │           │                                           │      │
│  │           └──────► Next Generation                   │      │
│  │                                                       │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               │ Uses letter values
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SPELLING PARSER                               │
│                  (spelling_parser.py)                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  Input: "TWENTY-THREE" + letter values               │      │
│  │                                                       │      │
│  │  1. Parse Components:                                │      │
│  │     ├─ "TWENTY" (magnitude 20)                       │      │
│  │     └─ "THREE" (magnitude 3)                         │      │
│  │                                                       │      │
│  │  2. Detect Order:                                    │      │
│  │     └─ 20 > 3 → Largest to smallest → ADD           │      │
│  │                                                       │      │
│  │  3. Calculate Word Products:                         │      │
│  │     ├─ TWENTY = T×W×E×N×T×Y                         │      │
│  │     └─ THREE = T×H×R×E×E                            │      │
│  │                                                       │      │
│  │  4. Apply Rule:                                      │      │
│  │     └─ Result = TWENTY + THREE                       │      │
│  │                                                       │      │
│  │  Output: Spelled value + explanation                 │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               │ Needs number spelling
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  NUMBER TO WORDS CONVERTER                       │
│                   (number_to_words.py)                           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  Input: 23 (integer)                                 │      │
│  │                                                       │      │
│  │  1. Check if negative → handle NEGATIVE prefix       │      │
│  │  2. Break down by magnitude:                         │      │
│  │     - Billions (if >= 1,000,000,000)                 │      │
│  │     - Millions (if >= 1,000,000)                     │      │
│  │     - Thousands (if >= 1,000)                        │      │
│  │     - Hundreds (if >= 100)                           │      │
│  │     - Tens and ones                                  │      │
│  │  3. Convert each part to words                       │      │
│  │  4. Combine with spaces/hyphens                      │      │
│  │                                                       │      │
│  │  Output: "TWENTY-THREE"                              │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User Input (Range: -100 to 100, Pop: 100, Gens: 100)
    │
    ▼
Optimizer.initialize_population()
    │
    ├─► Create 100 random letter value sets (A-Z)
    │   Each letter: random float between -5 and 5
    │
    ▼
For each generation (1 to 100):
    │
    ├─► For each individual in population:
    │   │
    │   ├─► For each number in range (-100 to 100):
    │   │   │
    │   │   ├─► number_to_words(number) → spelling
    │   │   │
    │   │   ├─► SpellingParser.calculate_spelled_value(spelling)
    │   │   │   │
    │   │   │   ├─► Parse components
    │   │   │   ├─► Detect multiplication vs addition
    │   │   │   ├─► Calculate word products
    │   │   │   └─► Return spelled_value
    │   │   │
    │   │   └─► Calculate error = (spelled_value - number)²
    │   │
    │   └─► Sum all errors → individual's fitness
    │
    ├─► Sort population by fitness (lower = better)
    │
    ├─► Selection: Pick parents via tournament
    │
    ├─► Crossover: Create children from parents
    │
    ├─► Mutation: Randomly modify children
    │
    ├─► Elitism: Keep top 10% unchanged
    │
    ├─► Update UI with progress
    │
    └─► Next generation
    │
    ▼
Best solution found (26 letter values)
    │
    ▼
Results displayed in UI
    │
    ├─► Show letter values
    ├─► Show solved count
    └─► Enable number explorer
```

## Component Dependencies

```
app.py
  ├─ depends on → optimizer.py
  ├─ depends on → spelling_parser.py
  └─ depends on → number_to_words.py

optimizer.py
  ├─ depends on → spelling_parser.py
  ├─ depends on → number_to_words.py
  └─ depends on → numpy

spelling_parser.py
  └─ depends on → number_to_words.py

number_to_words.py
  └─ (no dependencies - pure Python)
```

## Optimization Algorithm Detail

```
┌──────────────────────────────────────────────────────┐
│           GENETIC ALGORITHM PARAMETERS                │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Population Size: 50-200                             │
│  ├─ Each individual: 26 letter values (A-Z)          │
│  └─ Stored as: {'A': 1.5, 'B': -0.3, ...}           │
│                                                       │
│  Selection Method: Tournament                        │
│  ├─ Tournament size: 5                               │
│  └─ Pick best from random 5 individuals              │
│                                                       │
│  Crossover: Uniform with averaging                   │
│  ├─ 45% chance: take from parent1                    │
│  ├─ 45% chance: take from parent2                    │
│  └─ 10% chance: average + noise                      │
│                                                       │
│  Mutation: Multi-level                               │
│  ├─ Rate: 10% per letter                             │
│  ├─ Small: ±0.5 (40%)                               │
│  ├─ Medium: ±2.0 (30%)                              │
│  └─ Large: random -5 to 5 (30%)                     │
│                                                       │
│  Elitism: Top 10% preserved                          │
│  └─ Ensures best solutions never lost                │
│                                                       │
│  Constraints:                                        │
│  └─ NEGATIVE penalty: 10 × (N×E×G×A×T×I×V×E - (-1))²│
│                                                       │
└──────────────────────────────────────────────────────┘
```

## Parsing Rules Flowchart

```
                    Input: "TWENTY-THREE"
                             │
                             ▼
                  ┌─────────────────────┐
                  │  Parse Components   │
                  └─────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
        "TWENTY" (20)                 "THREE" (3)
              │                             │
              └──────────────┬──────────────┘
                             ▼
                  ┌─────────────────────┐
                  │ Compare Magnitudes  │
                  └─────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
    [20 > 3: Decreasing]        [3 < 20: Increasing]
              │                             │
              ▼                             ▼
         ┌─────────┐                 ┌──────────────┐
         │   ADD   │                 │  MULTIPLY    │
         └─────────┘                 └──────────────┘
              │                             │
              ▼                             ▼
    T×W×E×N×T×Y + T×H×R×E×E       T×H×R×E×E × H×U×N×D×R×E×D
```

## Threading Model

```
┌─────────────────────────────────────────────────────┐
│                   MAIN THREAD                        │
│                     (UI)                             │
│                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │  tkinter   │  │   Update   │  │  Display   │   │
│  │  Events    │◄─┤   UI       │◄─┤  Results   │   │
│  └────────────┘  └────────────┘  └────────────┘   │
│        │                │                           │
└────────┼────────────────┼───────────────────────────┘
         │                │
         │                │ callbacks
         │                │
         ▼                │
┌─────────────────────────┼───────────────────────────┐
│              BACKGROUND THREAD                       │
│                 (Optimization)                       │
│                      │                               │
│  ┌───────────────────▼────────────────────┐        │
│  │   Optimizer.optimize()                  │        │
│  │                                         │        │
│  │   Loop through generations:             │        │
│  │   ├─ Calculate fitness                  │        │
│  │   ├─ Selection                          │        │
│  │   ├─ Crossover                          │        │
│  │   ├─ Mutation                           │        │
│  │   └─ Callback to main thread ──────────┼────┐   │
│  │                                         │    │   │
│  └─────────────────────────────────────────┘    │   │
│                                                  │   │
└──────────────────────────────────────────────────┼───┘
                                                   │
                         (root.after)              │
                                                   │
                    Updates UI safely ◄────────────┘
```

## File Size & Complexity

```
Component              Lines    Complexity    Purpose
─────────────────────────────────────────────────────────
number_to_words.py      ~120    Simple        Conversion
spelling_parser.py      ~220    Medium        Parsing logic
optimizer.py            ~290    Complex       AI algorithm
app.py                  ~590    Medium        GUI interface
demo.py                  ~80    Simple        Demonstration
test_*.py               ~100    Simple        Testing
─────────────────────────────────────────────────────────
Total                  ~1400    Mixed         Complete app
```
