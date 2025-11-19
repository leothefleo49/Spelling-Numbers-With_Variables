"""
Hive Mind Optimization Solver (Type-Safe Version)
-------------------------------------------------
Features:
1. Analytical Gradient L-BFGS-B (Mathematical exactness for speed).
2. Hive Mind Strategy: Workers share the "Best Candidate" in real-time.
3. Dynamic CPU Governor: Auto-scales worker count based on live System vs App load.
4. Full Negative Number Support.
5. Robust Type Safety (Fixes Pylance/NoneType errors).
"""

import numpy as np
from scipy.optimize import minimize
from typing import List, Tuple, Dict, Callable, Optional, Any, Union
import time
import sys
import concurrent.futures
import multiprocessing
import os
import psutil
import math
import threading
from .parser import SpellingParser
from .number_to_words import number_to_words

# --- Math Kernels (Global for Multiprocessing Pickling) ---

def vectorized_objective(x, term_coeffs, term_powers, term_indices, targets, num_numbers):
    """
    Calculates Error and Exact Analytical Gradient.
    Handles negative numbers correctly.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    
    # 1. Calculate value of every term: coeff * product(x_i ^ p_i)
    try:
        # Broadcasting x over term_powers
        bases = np.power(x_arr, term_powers) 
        term_values = term_coeffs * np.prod(bases, axis=1)
    except Exception:
        # Fallback for safety
        term_values = term_coeffs.copy()
        for i in range(26):
            mask = term_powers[:, i] != 0
            term_values[mask] *= (x_arr[i] ** term_powers[mask, i])

    # 2. Sum terms to get value for each number
    calc_values = np.zeros(num_numbers, dtype=np.float64)
    np.add.at(calc_values, term_indices, term_values)
    
    # 3. Calculate Error (Residuals)
    diffs = calc_values - targets
    total_error = np.sum(diffs ** 2)
    
    # 4. Calculate Gradient (Analytical differentiation)
    term_diffs = diffs[term_indices]  # Map number diffs back to terms
    
    with np.errstate(divide='ignore', invalid='ignore'):
        # Efficient gradient calculation:
        # Grad_k = Sum_terms ( 2 * diff * term_val * power_k / x_k )
        
        pv = 2.0 * term_diffs * term_values # Shape: (N_terms,)
        
        # We need to multiply pv by (powers / x)
        weighted_powers = term_powers * pv[:, np.newaxis]
        
        # Sum over terms for each letter
        grad_numer = np.sum(weighted_powers, axis=0)
        
        # Final divide by x
        safe_x = np.where(np.abs(x_arr) < 1e-10, 1e-10, x_arr)
        gradient = grad_numer / safe_x
        
        # Fix gradient where x was effectively 0 to prevent explosion
        gradient = np.where(np.abs(x_arr) < 1e-10, 0.0, gradient)

    return total_error, gradient


def compute_per_number_values(x, term_coeffs, term_powers, term_indices, targets, num_numbers):
    """
    Compute the per-number calculated values (not the total error).
    Returns a numpy array of length `num_numbers`.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    try:
        bases = np.power(x_arr, term_powers)
        term_values = term_coeffs * np.prod(bases, axis=1)
    except Exception:
        term_values = term_coeffs.copy()
        for i in range(26):
            mask = term_powers[:, i] != 0
            term_values[mask] *= (x_arr[i] ** term_powers[mask, i])

    calc_values = np.zeros(num_numbers, dtype=np.float64)
    np.add.at(calc_values, term_indices, term_values)
    return calc_values

