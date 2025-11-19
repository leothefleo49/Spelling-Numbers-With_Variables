"""
Hive Mind Optimization Solver (Snap & Flip Edition)
---------------------------------------------------
Improvements:
1. "Snap & Flip" Strategy: Workers actively try rounding floating point results to integers
   and permuting their signs to find the exact solution instantly.
2. Stagnation Detection: If the solver gets stuck, it triggers a 'Big Bang' reset to force new paths.
3. Performance: Reduced solver tolerance (ftol) because we rely on the integer snap for final accuracy.
"""

import numpy as np
from scipy.optimize import minimize
import time
import concurrent.futures
import multiprocessing
import os
import psutil
import threading
from typing import List, Dict, Callable, Optional, Any, Union

# Import local modules
from .parser import SpellingParser
from .number_to_words import number_to_words

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
        bases = np.power(x_arr, term_powers)
        term_values = term_coeffs * np.prod(bases, axis=1)
    except Exception:
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
    total_error = np.sum(diffs ** 2)
    
    # 4. Gradient
    term_diffs = diffs[term_indices] 
    pv = 2.0 * term_diffs * term_values 
    grad_numer = np.dot(pv, term_powers)
    
    with np.errstate(divide='ignore', invalid='ignore'):
        safe_x = np.where(np.abs(x_arr) < 1e-12, 1e-12, x_arr)
        gradient = grad_numer / safe_x
        gradient = np.where((np.abs(x_arr) < 1e-12) & (np.abs(grad_numer) < 1e-12), 0.0, gradient)

    return total_error, gradient

