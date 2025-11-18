"""
Optimization Solver
Uses SciPy L-BFGS-B with analytical gradients for maximum performance.
"""

import numpy as np
from scipy.optimize import minimize
from typing import List, Tuple, Dict, Callable, Optional
import time
import concurrent.futures
import os
from .parser import SpellingParser
from .number_to_words import number_to_words

class Optimizer:
    def __init__(self, start: int, end: int, 
                 space_operator='auto', hyphen_operator='minus',
                 allow_negative=True, cpu_usage='auto',
                 callback: Optional[Callable] = None):
        self.start = start
        self.end = end
        self.numbers = list(range(start, end + 1))
        self.parser = SpellingParser(space_operator=space_operator, hyphen_operator=hyphen_operator)
        self.callback = callback
        self.allow_negative = allow_negative
        
        # Determine workers
        if cpu_usage == 'auto':
            # Gentle auto: use half of available cores to prevent lag
            self.workers = max(1, (os.cpu_count() or 1) // 2)
        elif cpu_usage == 'max':
             self.workers = max(1, (os.cpu_count() or 1) - 1)
        else:
            try:
                self.workers = int(cpu_usage)
            except:
                self.workers = 1
        
        # Pre-compile structure for fast evaluation and gradient computation
        # Structure: List of (target, List of (coeff, counts_array))
        # counts_array is size 26, containing exponent of each letter in the term
        self.compiled_data = []
        self.letters = [chr(65+i) for i in range(26)]
        
        print("Compiling number structures...")
        for num in self.numbers:
            spelling = number_to_words(num)
            terms = self.parser.compile_to_terms(spelling)
            
            compiled_terms = []
            for coeff, indices in terms:
                counts = np.zeros(26, dtype=np.float64)
                for idx in indices:
                    counts[idx] += 1
                compiled_terms.append((coeff, counts))
            
            self.compiled_data.append((num, compiled_terms))
        print(f"Compiled {len(self.compiled_data)} numbers.")

    def objective_function(self, x):
        """
        Returns tuple (total_error, gradient)
        x is array of 26 floats (A-Z)
        """
        total_error = 0.0
        gradient = np.zeros(26, dtype=np.float64)
        
        for target, terms in self.compiled_data:
            # Calculate value of this number
            calc_value = 0.0
            term_values = [] # Store for gradient calc
            
            for coeff, counts in terms:
                # term_val = coeff * product(x^counts)
                
                # Optimization: only compute for non-zero counts
                term_val = coeff
                for i in range(26):
                    if counts[i] > 0:
                        term_val *= (x[i] ** counts[i])
                
                calc_value += term_val
                term_values.append(term_val)
            
            diff = calc_value - target
            total_error += diff ** 2
            
            two_diff = 2 * diff
            for i, (coeff, counts) in enumerate(terms):
                term_val = term_values[i]
                
                for k in range(26):
                    c_k = counts[k]
                    if c_k == 0:
                        continue
                    
                    # Calculate partial derivative of this term w.r.t x[k]
                    if abs(x[k]) > 1e-10:
                        grad_term = term_val * c_k / x[k]
                    else:
                        # Special case x[k] ~ 0
                        if c_k == 1:
                            # Derivative is coeff * product(others)
                            # Recompute without x[k]
                            grad_term = coeff
                            for j in range(26):
                                if j != k and counts[j] > 0:
                                    grad_term *= (x[j] ** counts[j])
                        else:
                            # c_k > 1, derivative contains factor x[k]^(c_k-1) which is 0
                            grad_term = 0.0
                    
                    gradient[k] += two_diff * grad_term

        return total_error, gradient

    def _generate_smart_guess(self):
        """
        Generates a smart initial guess using Log-Linear Least Squares.
        Approximates the problem as purely multiplicative: Product(Letters) = Target
        ln(Product) = ln(Target) -> Sum(ln(Letter)) = ln(Target)
        This is a linear system Ax = b where x is ln(Letter).
        """
        rows = []
        b = []
        
        for target, terms in self.compiled_data:
            # Only use positive targets and single-term numbers (pure products) for initialization
            if target <= 0: continue
            if len(terms) == 1:
                coeff, counts = terms[0]
                if coeff <= 0: continue
                
                rows.append(counts)
                b.append(np.log(target) - np.log(coeff))
        
        # We need enough equations to solve for 26 variables
        if len(rows) < 10:
            return None
            
        try:
            A = np.array(rows)
            B = np.array(b)
            # Solve A * ln_x = B
            ln_x, _, _, _ = np.linalg.lstsq(A, B, rcond=None)
            
            # Convert back: x = exp(ln_x)
            x = np.exp(ln_x)
            
            # Handle bounds/NaNs
            x = np.nan_to_num(x, nan=1.0, posinf=10.0, neginf=0.1)
            return x
        except Exception as e:
            print(f"Smart guess failed: {e}")
            return None

    def _run_single_optimization(self, seed, initial_guess=None):
        np.random.seed(seed)
        
        if initial_guess is None:
            # Random initialization between -5 and 5 (or 0 and 5 if no negative)
            if self.allow_negative:
                initial_guess = np.random.uniform(-5, 5, 26)
            else:
                initial_guess = np.random.uniform(0, 10, 26)
            
        bounds = [(-100, 100) if self.allow_negative else (0, 100) for _ in range(26)]
        
        result = minimize(
            self.objective_function,
            initial_guess,
            method='L-BFGS-B',
            jac=True,
            bounds=bounds,
            options={'maxiter': 2000, 'ftol': 1e-12, 'gtol': 1e-12}
        )
        return result

    def solve(self, max_iter=1000):
        start_time = time.time()
        
        # Multi-start optimization
        # We run multiple optimizations in parallel with different random seeds
        
        num_starts = self.workers # Reduced from *2 to save resources
        seeds = [int(time.time()) + i for i in range(num_starts)]
        
        best_result = None
        best_error = float('inf')
        
        print(f"Starting multi-start optimization with {num_starts} runs on {self.workers} workers...")
        
        # Generate smart guess
        smart_guess = self._generate_smart_guess()
        if smart_guess is not None:
            print("Smart geometric initialization generated.")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = []
            
            # 1. Submit smart guess run (if available)
            if smart_guess is not None:
                futures.append(executor.submit(self._run_single_optimization, seeds[0], smart_guess))
                # Use remaining seeds for random starts
                remaining_seeds = seeds[1:]
            else:
                remaining_seeds = seeds
            
            # 2. Submit random runs
            for seed in remaining_seeds:
                futures.append(executor.submit(self._run_single_optimization, seed))
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    # Check if we should stop (via callback check)
                    if self.callback:
                        try:
                            # Dummy call to check status
                            self.callback({'x': np.zeros(26), 'error': 0, 'time': 0})
                        except StopIteration:
                            print("Optimization stopped by user.")
                            executor.shutdown(wait=False, cancel_futures=True)
                            return {'success': False, 'message': "Stopped by user", 'x': np.zeros(26), 'fun': 0, 'nit': 0, 'letter_map': {}}

                    res = future.result()
                    if res.fun < best_error:
                        best_error = res.fun
                        best_result = res
                        
                        # Report progress if we found a better solution
                        if self.callback:
                            self.callback({
                                'x': best_result.x,
                                'error': best_error,
                                'time': time.time() - start_time
                            })
                            
                        # If we found a perfect solution, we can stop early
                        if best_error < 1e-6:
                            print("Perfect solution found!")
                            executor.shutdown(wait=False, cancel_futures=True)
                            break 
                except Exception as e:
                    print(f"Optimization run failed: {e}")

        if best_result is None:
            # Fallback if everything failed
            return {'success': False, 'message': "All runs failed", 'x': np.zeros(26), 'fun': float('inf'), 'nit': 0, 'letter_map': {}}

        return {
            'success': best_result.success,
            'message': best_result.message,
            'x': best_result.x,
            'fun': best_result.fun,
            'nit': best_result.nit,
            'letter_map': {self.letters[i]: best_result.x[i] for i in range(26)}
        }

