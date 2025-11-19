"""
Analytical Hybrid Solver (The "1000x" Speed Update)
---------------------------------------------------
Strategy:
1. ANALYTICAL STAGE (Deep Logic):
   a. Solves for 'Word Values' first (e.g. finds "Twenty"=20 from "Twenty-one"=21).
   b. Solves for 'Letter Values' using Log-Linear Algebra on those words.
   This step usually finds the solution in < 0.05 seconds.

2. NUMERICAL STAGE (Snap & Flip):
   a. If Analytical result is close, it 'Snaps' to integers and 'Flips' signs 
      to correct for the sign-loss in logarithms.
      
3. HIVE MIND (Fallback):
   a. Only activates if the math solver fails (rare).
   b. Uses extremely aggressive convergence settings.
"""

import numpy as np
from scipy.optimize import minimize
import time
import concurrent.futures
import multiprocessing
import os
import sys
import psutil
import threading
from typing import List, Dict, Callable, Optional, Any, Union

# Ensure project root is in path for worker processes
# This helps if the worker process doesn't inherit the path correctly on Windows
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import local modules
from src.core.parser import SpellingParser
from src.core.number_to_words import number_to_words

# --- Safety Helper ---
def get_safe_cpu_count() -> int:
    try:
        count = os.cpu_count()
        if count is None or count < 1:
            return 1
        return int(count)
    except:
        return 1

# --- Math Kernels ---

