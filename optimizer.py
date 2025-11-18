"""  
Optimization Solver
Uses genetic algorithm to find optimal letter values.
"""

from typing import Union
import random
import multiprocessing as mp
import os
import time
try:
    import numpy as np  # type: ignore
except ImportError:
    np = None
try:
    import psutil  # type: ignore
except ImportError:
    psutil = None
from spelling_parser import SpellingParser
from number_to_words import number_to_words
from logger_setup import get_logger

logger = get_logger('optimizer')


class LetterValueOptimizer:
    """
    Finds optimal letter values (A-Z) to minimize spelling errors.
    Uses a genetic algorithm approach.
    """
    
    def __init__(self, start_range: int, end_range: int, population_size: int = 100,
                 mutation_rate: float = 0.1, decimal_places: Union[int, str] = 4,
                 allow_negative_values: bool = True, space_operator: str = 'auto',
                 hyphen_operator: str = 'minus', cpu_usage: Union[str, int] = 'auto',
                 evaluation_mode: str = 'product'):
        """
        Initialize the optimizer.
        
        Args:
            start_range (int): Start of number range
            end_range (int): End of number range
            population_size (int): Size of the genetic algorithm population
            mutation_rate (float): Probability of mutation
            decimal_places (int | str): Number of decimal places (0-10) or 'auto'
            allow_negative_values (bool): Whether letter values can be negative
            space_operator (str): Operation for spaces
            hyphen_operator (str): Operation for hyphens
            cpu_usage (str | int): 'auto', percentage (1-100), or number of cores
        """
        self.start_range = start_range
        self.end_range = end_range
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.initial_decimal_places = decimal_places
        # Convert to int immediately - 'auto' becomes 0, then adapts
        self.decimal_places: int = 0 if decimal_places == 'auto' else int(decimal_places)
        self.adaptive_decimals = (decimal_places == 'auto')
        self.allow_negative_values = allow_negative_values
        self.space_operator = space_operator
        self.hyphen_operator = hyphen_operator
        self.numbers = list(range(start_range, end_range + 1))
        self.evaluation_mode = evaluation_mode  # 'product' or 'linear'
        
        # CPU usage configuration
        self.cpu_usage_mode = cpu_usage
        total_cores = mp.cpu_count()
        if cpu_usage == 'auto':
            self.cpu_cores = max(1, total_cores - 1)
            self.dynamic_cpu = True
            self.last_cpu_check = time.time()
        elif isinstance(cpu_usage, str) and cpu_usage.endswith('%'):
            percentage = int(cpu_usage[:-1])
            self.cpu_cores = max(1, int(total_cores * percentage / 100))
            self.dynamic_cpu = False
        else:
            self.cpu_cores = max(1, min(int(cpu_usage), total_cores))
            self.dynamic_cpu = False
        
        # Adaptive tracking
        self.stagnation_counter = 0
        self.last_improvement = float('inf')
        self.decimal_increased = False
        
        # Population: list of letter value sets
        self.population = []
        self.best_solution = None
        self.best_fitness = float('inf')
        self.generation = 0
        self.fitness_history = []
        
        # Internal caches
        self.letters = [chr(65 + i) for i in range(26)]
        self.parser = SpellingParser(space_operator=self.space_operator,
                                     hyphen_operator=self.hyphen_operator,
                                     decimal_places=self.decimal_places)
        self.letter_constraints = {}
        self.letter_hints = {}
        self.letter_count_matrix = None  # For least squares approximation
        self.targets_vector = None
        self.component_cache = []  # Parsed spelling components per number
        self.precompute_structures()
        self.analyze_constraints()
        self.initialize_population()
        # Deterministic / analytic tracking
        self.last_gradients = {L: 0.0 for L in self.letters}
        self.least_squares_solution = None
        if self.evaluation_mode == 'linear' and np is not None:
            self.perform_analytic_solve()

    def precompute_structures(self):
        """Precompute letter count matrix and parsed components for speed & logic."""
        counts = []
        targets = []
        self.component_cache = []
        for num in self.numbers:
            spelling = number_to_words(num)
            # store parsed components (list of words and separators) for reuse
            components = self.parser.parse_components(spelling)
            self.component_cache.append((num, spelling, components))
            flat_spelling = spelling.upper().replace(' ', '').replace('-', '')
            counts.append([flat_spelling.count(L) for L in self.letters])
            targets.append(num)
        if np is not None:
            try:
                self.letter_count_matrix = np.array(counts, dtype=float)
                self.targets_vector = np.array(targets, dtype=float)
            except Exception:
                self.letter_count_matrix = None
                self.targets_vector = None
        else:
            # Pure Python fallback (lists)
            self.letter_count_matrix = counts
            self.targets_vector = targets
    
    def solve_constraints_system(self):
        """Try to solve letter values directly using equation systems"""
        # For simple cases, we can solve exact equations
        # Example: if we only have 0, 1, 2 -> we can solve directly
        if np is None or self.letter_count_matrix is None or self.targets_vector is None:
            return False
        A = self.letter_count_matrix
        b = self.targets_vector
        rows = len(A)
        if rows < 5:  # need enough equations
            return False
        try:
            solution, residuals, rank, _ = np.linalg.lstsq(A, b, rcond=None)
            logger.info('Least squares rank=%s residuals=%s', rank, residuals)
            cols = len(A[0]) if rows > 0 else 0
            if rank >= min(10, cols):
                solved_letters = 0
                for i, val in enumerate(solution):
                    letter = self.letters[i]
                    if abs(val) < 1e6:  # keep sane
                        self.letter_hints[letter] = (val * 0.9, val * 1.1) if val != 0 else (-0.5, 0.5)
                        solved_letters += 1
                self.least_squares_solution = {self.letters[i]: solution[i] for i in range(len(self.letters))}
                logger.info('Generated hints for %d letters via least squares', solved_letters)
                return True
        except Exception as e:
            logger.exception('Least squares solving failed: %s', e)
            return False
        return False
    
    def analyze_constraints(self):
        """Analyze number spellings to deduce logical constraints"""
        from collections import Counter
        
        # First try to solve the system directly
        solved_directly = self.solve_constraints_system()
        if solved_directly:
            logger.info('Initial equation system produced hints for letters. Hints count=%d', len(self.letter_hints))
        
        # Count letter occurrences across all numbers
        letter_counts = Counter()
        number_spellings = {}
        
        for num in self.numbers:
            spelling = number_to_words(num).upper().replace(' ', '').replace('-', '')
            number_spellings[num] = spelling
            letter_counts.update(spelling)
        
        # Find unique letters (appear in only one number)
        letter_to_numbers = {chr(65 + i): [] for i in range(26)}
        for num, spelling in number_spellings.items():
            for letter in set(spelling):
                letter_to_numbers[letter].append(num)
        
        # ZERO is the only number with Z - we can deduce Z = 0 / len(Z occurrences)
        if 0 in self.numbers:
            zero_spelling = number_to_words(0).upper().replace(' ', '').replace('-', '')
            z_count = zero_spelling.count('Z')
            if z_count > 0:
                # Z appears in ZERO: Z*E*R*O should ≈ 0
                # For simple case: if only in zero, Z should be very small or 0
                self.letter_hints['Z'] = (0.0, 0.1)  # Z should be near 0
                logger.debug('Applied Z near-zero hint based on ZERO presence')
        
        # ONE has unique combination - if we know target, can deduce relationships
        if 1 in self.numbers:
            one_spelling = number_to_words(1).upper().replace(' ', '').replace('-', '')
            # O*N*E should ≈ 1, so these letters multiply to 1
            applied = False
            for letter in one_spelling:
                if letter not in self.letter_hints:
                    self.letter_hints[letter] = (0.5, 1.5)
                    applied = True
            if applied:
                logger.debug('Applied ONE product hints to letters %s', list(one_spelling))
        
        # Numbers with unique letters give us direct equations
        unique_letters = {letter: nums for letter, nums in letter_to_numbers.items() 
                         if len(nums) == 1 and abs(nums[0]) <= 20}
        
        # Frequency-based hints: common letters should have moderate values
        total_letters = sum(letter_counts.values())
        for letter, count in letter_counts.most_common():
            if count > 0 and letter not in self.letter_hints:
                # More frequent = smaller value to avoid dominating
                frequency = count / total_letters
                if frequency > 0.15:  # Very common
                    self.letter_hints[letter] = (0.1, 0.8)
                elif frequency > 0.08:  # Common
                    self.letter_hints[letter] = (0.3, 1.2)
                else:  # Rare
                    self.letter_hints[letter] = (0.5, 2.0)
        logger.info('Constraint analysis complete. Hints=%d', len(self.letter_hints))

    def perform_analytic_solve(self):
        """Perform direct least-squares solve for linear evaluation mode."""
        if self.evaluation_mode != 'linear' or np is None:
            return
        if self.letter_count_matrix is None or self.targets_vector is None:
            return
        try:
            A = self.letter_count_matrix
            b = self.targets_vector
            solution, residuals, rank, _ = np.linalg.lstsq(A, b, rcond=None)
            letter_values = {self.letters[i]: float(solution[i]) for i in range(len(self.letters))}
            if not self.allow_negative_values:
                letter_values = {L: (v if v >= 0 else abs(v)) for L, v in letter_values.items()}
            self.best_solution = letter_values.copy()
            self.best_fitness, solved_count, _ = self.calculate_fitness(letter_values)
            # Seed population around analytic solution
            self.population = [letter_values.copy()]
            for _ in range(max(1, self.population_size - 1)):
                perturbed = {L: (val + random.uniform(-0.1, 0.1)) for L, val in letter_values.items()}
                if self.decimal_places is not None:
                    perturbed = {L: round(v, self.decimal_places) for L, v in perturbed.items()}
                self.population.append(perturbed)
            logger.info('Analytic linear solve complete: rank=%d residuals=%s fitness=%.4f solved=%d/%d',
                        rank, residuals, self.best_fitness, solved_count, len(self.numbers))
        except Exception as e:
            logger.exception('Analytic solve failed: %s', e)
    
    def initialize_population(self):
        """Create initial population with constraint-based seeding"""
        self.population = []
        
        # Use analyzed constraints as primary guide
        letter_freq = {
            'E': 0.8, 'T': 0.6, 'A': 0.5, 'O': 0.5, 'I': 0.4, 'N': 0.4, 'S': 0.3,
            'H': 0.3, 'R': 0.3, 'D': 0.2, 'L': 0.2, 'U': 0.1, 'C': 0.1, 'M': 0.1,
            'W': 0.1, 'F': 0.1, 'G': 0.1, 'Y': 0.1, 'P': 0.1, 'B': 0.1,
            'V': 0.1, 'K': 0.05, 'X': 0.05, 'J': 0.05, 'Q': 0.05, 'Z': 0.05
        }
        
        # Add constraint-based seeded individuals
        seeded_count = min(10, self.population_size // 2)  # More seeds
        
        logger.info('Seeding population with %d constraint-based individuals', seeded_count)
        for seed_idx in range(seeded_count):
            letter_values = {}
            for i in range(26):
                letter = chr(65 + i)
                
                # Check if we have constraints/hints for this letter
                if letter in self.letter_constraints:
                    # Use fixed constraint value with small noise
                    base = self.letter_constraints[letter]
                    if seed_idx == 0:
                        value = base  # First seed is exact
                    else:
                        # Add small variations for diversity
                        noise = random.gauss(0, 0.01 * abs(base) if base != 0 else 0.01)
                        value = base + noise
                elif letter in self.letter_hints:
                    # Use hint range
                    min_val, max_val = self.letter_hints[letter]
                    value = random.uniform(min_val, max_val)
                else:
                    # Use seeding strategies
                    base_val = letter_freq.get(letter, 0.1)
                    
                    if seed_idx == 0:
                        # Seed 1: Constraint-aware frequency
                        value = base_val + random.uniform(-0.1, 0.1)
                    elif seed_idx == 1:
                        # Seed 2: Optimize for small numbers (0-10)
                        if letter in 'ZERO':
                            value = random.uniform(0.0, 0.5)
                        elif letter in 'ONE':
                            value = random.uniform(0.8, 1.2)
                        elif letter in 'TWO':
                            value = random.uniform(0.4, 0.8)
                        else:
                            value = random.uniform(0.1, 1.0)
                    elif seed_idx == 2:
                        # Seed 3: Target product = 1 for common combos
                        value = random.uniform(0.5, 1.5)
                    elif seed_idx == 3:
                        # Seed 4: Vowels moderate, consonants varied
                        if letter in 'AEIOU':
                            value = random.uniform(0.6, 1.4)
                        else:
                            value = random.uniform(0.2, 1.8)
                    elif seed_idx == 4:
                        # Seed 5: Position hints
                        value = (i + 1) * 0.08 + random.uniform(-0.1, 0.1)
                    elif seed_idx == 5:
                        # Seed 6: Reverse position
                        value = (26 - i) * 0.08 + random.uniform(-0.1, 0.1)
                    elif seed_idx == 6:
                        # Seed 7: Cluster around 1.0
                        value = 1.0 + random.gauss(0, 0.3)
                    else:
                        # Seed 8: Wide exploration
                        value = random.uniform(0.1, 2.5)
                
                if self.decimal_places is not None:
                    value = round(value, self.decimal_places)
                letter_values[letter] = value
            
            self.population.append(letter_values)
        
        # Fill rest with random individuals
        for _ in range(self.population_size - seeded_count):
            letter_values = {}
            for i in range(26):
                letter = chr(65 + i)
                if self.least_squares_solution and letter in self.least_squares_solution:
                    base = self.least_squares_solution[letter]
                    span = 0.5 if abs(base) < 2 else 1.0
                    value = random.uniform(base - span, base + span)
                else:
                    if self.allow_negative_values:
                        value = random.uniform(-2, 3)
                    else:
                        value = random.uniform(0, 3)
                
                if self.decimal_places is not None:
                    value = round(value, self.decimal_places)
                
                letter_values[letter] = value
            
            self.population.append(letter_values)
    
    def calculate_fitness(self, letter_values):
        """
        Calculate fitness (lower is better).
        Fitness = sum of squared errors across all numbers.
        
        Args:
            letter_values (dict): Dictionary of letter values
            
        Returns:
            tuple: (total_error, solved_count, max_error)
        """
        if self.evaluation_mode == 'linear' and self.letter_count_matrix is not None:
            vec = [letter_values.get(L, 0.0) for L in self.letters]
            total_error = 0.0
            solved_count = 0
            max_error = 0.0
            for idx, number in enumerate(self.numbers):
                row = self.letter_count_matrix[idx]
                if np is not None:
                    predicted = float(np.dot(row, vec))
                else:
                    predicted = sum(r * v for r, v in zip(row, vec))
                if self.decimal_places is not None:
                    predicted = round(predicted, self.decimal_places)
                error = (predicted - number) ** 2
                total_error += error
                max_error = max(max_error, error)
                if error < 0.25:
                    solved_count += 1
            return total_error, solved_count, max_error
        # Product-based evaluation
        self.parser.set_letter_values(letter_values)
        if self.parser.decimal_places != self.decimal_places:
            self.parser.decimal_places = self.decimal_places
        total_error = 0.0
        solved_count = 0
        max_error = 0.0
        for (number, _spelling, components) in self.component_cache:
            current_value = self._calculate_components_value(components)
            error = (current_value - number) ** 2
            total_error += error
            max_error = max(max_error, error)
            if error < 0.001:
                solved_count += 1
        return total_error, solved_count, max_error

    def _calculate_components_value(self, components):
        """Fast evaluation of parsed components without reparsing string."""
        if not components:
            return 0.0
        # first component
        prod = 1.0
        word0 = components[0][0]
        for ch in word0:
            if ch.isalpha():
                prod *= self.parser.letter_values.get(ch, 1.0)
                if prod > 1e6:
                    prod = 1e6
                if prod < -1e6:
                    prod = -1e6
        value = prod
        for i in range(1, len(components)):
            prev_word, prev_mag, sep = components[i-1]
            next_word, next_mag, _ = components[i]
            # product of next word
            prod_next = 1.0
            for ch in next_word:
                if ch.isalpha():
                    prod_next *= self.parser.letter_values.get(ch, 1.0)
                    if prod_next > 1e6:
                        prod_next = 1e6
                    if prod_next < -1e6:
                        prod_next = -1e6
            # decide operator (mirror parser logic simplified)
            if sep == 'space':
                if self.space_operator == 'auto':
                    op = 'multiply' if next_mag > prev_mag else 'add'
                else:
                    op = self.space_operator
            elif sep == 'hyphen':
                op = self.hyphen_operator
            elif sep == 'multiply':
                op = 'multiply'
            else:
                op = 'add'
            if op == 'multiply':
                value = value * prod_next
            elif op in ('subtract', 'minus'):
                value = value - prod_next
            elif op == 'divide':
                value = value / prod_next if prod_next != 0 else 0
            else:
                value = value + prod_next
            # Clamp
            if value > 1e6:
                value = 1e6
            if value < -1e6:
                value = -1e6
        if self.decimal_places is not None:
            value = round(value, self.decimal_places)
        return value
    
    def selection(self, fitness_scores):
        """Stochastic Universal Sampling selection returns one parent."""
        if not fitness_scores:
            return {L: 1.0 for L in self.letters}
        # Convert fitness to probability (lower fitness = higher prob)
        fitness_values = [fs[0] for fs in fitness_scores]
        inv = [1.0 / (fv + 1e-9) for fv in fitness_values]
        total_inv = sum(inv)
        probs = [v / total_inv for v in inv]
        r = random.random()
        cumulative = 0.0
        for i, p in enumerate(probs):
            cumulative += p
            if r <= cumulative:
                return fitness_scores[i][3]
        return fitness_scores[-1][3]
    
    def crossover(self, parent1, parent2):
        """
        Create offspring by combining two parents.
        
        Args:
            parent1, parent2 (dict): Parent letter values
            
        Returns:
            dict: Child letter values
        """
        child = {}
        for letter in parent1:
            # Randomly choose from parent1, parent2, or average
            choice = random.random()
            if choice < 0.45:
                child[letter] = parent1[letter]
            elif choice < 0.90:
                child[letter] = parent2[letter]
            else:
                # Average with some noise
                child[letter] = (parent1[letter] + parent2[letter]) / 2 + random.uniform(-0.5, 0.5)
        
        return child
    
    def mutate(self, individual):
        """
        Apply smart mutations based on fitness gradients.
        
        Args:
            individual (dict): Letter values to mutate
            
        Returns:
            dict: Mutated letter values
        """
        mutated = individual.copy()
        
        # Don't mutate constrained letters (we solved these)
        protected_letters = set(self.letter_constraints.keys())
        
        # Adaptive mutation rate based on generation
        effective_rate = self.mutation_rate * (1.0 + 0.8 * (self.generation / 100))
        effective_rate = min(effective_rate, 0.5)  # Cap at 50% for more exploration
        
        for letter in mutated:
            # Skip letters we've already solved
            if letter in protected_letters:
                continue
                
            if random.random() < effective_rate:
                # Apply mutation
                mutation_type = random.random()
                
                # Gradient-aware scaling (larger gradient -> smaller perturbation)
                grad_mag = abs(self.last_gradients.get(letter, 0.0))
                scale = 1.0 / (1.0 + grad_mag)
                if mutation_type < 0.5:
                    mutated[letter] += random.uniform(-0.2, 0.2) * scale
                elif mutation_type < 0.8:
                    mutated[letter] += random.uniform(-1, 1) * scale
                else:
                    span = 3 if self.allow_negative_values else 3
                    mutated[letter] = mutated[letter] + random.uniform(-span, span) * 0.3 * scale
                
                # Enforce positive constraint if needed
                if not self.allow_negative_values and mutated[letter] < 0:
                    mutated[letter] = abs(mutated[letter])
                
                # Round to decimal places
                if self.decimal_places is not None:
                    mutated[letter] = round(mutated[letter], self.decimal_places)
        
        return mutated
    
    def hill_climb(self, individual):
        """Apply gradient-based hill climbing to refine a solution"""
        best = individual.copy()
        best_fitness, _, _ = self.calculate_fitness(best)
        
        improved = True
        iterations = 0
        max_iterations = 50  # More iterations for better refinement
        
        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            
            # Try improving each letter
            for letter in best:
                if letter in self.letter_constraints:
                    continue  # Skip solved letters
                
                original = best[letter]
                
                # Calculate gradient by testing small changes
                step_size = 0.1 if self.decimal_places < 10 else 0.01
                if self.decimal_places > 20:
                    step_size = 0.001
                
                # Test positive and negative changes
                for delta in [step_size, -step_size, step_size * 2, -step_size * 2]:
                    candidate = best.copy()
                    candidate[letter] = original + delta
                    
                    if not self.allow_negative_values and candidate[letter] < 0:
                        continue
                    
                    if self.decimal_places is not None:
                        candidate[letter] = round(candidate[letter], self.decimal_places)
                    
                    fitness, _, _ = self.calculate_fitness(candidate)
                    if fitness < best_fitness:
                        best = candidate
                        best_fitness = fitness
                        improved = True
                        break  # Move to next letter once improved
        
        return best

    def multi_pass_refine(self, individual, passes=5):
        """Run several gradient refinement passes until convergence."""
        current = individual.copy()
        base_fit, _, _ = self.calculate_fitness(current)
        for p in range(passes):
            refined = self.gradient_refine(current, store_gradients=(p == passes - 1))
            new_fit, _, _ = self.calculate_fitness(refined)
            if new_fit + 1e-9 < base_fit:
                current = refined
                base_fit = new_fit
            else:
                break
        return current, base_fit
    
    def adjust_cpu_usage(self):
        """Dynamically adjust CPU usage based on system load"""
        if not self.dynamic_cpu or psutil is None:
            return
        
        # Check every 5 seconds
        current_time = time.time()
        if current_time - self.last_cpu_check < 5:
            return
        
        self.last_cpu_check = current_time
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            total_cores = mp.cpu_count()
            
            # Target: keep system CPU below 95%, but use as much as possible
            if cpu_percent < 70:
                # System has plenty of capacity, use more cores
                self.cpu_cores = min(total_cores, self.cpu_cores + 1)
            elif cpu_percent > 95:
                # System is overloaded, reduce usage
                self.cpu_cores = max(1, self.cpu_cores - 1)
            # Between 70-95%: maintain current usage (optimal range)
        except:
            pass  # If psutil fails, keep current settings
    
    def check_adaptive_decimals(self):
        """Check if we should increase decimal precision"""
        if not self.adaptive_decimals or self.decimal_places >= 100:
            return False
        
        # Check for stagnation
        if abs(self.best_fitness - self.last_improvement) < 0.01:
            self.stagnation_counter += 1
        else:
            self.stagnation_counter = 0
            self.last_improvement = self.best_fitness
        
        # If stagnant for 10 generations and no perfect solution (faster adaptation)
        if self.stagnation_counter >= 10:
            solved_count = sum(1 for ind in self.population 
                             if self.calculate_fitness(ind)[1] == len(self.numbers))
            if solved_count == 0:  # No perfect solution yet
                # Increase decimals more aggressively
                if self.decimal_places < 5:
                    self.decimal_places += 1
                elif self.decimal_places < 20:
                    self.decimal_places += 2
                else:
                    self.decimal_places += 5
                
                self.decimal_places = min(self.decimal_places, 100)
                logger.info('Adaptive decimals increased to %d', self.decimal_places)
                self.stagnation_counter = 0
                self.decimal_increased = True
                return True
        return False
    
    def evolve_generation(self):
        """Run one generation with smart selection and local search"""
        # Ensure population exists
        if not self.population:
            self.initialize_population()
        
        if not self.population:
            raise RuntimeError("Population is empty - cannot evolve")
        
        # Dynamic CPU adjustment
        self.adjust_cpu_usage()
        
        # Evaluate current population with caching
        fitness_scores = []
        fitness_cache = {}
        for idx, individual in enumerate(self.population):
            fitness, solved, max_err = self.calculate_fitness(individual)
            fitness_scores.append((fitness, solved, max_err, individual))
            fitness_cache[idx] = (fitness, solved, max_err)
        
        # Sort by fitness (lower is better)
        fitness_scores.sort(key=lambda x: x[0])
        
        # Safety check
        if not fitness_scores:
            logger.error('No fitness scores generated - population size=%d', len(self.population))
            raise RuntimeError("No fitness scores generated")
        
        # Update best solution with hill climbing + multi-pass gradient refinement
        if fitness_scores[0][0] < self.best_fitness:
            base_best = fitness_scores[0][3]
            if self.generation % 5 == 0:
                refined = self.hill_climb(base_best)
                refined_fitness, _, _ = self.calculate_fitness(refined)
                if refined_fitness < fitness_scores[0][0]:
                    base_best = refined
                    fitness_scores[0] = (refined_fitness,) + fitness_scores[0][1:]
            grad_refined, grad_fit = self.multi_pass_refine(base_best, passes=5)
            if grad_fit < fitness_scores[0][0]:
                self.best_solution = grad_refined.copy()
                self.best_fitness = grad_fit
                logger.debug('Multi-pass gradient refinement improved fitness to %.6f', grad_fit)
            else:
                self.best_solution = base_best.copy()
                self.best_fitness = fitness_scores[0][0]
                logger.debug('Best fitness updated to %.6f', self.best_fitness)
        
        # Record statistics
        best_fitness, best_solved, best_max_err, _ = fitness_scores[0]
        
        # Check adaptive decimals
        decimal_changed = self.check_adaptive_decimals()
        
        self.fitness_history.append({
            'generation': self.generation,
            'best_fitness': best_fitness,
            'solved_count': best_solved,
            'max_error': best_max_err,
            'decimal_places': self.decimal_places,
            'decimal_changed': decimal_changed,
            'cpu_cores': self.cpu_cores
        })
        
        # Create new population
        new_population = []
        
        # Elitism: keep top 25% for better solutions preservation
        elite_count = max(1, min(self.population_size // 4, len(fitness_scores)))
        prev_best = self.best_fitness
        for i in range(min(elite_count, len(fitness_scores))):
            new_population.append(fitness_scores[i][3].copy())

        # Adaptive narrowing of hint ranges if significant improvement
        if self.best_fitness < prev_best - 0.5 and self.letter_hints:
            for L, (lo, hi) in list(self.letter_hints.items()):
                mid = (lo + hi) / 2
                span = (hi - lo) * 0.6
                self.letter_hints[L] = (mid - span/2, mid + span/2)
            logger.debug('Narrowed hint ranges to focus search')
        
        # Generate rest through crossover and mutation using SUS on full fitness_scores
        while len(new_population) < self.population_size:
            parent1 = self.selection(fitness_scores)
            parent2 = self.selection(fitness_scores)
            child = self.crossover(parent1, parent2)
            child = self.mutate(child)
            new_population.append(child)
        
        self.population = new_population
        self.generation += 1
        
        return {
            'generation': self.generation,
            'best_fitness': best_fitness,
            'solved_count': best_solved,
            'total_numbers': len(self.numbers),
            'max_error': best_max_err,
            'decimal_places': self.decimal_places,
            'decimal_changed': decimal_changed,
            'cpu_cores': self.cpu_cores,
            'cpu_percent': psutil.cpu_percent(interval=0) if (self.dynamic_cpu and psutil is not None) else 0
        }
    
    def optimize(self, max_generations=100, callback=None):
        """
        Run the optimization process.
        
        Args:
            max_generations (int): Maximum number of generations
            callback (function): Optional callback function called after each generation
                                with stats dictionary
        
        Returns:
            dict: Best letter values found
        """
        # Ensure population is initialized
        if not self.population:
            self.initialize_population()
        
        if not self.population:
            raise RuntimeError("Failed to initialize population")
        
        for gen in range(max_generations):
            stats = self.evolve_generation()
            if callback:
                callback(stats)
            # Early convergence
            if stats['solved_count'] / max(1, stats['total_numbers']) >= 0.95:
                logger.info('Early convergence achieved at generation %d (accuracy %.2f%%)', stats['generation'], stats['solved_count']/stats['total_numbers']*100)
                break
        return self.best_solution

    def gradient_refine(self, solution, store_gradients: bool = False):
        """Numerically approximate gradient and apply one descent step.
        Optionally store gradients for mutation guidance."""
        lr = 0.05 if self.decimal_places < 10 else 0.01
        eps = 0.001 if self.decimal_places < 10 else 10 ** (-(min(self.decimal_places, 10)))
        base_fitness, _, _ = self.calculate_fitness(solution)
        refined = solution.copy()
        grads_local = {}
        for L in self.letters:
            if L in self.letter_constraints:
                continue
            orig = refined[L]
            refined[L] = orig + eps
            f_plus, _, _ = self.calculate_fitness(refined)
            refined[L] = orig - eps
            f_minus, _, _ = self.calculate_fitness(refined)
            refined[L] = orig
            # central difference
            grad = (f_plus - f_minus) / (2 * eps)
            new_val = orig - lr * grad
            if not self.allow_negative_values and new_val < 0:
                new_val = abs(new_val)
            if self.decimal_places is not None:
                new_val = round(new_val, self.decimal_places)
            refined[L] = new_val
            grads_local[L] = grad
        if store_gradients:
            self.last_gradients = grads_local
        return refined
    
    def get_solution_details(self):
        """Get detailed information about the current best solution"""
        if self.best_solution is None:
            return None
        
        parser = SpellingParser(self.best_solution, self.space_operator, self.hyphen_operator,
                               self.decimal_places)
        
        results = []
        solved_count = 0
        
        for number in self.numbers:
            spelling = number_to_words(number)
            spelled_value, explanation = parser.calculate_spelled_value(spelling)
            error = (spelled_value - number) ** 2
            
            is_solved = error < 0.01
            if is_solved:
                solved_count += 1
            
            results.append({
                'number': number,
                'spelling': spelling,
                'spelled_value': spelled_value,
                'error': error,
                'is_solved': is_solved,
                'explanation': explanation
            })
        
        return {
            'letter_values': self.best_solution,
            'results': results,
            'solved_count': solved_count,
            'total_count': len(self.numbers),
            'total_error': sum(r['error'] for r in results)
        }


if __name__ == "__main__":
    # Test optimization
    print("Testing Optimizer on range -10 to 10")
    print("=" * 60)
    
    optimizer = LetterValueOptimizer(-10, 10, population_size=50)
    
    def progress_callback(stats):
        print(f"Gen {stats['generation']:3d}: "
              f"Solved {stats['solved_count']:2d}/{stats['total_numbers']:2d}, "
              f"Fitness: {stats['best_fitness']:.2f}, "
              f"Max Error: {stats['max_error']:.2f}")
    
    best_solution = optimizer.optimize(max_generations=50, callback=progress_callback)
    
    print("\n" + "=" * 60)
    print("Best Solution Found:")
    print("=" * 60)
    
    if best_solution:
        for letter, value in sorted(best_solution.items()):
            print(f"{letter}: {value:7.3f}")
        
        details = optimizer.get_solution_details()
        if details:
            print(f"\nSolved {details['solved_count']} out of {details['total_count']} numbers")
            print(f"Total Error: {details['total_error']:.2f}")
        else:
            print("\nNo details available")
    else:
        print("No solution found")