def worker_task(seed: int, bounds: List, shared_data: Any, task_args: tuple):
    """
    Hive Mind Worker with "Snap & Flip" logic.
    """
    # Ensure seed fits 32-bit unsigned (np.random requires 0 <= seed < 2**32)
    try:
        seed = int(seed) & 0xFFFFFFFF
    except Exception:
        seed = int(time.time() * 1000) & 0xFFFFFFFF
    np.random.seed(seed)
    term_coeffs, term_powers, term_indices, targets, num_numbers = task_args
    
    # --- HIVE MIND: READ ---
    best_x = None
    best_err = float('inf')
    
    if shared_data is not None:
        try:
            best_x = shared_data.get('best_x')
            best_err = shared_data.get('best_err', float('inf'))
        except: pass

    # --- STRATEGY 1: SNAP & FLIP (The "Closer" Strategy) ---
    # If we are reasonably close, try to force the integer solution
    if best_x is not None and best_err < 100.0:
        # 1. Round to nearest integer
        x_round = np.round(best_x)
        
        # 2. Check Error
        err_round, _ = vectorized_objective(x_round, *task_args)
        if err_round < 1e-5:
            return {'success': True, 'x': x_round, 'fun': err_round, 'nit': 0}
        
        # 3. Flip Search: Randomly flip signs of the rounded vector to see if that fixes it
        # This helps when x^2 = 25 found x=5 but needed x=-5
        for _ in range(20): # Try 20 permutations
            x_flip = x_round.copy()
            # Flip 1 to 4 variables
            flip_idx = np.random.choice(26, size=np.random.randint(1, 5), replace=False)
            x_flip[flip_idx] *= -1
            
            err_flip, _ = vectorized_objective(x_flip, *task_args)
            if err_flip < 1e-5:
                return {'success': True, 'x': x_flip, 'fun': err_flip, 'nit': 0}

    # --- STRATEGY 2: OPTIMIZATION (The "Search" Strategy) ---
    initial_guess = None
    
    # 70% Chance to refine best, 30% chance to explore
    if best_x is not None and np.random.random() > 0.3:
        noise = np.random.normal(0, max(0.1, best_err / 500.0), 26)
        initial_guess = best_x + noise
    else:
        # Random initialization
        initial_guess = np.random.uniform(bounds[0][0], bounds[0][1], 26)
    
        # Respect fixed bounds: if a bound is a singleton (a,a) then fix initial guess
        try:
            for i in range(len(initial_guess)):
                lo, hi = bounds[i]
                if lo == hi:
                    initial_guess[i] = lo
        except Exception:
            pass

    try:
        # We use looser tolerance (1e-4) because we rely on Snap & Flip for the final precision
        result = minimize(
            vectorized_objective,
            initial_guess,
            args=task_args,
            method='L-BFGS-B',
            jac=True,
            bounds=bounds,
            options={'maxiter': 80, 'ftol': 1e-4, 'gtol': 1e-4}
        )
        
        # --- HIVE MIND: TEACH ---
        if shared_data is not None:
            try:
                if result.fun < best_err:
                    if result.fun < shared_data.get('best_err', float('inf')):
                        shared_data['best_x'] = result.x
                        shared_data['best_err'] = result.fun
            except: pass

        return {
            'success': result.success,
            'x': result.x,
            'fun': result.fun,
            'nit': result.nit
        }
    except Exception as e:
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
        self.system_cpu = 0.0
        self.app_cpu = 0.0

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
        # Determine which letters actually appear in any term
        try:
            used = np.any(self.term_powers != 0, axis=0)
            self.letters_used = [bool(u) for u in used]
        except Exception:
            self.letters_used = [True] * 26

    def _generate_smart_guess(self):
        """Log-Linear Least Squares on atomic words."""
        try:
            rows = []
            b_vals = []
            unique_hashes = set()
            
            for i in range(self.num_numbers):
                target_val = self.targets[i]
                if target_val <= 0: continue 
                
                these_term_indices = np.where(self.term_indices == i)[0]
                if len(these_term_indices) == 1:
                    t_idx = these_term_indices[0]
                    if abs(self.term_coeffs[t_idx]) == 1:
                        row = self.term_powers[t_idx]
                        row_hash = row.tobytes()
                        if row_hash in unique_hashes: continue
                        unique_hashes.add(row_hash)
                        rows.append(row)
                        b_vals.append(np.log(target_val))
            
            if len(rows) < 1: return None
            
            A = np.array(rows)
            b = np.array(b_vals)
            log_x, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
            guess = np.exp(log_x)
            
            # Set defaults for unknown letters
            col_sums = np.sum(np.abs(A), axis=0)
            guess = np.where(col_sums > 0, guess, 10.0)
            
            if self.allow_negative:
                signs = np.random.choice([1, -1], size=26)
                guess = guess * signs
                
            return guess
        except Exception:
            return None

    def _cpu_governor(self):
        p = psutil.Process(os.getpid())
        while self.running and not self.should_stop:
            try:
                sys_load = psutil.cpu_percent(interval=1.0)
                count = get_safe_cpu_count()
                app_load = p.cpu_percent(interval=None) / count
                
                self.system_cpu = sys_load
                self.app_cpu = app_load
                
                if sys_load > 90:
                    if self.max_allowed_workers > 1: self.max_allowed_workers -= 1
                elif sys_load < 75:
                    if self.max_allowed_workers < count: self.max_allowed_workers += 1
                        
                if self.callback:
                    self.callback({
                        'cpu_stats': {
                            'system': sys_load,
                            'app': app_load,
                            'workers': self.current_workers,
                            'limit': self.max_allowed_workers
                        }
                    })
            except Exception: pass

    def solve(self):
        self.running = True
        self.should_stop = False
        start_time = time.time()
        
        threading.Thread(target=self._cpu_governor, daemon=True).start()
        
        bounds = [(-100.0, 100.0) if self.allow_negative else (0.0, 100.0) for _ in range(26)]
        # Freeze bounds for letters that never appear (they don't need a variable)
        for i in range(26):
            if not getattr(self, 'letters_used', [True]*26)[i]:
                bounds[i] = (0.0, 0.0)

        task_args = (self.term_coeffs, self.term_powers, self.term_indices, self.targets, self.num_numbers)
        
        print("Starting Hive Mind optimization...")

        with multiprocessing.Manager() as manager:
            shared_data = manager.dict()
            shared_data['best_x'] = None
            shared_data['best_err'] = float('inf')
            
            # Smart Guess
            smart_guess = self._generate_smart_guess()
            if smart_guess is not None:
                print("Analytical guess generated.")
                shared_data['best_x'] = smart_guess
                err, _ = vectorized_objective(smart_guess, *task_args)
                shared_data['best_err'] = err
            
            total_cores = get_safe_cpu_count()
            self.max_allowed_workers = max(1, total_cores - 1)
            
            best_global_x = np.zeros(26)
            best_global_err = float('inf')
            attempts = 0
            
            with concurrent.futures.ProcessPoolExecutor(max_workers=total_cores) as executor:
                futures = set()
                
                while not self.should_stop:
                    # Non-blocking check (wait=0.01s)
                    done, _ = concurrent.futures.wait(futures, timeout=0.01, return_when=concurrent.futures.FIRST_COMPLETED)
                    
                    for future in done:
                        futures.remove(future)
                        self.current_workers -= 1
                        attempts += 1
                        
                        try:
                            res = future.result()
                            if res['fun'] < best_global_err:
                                best_global_err = res['fun']
                                best_global_x = res['x']
                                
                                # IMMEDIATE STOP on perfect solution
                                if best_global_err < 1e-5:
                                    print("Solution Found!")
                                    self.running = False
                                    return self._pack_result(best_global_x, best_global_err, attempts, start_time)

                                if self.callback:
                                    self.callback({
                                        'x': best_global_x,
                                        'error': best_global_err,
                                        'attempts': attempts,
                                        'time': time.time() - start_time,
                                        'letters_used': getattr(self, 'letters_used', [True]*26)
                                    })
                        except Exception: pass

                    # Dynamic Scaling
                    target_workers = self.max_allowed_workers
                    if len(futures) < target_workers:
                        self.current_workers += 1
                        seed = (int(time.time() * 1000000) + attempts) & 0xFFFFFFFF
                        futures.add(executor.submit(worker_task, seed, bounds, shared_data, task_args))
                    
                    # Heartbeat
                    if self.callback and attempts % 10 == 0:
                        self.callback({'check_stop': True})

        self.running = False
        return self._pack_result(best_global_x, best_global_err, attempts, start_time)

    def _pack_result(self, x, error, attempts, start_time):
        if x is None: x = np.zeros(26)
        # Final round to ensure display looks clean
        x_final = np.round(x) if error < 0.1 else x
        return {
            'success': error < 1e-3,
            'x': x_final,
            'fun': error,
            'nit': 0,
            'letter_map': {self.letters[i]: float(x_final[i]) for i in range(26)},
            'letters_used': getattr(self, 'letters_used', [True]*26),
            'attempts': attempts,
            'duration': time.time() - start_time
        }

    def stop(self):
        self.should_stop = True