def vectorized_objective(x: np.ndarray, term_coeffs: np.ndarray, term_powers: np.ndarray, 
                         term_indices: np.ndarray, targets: np.ndarray, num_numbers: int):
    """
    Calculates Error and Analytical Gradient.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    
    # 1. Calculate term values
    try:
        # Fast path
        bases = np.power(x_arr, term_powers)
        term_values = term_coeffs * np.prod(bases, axis=1)
    except Exception:
        # Robust path for edge cases
        term_values = term_coeffs.copy()
        for i in range(len(x_arr)):
            mask = term_powers[:, i] != 0
            if np.any(mask):
                term_values[mask] *= np.power(x_arr[i], term_powers[mask, i])

    # 2. Sum terms
    calc_values = np.zeros(num_numbers, dtype=np.float64)
    np.add.at(calc_values, term_indices, term_values)
    
    # 3. Residuals
    diffs = calc_values - targets
    total_error = np.sum(np.square(diffs))
    
    # 4. Gradient
    # dE/dx = 2 * sum( diff * d(Val)/dx )
    term_diffs = diffs[term_indices] 
    pv = 2.0 * term_diffs * term_values 
    grad_numer = np.dot(pv, term_powers)
    
    with np.errstate(divide='ignore', invalid='ignore'):
        # Avoid div by zero
        safe_x = np.where(np.abs(x_arr) < 1e-12, 1e-12, x_arr)
        gradient = grad_numer / safe_x
        # If x was really 0, gradient is usually 0 unless power is negative/singular
        gradient = np.where(np.abs(x_arr) < 1e-12, 0.0, gradient)

    return total_error, gradient

def solve_sign_flipping(x_start, task_args, max_flips=500):
    """
    Rapidly searches for the correct sign combination.
    Log-linear solvers find the magnitude |x| correctly, but miss the sign.
    This brute-forces the optimal sign configuration.
    """
    best_x = x_start.copy()
    best_err, _ = vectorized_objective(best_x, *task_args)
    
    if best_err < 1e-5: return best_x, best_err

    # 1. Try flipping each variable individually
    current_x = best_x.copy()
    for i in range(26):
        current_x[i] *= -1
        err, _ = vectorized_objective(current_x, *task_args)
        if err < best_err:
            best_err = err
            best_x = current_x.copy()
        else:
            current_x[i] *= -1 # Flip back

    if best_err < 1e-5: return best_x, best_err
    
    # 2. Random subset flips
    for _ in range(max_flips):
        test_x = best_x.copy()
        # Flip 2 to 5 random variables
        n_flips = np.random.randint(2, 6)
        idxs = np.random.choice(26, n_flips, replace=False)
        test_x[idxs] *= -1
        
        err, _ = vectorized_objective(test_x, *task_args)
        if err < best_err:
            best_err = err
            best_x = test_x.copy()
            if best_err < 1e-5: break
            
    return best_x, best_err

def worker_task(seed: int, bounds: List, shared_data: Any, task_args: tuple):
    """
    Worker task that prioritizes "Snap & Flip" over random searching.
    """
    np.random.seed(seed)
    
    best_x = None
    best_err = float('inf')
    
    if shared_data is not None:
        try:
            best_x = shared_data.get('best_x')
            best_err = shared_data.get('best_err', float('inf'))
        except: pass

    # --- STRATEGY: INTELLIGENT REFINEMENT ---
    if best_x is not None:
        # 1. Snap to Integer and Solve Signs
        x_round = np.round(best_x)
        x_final, err_final = solve_sign_flipping(x_round, task_args)
        
        if err_final < 1e-5:
            return {'success': True, 'x': x_final, 'fun': err_final, 'nit': 0}
            
        # 2. Gradient Descent with Jitter
        # If signs didn't fix it, maybe magnitude is slightly off
        jitter = np.random.normal(0, 0.2, 26)
        initial_guess = best_x + jitter
    else:
        initial_guess = np.random.uniform(bounds[0][0], bounds[0][1], 26)

    try:
        # DEBUG: Print to console to verify worker start
        print(f"Worker started with seed {seed}", file=sys.__stdout__)
        
        result = minimize(
            vectorized_objective,
            initial_guess,
            args=task_args,
            method='L-BFGS-B',
            jac=True,
            bounds=bounds,
            options={'maxiter': 100, 'ftol': 1e-5, 'gtol': 1e-5}
        )
        
        # Try to fix signs on the result
        x_fixed, err_fixed = solve_sign_flipping(result.x, task_args, max_flips=50)
        
        final_res = {
            'success': err_fixed < 1e-3,
            'x': x_fixed,
            'fun': err_fixed,
            'nit': result.nit
        }

        # Update Hive Mind
        if shared_data is not None:
            try:
                if err_fixed < shared_data.get('best_err', float('inf')):
                    shared_data['best_x'] = x_fixed
                    shared_data['best_err'] = err_fixed
            except: pass

        return final_res
    except Exception as e:
        print(f"Worker error: {e}", file=sys.__stdout__)
        return {'success': False, 'error': str(e), 'fun': float('inf')}

class Optimizer:
    def __init__(self, start: int, end: int, 
                 space_operator='auto', hyphen_operator='minus',
                 allow_negative=True, cpu_usage='auto',
                 callback: Optional[Callable] = None):
        
        self.start = start
        self.end = end
        self.numbers = list(range(start, end + 1))
        self.allow_negative = allow_negative
        if not self.allow_negative:
            self.numbers = [n for n in self.numbers if n >= 0]
            
        self.parser = SpellingParser(space_operator=space_operator, hyphen_operator=hyphen_operator)
        self.callback = callback
        self.cpu_usage_setting = cpu_usage
        self.letters = [chr(65+i) for i in range(26)]
        
        self._compile_terms()
        
        self.running = False
        self.should_stop = False
        self.max_allowed_workers = 1
        self.current_workers = 0

    def _compile_terms(self):
        """Converts words to mathematical arrays."""
        coeffs = []
        powers = []
        indices = []
        targets = []
        
        print(f"Compiling math for numbers {self.numbers[0]} to {self.numbers[-1]}...")
        
        for i, num in enumerate(self.numbers):
            spelling = number_to_words(num)
            terms = self.parser.compile_to_terms(spelling)
            targets.append(num)
            
            for coeff, letter_idxs in terms:
                p = np.zeros(26, dtype=np.int32)
                for idx in letter_idxs:
                    p[idx] += 1
                coeffs.append(coeff)
                powers.append(p)
                indices.append(i)
                
        self.term_coeffs = np.array(coeffs, dtype=np.float64)
        self.term_powers = np.array(powers, dtype=np.int32)
        self.term_indices = np.array(indices, dtype=np.int32)
        self.targets = np.array(targets, dtype=np.float64)
        self.num_numbers = len(self.numbers)

    def _solve_analytical(self):
        """
        Two-Stage Analytical Solver (The "Deep Logic").
        Stage 1: Solve for Word Values (Linear Algebra).
        Stage 2: Solve for Letter Values (Log-Linear Algebra).
        """
        try:
            print("Running Analytical Solver Stage 1: Solving for Words...")
            # 1. Identify Unique Terms (Word signatures)
            # We need to group identical rows in term_powers
            # term_powers is (N_terms, 26). We want unique rows.
            
            # Convert rows to bytes for hashing
            term_bytes = [t.tobytes() for t in self.term_powers]
            unique_hashes, unique_indices, unique_inverse = np.unique(term_bytes, return_index=True, return_inverse=True)
            num_unique_terms = len(unique_hashes)
            
            # Build Matrix A: (num_numbers x num_unique_terms)
            # Equation: Number = Sum(Coeff * Term)
            A_words = np.zeros((self.num_numbers, num_unique_terms), dtype=np.float64)
            b_targets = self.targets
            
            for k in range(len(self.term_coeffs)):
                row = self.term_indices[k]
                col = unique_inverse[k]
                val = self.term_coeffs[k]
                A_words[row, col] += val
                
            # Solve A * w = b for w (Word Values) using Least Squares
            word_values, residuals, rank, s = np.linalg.lstsq(A_words, b_targets, rcond=None)
            
            print(f"Stage 1 Complete. Found {num_unique_terms} unique word values.")
            
            # Stage 2: Solve for Letters
            # Equation: Product(Letters) = WordValue
            # Log-Eq: Sum(Count * Log(Letter)) = Log(WordValue)
            
            # We need to reconstruct the letter counts for the unique terms
            # We pick the first occurrence of each unique hash
            unique_powers = self.term_powers[unique_indices]
            
            # Filter out non-positive word values (cannot log them)
            # We take abs because sign is handled separately usually, 
            # or we just assume words are positive magnitudes.
            valid_mask = np.abs(word_values) > 1e-9
            
            if not np.any(valid_mask): return None
            
            A_log = unique_powers[valid_mask]
            b_log = np.log(np.abs(word_values[valid_mask]))
            
            # Solve for log(letters)
            log_x, _, _, _ = np.linalg.lstsq(A_log, b_log, rcond=None)
            
            # Exponentiate
            x_guess = np.exp(log_x)
            
            # Handle unobserved letters (set to default)
            col_sums = np.sum(A_log, axis=0)
            x_guess = np.where(col_sums > 0, x_guess, 10.0)
            
            # Apply sign correction immediately
            task_args = (self.term_coeffs, self.term_powers, self.term_indices, self.targets, self.num_numbers)
            x_final, err = solve_sign_flipping(x_guess, task_args, max_flips=1000)
            
            print(f"Analytical Solution Found. Error: {err}")
            return x_final, err
            
        except Exception as e:
            print(f"Analytical solver failed: {e}")
            return None

    def _cpu_governor(self):
        p = psutil.Process(os.getpid())
        while self.running and not self.should_stop:
            try:
                sys_load = psutil.cpu_percent(interval=1.0)
                count = get_safe_cpu_count()
                if sys_load > 90:
                    if self.max_allowed_workers > 1: self.max_allowed_workers -= 1
                elif sys_load < 75:
                    if self.max_allowed_workers < count: self.max_allowed_workers += 1
                
                if self.callback:
                    # Send worker info in a format the UI expects
                    self.callback({
                        'workers': self.current_workers,
                        'auto_worker_info': {
                            'workers': self.current_workers,
                            'cpu_percent': sys_load,
                            'reason': 'Auto-adjustment'
                        }
                    })
            except: pass

    def solve(self):
        self.running = True
        self.should_stop = False
        start_time = time.time()
        
        if self.callback:
            self.callback({'log': "Initializing optimizer..."})

        threading.Thread(target=self._cpu_governor, daemon=True).start()
        
        task_args = (self.term_coeffs, self.term_powers, self.term_indices, self.targets, self.num_numbers)
        bounds = [(-100, 100) if self.allow_negative else (0, 100) for _ in range(26)]
        
        # 1. TRY ANALYTICAL SOLVER FIRST
        if self.callback:
            self.callback({'log': "Running Analytical Solver (Stage 1)..."})
            
        ana_x, ana_err = self._solve_analytical() or (None, float('inf'))
        
        if ana_err < 1e-5:
            if self.callback:
                self.callback({'log': "Analytical Solver found exact solution!"})
            return self._pack_result(ana_x, ana_err, 1, start_time)
            
        # 1.5 REFINEMENT STAGE (New)
        if ana_x is not None:
            if self.callback:
                self.callback({'log': "Analytical result approximate. Running Gradient Refinement..."})
            
            # Try to refine the analytical guess using L-BFGS-B locally before swarming
            try:
                res = minimize(
                    vectorized_objective,
                    ana_x,
                    args=task_args,
                    method='L-BFGS-B',
                    jac=True,
                    bounds=bounds,
                    options={'maxiter': 200, 'ftol': 1e-9, 'gtol': 1e-9}
                )
                # Check signs again
                x_refined, err_refined = solve_sign_flipping(res.x, task_args, max_flips=200)
                
                if err_refined < 1e-5:
                    if self.callback:
                        self.callback({'log': "Gradient Refinement successful!"})
                    return self._pack_result(x_refined, err_refined, res.nit, start_time)
                
                # Update best guess
                ana_x = x_refined
                ana_err = err_refined
            except Exception as e:
                print(f"Refinement failed: {e}")

        if self.callback:
            self.callback({'log': "Starting Swarm Optimization (Hive Mind)..."})

        # 2. START SWARM (Fall back if analytical wasn't perfect)
        # We use a simpler executor model to avoid Manager() issues on Windows for now
        
        total_cores = get_safe_cpu_count()
        self.max_allowed_workers = max(1, total_cores - 1)
        
        best_global_x = ana_x if ana_x is not None else np.zeros(26)
        best_global_err = ana_err
        attempts = 0
        last_update = time.time()
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=total_cores) as executor:
            futures = set()
            
            while not self.should_stop:
                # Check results
                done, _ = concurrent.futures.wait(futures, timeout=0.02, return_when=concurrent.futures.FIRST_COMPLETED)
                
                for future in done:
                    futures.remove(future)
                    self.current_workers -= 1
                    attempts += 1
                    try:
                        res = future.result()
                        if res['success'] or res['fun'] < best_global_err:
                            if res['fun'] < best_global_err:
                                best_global_err = res['fun']
                                best_global_x = res['x']
                                
                                # Immediate update on improvement
                                if self.callback:
                                    self.callback({
                                        'x': best_global_x, 
                                        'error': best_global_err, 
                                        'attempts': attempts,
                                        'log': f"New best found! Error: {best_global_err:.6f}"
                                    })
                            
                            if best_global_err < 1e-5:
                                self.running = False
                                return self._pack_result(best_global_x, best_global_err, attempts, start_time)
                            
                    except Exception as e:
                        # Log the worker crash
                        if self.callback:
                            self.callback({'log': f"Worker crashed: {e}"})

                # Submit
                target = self.max_allowed_workers
                if len(futures) < target:
                    self.current_workers += 1
                    # Ensure seed is within 32-bit integer range (0 to 2**32 - 1)
                    seed = (int(time.time() * 1000000) + attempts) % (2**32 - 1)
                    # Pass None for shared_data to avoid Manager issues
                    futures.add(executor.submit(worker_task, seed, bounds, None, task_args))
                
                if best_global_err < 1e-9: break
                
                # Regular updates
                now = time.time()
                if self.callback and (now - last_update > 0.1): # Update every 100ms
                    self.callback({
                        'check_stop': True,
                        'attempts': attempts,
                        'workers': self.current_workers,
                        'speed': attempts / (now - start_time) if (now - start_time) > 0 else 0,
                        'error': best_global_err,
                        'x': best_global_x
                    })
                    last_update = now

        self.running = False
        return self._pack_result(best_global_x, best_global_err, attempts, start_time)

    def _pack_result(self, x, error, attempts, start_time):
        if x is None: x = np.zeros(26)
        x_final = np.round(x) if error < 0.1 else x
        return {
            'success': error < 1e-3,
            'x': x_final,
            'fun': error,
            'nit': 0,
            'letter_map': {self.letters[i]: float(x_final[i]) for i in range(26)},
            'attempts': attempts,
            'duration': time.time() - start_time
        }

    def stop(self):
        self.should_stop = True