def worker_task(seed, bounds, shared_data, task_args):
    """
    The Worker Drone.
    1. Checks Shared Memory for the current best solution (Hive Mind).
    2. Mutates it slightly (Exploration).
    3. Runs Gradient Descent (Exploitation).
    4. Reports back if it found something better.
    """
    # Ensure seed is a valid 32-bit unsigned integer (required by numpy)
    try:
        seed = int(seed) & 0xFFFFFFFF
    except Exception:
        seed = int(time.time()) & 0xFFFFFFFF
    np.random.seed(seed)
    
    # --- HIVE MIND: READ ---
    # Check if the swarm found a good spot. If so, start there.
    best_x_so_far = shared_data.get('best_x', None)
    best_err_so_far = shared_data.get('best_err', float('inf'))
    
    initial_guess = None
    
    if best_x_so_far is not None and np.random.random() > 0.2:
        # 80% chance to learn from the best (Exploitation)
        try:
            # Add jitter to break out of local minima
            jitter_scale = max(0.1, min(1.0, best_err_so_far / 1000.0))
            initial_guess = np.array(best_x_so_far) + np.random.normal(0, jitter_scale, 26)
        except Exception:
            initial_guess = None
    
    if initial_guess is None:
        # 20% chance (or fallback) to try something completely new
        if bounds[0][0] < 0:
            initial_guess = np.random.uniform(-10, 10, 26)
        else:
            initial_guess = np.random.uniform(0, 20, 26)

    try:
        result = minimize(
            vectorized_objective,
            initial_guess,
            args=task_args,
            method='L-BFGS-B',
            jac=True, # We provide exact gradient
            bounds=bounds,
            options={'maxiter': 200, 'ftol': 1e-9, 'gtol': 1e-9}
        )
        
        # --- HIVE MIND: WRITE ---
        if result.success or result.fun < best_err_so_far:
            if result.fun < best_err_so_far:
                shared_data['best_x'] = result.x
                shared_data['best_err'] = result.fun

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
        
        # --- Compile Math Structures ---
        self._compile_terms()
        
        # --- CPU Control State ---
        self.running = False
        self.current_workers = 0
        # Safety: ensure cpu_count is an int, default to 1 if None
        self.max_allowed_workers = os.cpu_count() or 1
        self.system_cpu = 0.0
        self.app_cpu = 0.0
        self.should_stop = False

    def _compile_terms(self):
        """Pre-compiles string words into numpy math arrays."""
        term_coeffs_list = []
        term_powers_list = []
        term_indices_list = []
        targets_list = []
        
        print(f"Compiling math for {len(self.numbers)} numbers...")
        for i, num in enumerate(self.numbers):
            spelling = number_to_words(num)
            terms = self.parser.compile_to_terms(spelling)
            targets_list.append(num)
            
            for coeff, indices in terms:
                counts = np.zeros(26, dtype=np.float64)
                for idx in indices:
                    counts[idx] += 1
                term_coeffs_list.append(coeff)
                term_powers_list.append(counts)
                term_indices_list.append(i)
                
        self.term_coeffs = np.array(term_coeffs_list, dtype=np.float64)
        self.term_powers = np.array(term_powers_list, dtype=np.int32)
        self.term_indices = np.array(term_indices_list, dtype=np.int32)
        self.targets = np.array(targets_list, dtype=np.float64)
        self.num_numbers = len(self.numbers)

    def _cpu_governor(self):
        """
        Background thread that monitors System vs App CPU.
        Adjusts self.current_workers dynamic limit.
        """
        p = psutil.Process(os.getpid())
        
        while self.running:
            try:
                # Get loads
                sys_load = psutil.cpu_percent(interval=0.5)
                
                # Safety: psutil.cpu_count() can return None
                cpu_count = psutil.cpu_count() or 1
                app_load = p.cpu_percent(interval=None) / cpu_count 
                
                self.system_cpu = sys_load
                self.app_cpu = app_load

                # Safety Thresholds
                TARGET_MAX = 90.0
                LAG_THRESHOLD = 95.0
                
                # Logic: If system is stressed, reduce workers. If room exists, increase.
                logical_cores = psutil.cpu_count(logical=True) or 1
                
                # Ensure self.max_allowed_workers is treated as int
                current_limit = self.max_allowed_workers or 1
                
                if sys_load > LAG_THRESHOLD:
                    # Emergency brake
                    current_limit = max(1, int(current_limit * 0.5))
                elif sys_load > TARGET_MAX:
                    # Gentle throttle
                    current_limit = max(1, current_limit - 1)
                elif sys_load < 70.0 and current_limit < logical_cores:
                    # Ramp up
                    current_limit += 1
                
                self.max_allowed_workers = int(current_limit)
                
                # Send stats to UI if callback exists
                if self.callback:
                    self.callback({
                        'cpu_stats': {
                            'system': sys_load,
                            'app': app_load,
                            'workers': self.current_workers,
                            'limit': self.max_allowed_workers
                        }
                    })
            except Exception:
                pass
            
            time.sleep(0.5)

    def solve(self):
        self.running = True
        self.should_stop = False
        start_time = time.time()
        
        # Start CPU Governor
        gov_thread = threading.Thread(target=self._cpu_governor, daemon=True)
        gov_thread.start()
        
        bounds = [(-100, 100) if self.allow_negative else (0, 100) for _ in range(26)]
        task_args = (self.term_coeffs, self.term_powers, self.term_indices, self.targets, self.num_numbers)
        
        print("Initializing Hive Mind (Multiprocessing Manager)...")
        
        # Use a Manager to share the "Best DNA" across processes
        with multiprocessing.Manager() as manager:
            # Shared memory dict
            shared_data = manager.dict()
            shared_data['best_x'] = None
            shared_data['best_err'] = float('inf')
            
            total_cores = os.cpu_count() or 1
            self.max_allowed_workers = max(1, total_cores - 1)
            
            best_global_result = None
            best_global_error = float('inf')
            attempts = 0

            # Progress history for ETA estimation (list of (time, error))
            best_history = []
            last_print_time = start_time
            last_attempts = 0
            last_attempts_time = start_time
            
            # We manage the executor manually to allow dynamic scaling
            with concurrent.futures.ProcessPoolExecutor(max_workers=total_cores) as executor:
                futures = set()
                
                while not self.should_stop:
                    # 1. Check Results
                    done, _ = concurrent.futures.wait(futures, timeout=0.05, return_when=concurrent.futures.FIRST_COMPLETED)
                    
                    for future in done:
                        futures.remove(future)
                        self.current_workers -= 1
                        attempts += 1
                        
                        try:
                            res = future.result()
                            if res['fun'] < best_global_error:
                                best_global_error = res['fun']
                                best_global_result = res

                                now = time.time()
                                # record history point for ETA fitting
                                best_history.append((now - start_time, float(best_global_error)))

                                # compute percent solved using per-number values
                                try:
                                    calc_vals = compute_per_number_values(res['x'], *task_args)
                                    correct_mask = np.isfinite(calc_vals) & (np.abs(calc_vals - self.targets) < 1e-6)
                                    pct_solved = 100.0 * (np.count_nonzero(correct_mask) / float(self.num_numbers))
                                except Exception:
                                    pct_solved = 0.0

                                # compute simple attempts/sec over short window
                                now_t = now
                                elapsed = max(1e-6, now_t - last_attempts_time)
                                attempts_delta = attempts - last_attempts
                                attempts_per_sec = attempts_delta / elapsed if elapsed > 0 else 0.0
                                last_attempts = attempts
                                last_attempts_time = now_t

                                # ETA estimation: exponential decay fit on error history
                                eta_seconds = None
                                try:
                                    if len(best_history) >= 3:
                                        times = np.array([t for t, e in best_history[-8:]])
                                        errs = np.array([e for t, e in best_history[-8:]])
                                        # avoid zeros
                                        errs = np.clip(errs, 1e-20, None)
                                        logs = np.log(errs)
                                        # fit linear model logs = m * t + b
                                        m, b = np.polyfit(times, logs, 1)
                                        if m < 0:
                                            target_err = 1e-9
                                            curr_log = logs[-1]
                                            eta_seconds = (math.log(target_err) - curr_log) / m
                                            if eta_seconds < 0:
                                                eta_seconds = None
                                except Exception:
                                    eta_seconds = None

                                # UI Update for new best
                                if self.callback:
                                    self.callback({
                                        'x': res['x'],
                                        'error': best_global_error,
                                        'time': now - start_time,
                                        'attempts': attempts,
                                        'attempts_per_sec': attempts_per_sec,
                                        'eta_seconds': eta_seconds,
                                        'percent_solved': pct_solved,
                                        'log': f"New Record! Error: {best_global_error:.6f} ({pct_solved:.1f}% solved)"
                                    })

                                # Check for "Perfect" integer snap solution
                                if best_global_error < 0.1:
                                    # Try rounding
                                    x_rounded = np.round(res['x'])
                                    err_r, _ = vectorized_objective(x_rounded, *task_args)
                                    if err_r < 1e-9:
                                        print("Integer Solution Found!")
                                        self.running = False
                                        return self._pack_result(x_rounded, 0.0, attempts, start_time)
                                        
                        except Exception as e:
                            print(f"Worker died: {e}")

                    # 2. Dynamic Scaling / Submission
                    # Only submit if we are below the dynamic limit set by Governor
                    # Safety check: self.max_allowed_workers could technically be None during init race, defaulting to 1
                    safe_max_workers = self.max_allowed_workers or 1
                    
                    while len(futures) < safe_max_workers:
                        self.current_workers += 1
                        # Use a bounded 32-bit seed to avoid numpy errors
                        seed = (int(time.time() * 1000000) + attempts) & 0xFFFFFFFF
                        # Submit task with access to shared_data
                        futures.add(executor.submit(worker_task, seed, bounds, shared_data, task_args))

                    # 3. Check Stop Condition
                    # Safety: Ensure best_global_result is not None before accessing
                    if best_global_result is not None and best_global_error < 1e-9:
                         self.running = False
                         return self._pack_result(best_global_result['x'], best_global_result['fun'], attempts, start_time)

                    # UI Update Heartbeat
                    # Periodic UI heartbeat and terminal progress (every ~0.5s)
                    now = time.time()
                    if now - last_print_time >= 0.5:
                        last_print_time = now
                        elapsed = now - start_time
                        attempts_per_sec_live = attempts / max(1e-6, elapsed)

                        # percent solved from best result if available
                        pct = 0.0
                        if best_global_result is not None:
                            try:
                                calc_vals = compute_per_number_values(best_global_result['x'], *task_args)
                                correct_mask = np.isfinite(calc_vals) & (np.abs(calc_vals - self.targets) < 1e-6)
                                pct = 100.0 * (np.count_nonzero(correct_mask) / float(self.num_numbers))
                            except Exception:
                                pct = 0.0

                        # ETA estimation from history (reuse last fitted value if present)
                        eta_seconds = None
                        try:
                            if len(best_history) >= 3:
                                times = np.array([t for t, e in best_history[-8:]])
                                errs = np.array([e for t, e in best_history[-8:]])
                                errs = np.clip(errs, 1e-20, None)
                                logs = np.log(errs)
                                m, b = np.polyfit(times, logs, 1)
                                if m < 0:
                                    target_err = 1e-9
                                    curr_log = logs[-1]
                                    eta_seconds = (math.log(target_err) - curr_log) / m
                                    if eta_seconds < 0:
                                        eta_seconds = None
                        except Exception:
                            eta_seconds = None

                        def fmt_seconds(s):
                            if s is None or not (isinstance(s, (int, float)) and math.isfinite(s)):
                                return 'unknown'
                            s = int(max(0, int(s)))
                            h = s // 3600
                            m = (s % 3600) // 60
                            sec = s % 60
                            parts = []
                            if h:
                                parts.append(f"{h}h")
                            if m:
                                parts.append(f"{m}m")
                            parts.append(f"{sec}s")
                            return ' '.join(parts)

                        eta_str = fmt_seconds(eta_seconds)

                        best_err_str = "unknown" if not (isinstance(best_global_error, float) and math.isfinite(best_global_error)) else f"{best_global_error:.6e}"
                        status = (f"Attempts: {attempts} | {attempts_per_sec_live:.1f}/s | "
                                  f"Workers: {self.current_workers}/{safe_max_workers} | "
                                  f"Best Err: {best_err_str} | "
                                  f"Solved: {pct:.1f}% | ETA: {eta_str}")

                        # Print to terminal, trying to overwrite previous line when possible
                        try:
                            sys.stdout.write('\r' + status + ' ' * 10)
                            sys.stdout.flush()
                        except Exception:
                            print(status)

                        # Also send heartbeat to UI
                        if self.callback:
                            self.callback({
                                'attempts': attempts,
                                'workers': self.current_workers,
                                'time': elapsed,
                                'error': None if not (isinstance(best_global_error, float) and math.isfinite(best_global_error)) else best_global_error,
                                'attempts_per_sec': attempts_per_sec_live,
                                'eta': eta_seconds,
                                'percent_solved': pct
                            })

        self.running = False
        
        # Final fallback return
        final_x = best_global_result['x'] if best_global_result is not None else np.zeros(26)
        
        return self._pack_result(final_x, best_global_error, attempts, start_time)

    def _pack_result(self, x, error, attempts, start_time):
        return {
            'success': error < 1e-3,
            'x': x,
            'fun': error,
            'nit': 0,
            'letter_map': {self.letters[i]: float(x[i]) for i in range(26)},
            'attempts': attempts,
            'duration': time.time() - start_time
        }

    def stop(self):
        self.should_stop = True