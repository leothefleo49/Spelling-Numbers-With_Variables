import customtkinter as ctk
import threading
import time
from tkinter import messagebox
import sys
import os
import math
import multiprocessing
import numpy as np

# Add src to path to import core modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.optimizer import Optimizer
from src.core.parser import SpellingParser
from src.core.number_to_words import number_to_words

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Spelling Numbers Solver Pro")
        self.geometry("1200x800")
        # Minimum size to keep layout usable across different UIs
        self.minsize(900, 600)
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=20)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Title
        self.logo = ctk.CTkLabel(self.sidebar, text="Solver Pro", font=ctk.CTkFont(size=28, weight="bold"))
        self.logo.grid(row=0, column=0, padx=20, pady=(30, 20))

        # Inputs
        self.create_input_group("Range Settings", 1)
        self.start_entry = self.create_labeled_entry("Start Number:", "-10", 2)
        self.end_entry = self.create_labeled_entry("End Number:", "10", 3)

        self.create_input_group("Operators", 4)
        self.space_opt = self.create_option("Space Operator:", ["auto", "multiply", "add"], 5)
        self.hyphen_opt = self.create_option("Hyphen Operator:", ["minus", "add", "multiply"], 6)

        self.create_input_group("System", 7)
        self.cpu_opt = self.create_option("CPU Workers:", ["auto", "max", "1", "2", "4", "8", "16"], 8)
        
        self.neg_switch = ctk.CTkSwitch(self.sidebar, text="Allow Negative Variables", font=ctk.CTkFont(size=14))
        self.neg_switch.grid(row=9, column=0, padx=25, pady=(20, 10), sticky="w")
        self.neg_switch.select()

        # Control Buttons
        self.btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.btn_frame.grid(row=11, column=0, padx=20, pady=20, sticky="ew")
        self.btn_frame.grid_columnconfigure((0, 1), weight=1)

        self.start_btn = ctk.CTkButton(self.btn_frame, text="START", font=ctk.CTkFont(weight="bold"), 
                                       height=40, corner_radius=10, fg_color="#2CC985", hover_color="#22A06B",
                                       command=self.start_optimization)
        self.start_btn.grid(row=0, column=0, padx=5, sticky="ew")

        self.stop_btn = ctk.CTkButton(self.btn_frame, text="STOP", font=ctk.CTkFont(weight="bold"),
                                      height=40, corner_radius=10, fg_color="#FF4757", hover_color="#CC3946",
                                      state="disabled", command=self.stop_optimization)
        self.stop_btn.grid(row=0, column=1, padx=5, sticky="ew")

        # Status
        self.status_lbl = ctk.CTkLabel(self.sidebar, text="Ready", text_color="gray70")
        self.status_lbl.grid(row=12, column=0, pady=(0, 20))

        # --- Main Content ---
        self.main_view = ctk.CTkTabview(self, corner_radius=20)
        self.main_view.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        
        self.tab_progress = self.main_view.add("Live Progress")
        self.tab_results = self.main_view.add("Results Analysis")
        self.tab_explorer = self.main_view.add("Number Explorer")

        self.setup_progress_tab()
        self.setup_results_tab()
        self.setup_explorer_tab()

        self.optimizer = None
        self.is_running = False
        self.start_time = 0

    def create_input_group(self, text, row):
        lbl = ctk.CTkLabel(self.sidebar, text=text, font=ctk.CTkFont(size=14, weight="bold"), text_color=("gray50", "gray70"))
        lbl.grid(row=row, column=0, padx=25, pady=(20, 5), sticky="w")

    def create_labeled_entry(self, text, default, row):
        frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frame.grid(row=row, column=0, padx=20, pady=5, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        
        lbl = ctk.CTkLabel(frame, text=text, width=100, anchor="w")
        lbl.grid(row=0, column=0)
        
        entry = ctk.CTkEntry(frame, height=30, corner_radius=8)
        entry.grid(row=0, column=1, sticky="ew")
        entry.insert(0, default)
        return entry

    def create_option(self, text, values, row):
        frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frame.grid(row=row, column=0, padx=20, pady=5, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        
        lbl = ctk.CTkLabel(frame, text=text, width=100, anchor="w")
        lbl.grid(row=0, column=0)
        
        opt = ctk.CTkOptionMenu(frame, values=values, height=30, corner_radius=8)
        opt.grid(row=0, column=1, sticky="ew")
        opt.set(values[0])
        return opt

    def setup_progress_tab(self):
        self.tab_progress.grid_columnconfigure(0, weight=1)
        self.tab_progress.grid_rowconfigure(2, weight=1)

        # Big Error Display
        self.error_frame = ctk.CTkFrame(self.tab_progress, corner_radius=15)
        self.error_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.big_error_lbl = ctk.CTkLabel(self.error_frame, text="0.000000", font=ctk.CTkFont(family="Roboto Mono", size=48, weight="bold"), text_color="#FF4757")
        self.big_error_lbl.pack(pady=20)
        self.error_desc_lbl = ctk.CTkLabel(self.error_frame, text="Current Total Error", font=ctk.CTkFont(size=14))
        self.error_desc_lbl.pack(pady=(0, 20))

        # Stats Grid
        self.stats_frame = ctk.CTkFrame(self.tab_progress, fg_color="transparent")
        self.stats_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.stat_attempts = self.create_stat_box(self.stats_frame, "Attempts", "0", 0)
        self.stat_speed = self.create_stat_box(self.stats_frame, "Speed", "0 it/s", 1)
        self.stat_time = self.create_stat_box(self.stats_frame, "Time Elapsed", "00:00", 2)
        self.stat_workers = self.create_stat_box(self.stats_frame, "Active Workers", "0", 3)
        self.stat_eta = self.create_stat_box(self.stats_frame, "ETA", "—", 4)

        # Log
        self.log_box = ctk.CTkTextbox(self.tab_progress, font=ctk.CTkFont(family="Consolas", size=12), corner_radius=10)
        self.log_box.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")

    def create_stat_box(self, parent, title, value, col):
        frame = ctk.CTkFrame(parent, corner_radius=10)
        frame.grid(row=0, column=col, padx=5, sticky="ew")
        
        lbl_title = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color="gray70")
        lbl_title.pack(pady=(10, 0))
        
        lbl_val = ctk.CTkLabel(frame, text=value, font=ctk.CTkFont(size=16, weight="bold"))
        lbl_val.pack(pady=(0, 10))
        return lbl_val

    def setup_results_tab(self):
        self.tab_results.grid_columnconfigure(0, weight=1)
        self.tab_results.grid_rowconfigure(1, weight=1)

        # Letters Grid inside a scrollable frame so UI doesn't cut off on smaller windows
        self.letters_frame = ctk.CTkScrollableFrame(self.tab_results, corner_radius=10, height=180)
        self.letters_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.letter_widgets = {}
        for i in range(26):
            l = chr(65+i)
            f = ctk.CTkFrame(self.letters_frame, fg_color="transparent")
            f.grid(row=i//9, column=i%9, padx=5, pady=5, sticky="ew")
            
            ctk.CTkLabel(f, text=l, font=ctk.CTkFont(weight="bold")).pack(side="left")
            val = ctk.CTkLabel(f, text="0.00", font=ctk.CTkFont(family="Consolas"), text_color="#2CC985")
            val.pack(side="right", padx=5)
            self.letter_widgets[l] = val
            
        self.letters_frame.grid_columnconfigure(tuple(range(9)), weight=1)

        # Detailed List
        self.results_box = ctk.CTkTextbox(self.tab_results, font=ctk.CTkFont(family="Consolas", size=14), corner_radius=10)
        self.results_box.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

    def setup_explorer_tab(self):
        self.tab_explorer.grid_columnconfigure(0, weight=1)
        
        self.exp_entry = ctk.CTkEntry(self.tab_explorer, placeholder_text="Type a number (e.g. 123) or words (ONE HUNDRED)", height=40, font=ctk.CTkFont(size=16))
        self.exp_entry.grid(row=0, column=0, padx=40, pady=40, sticky="ew")
        self.exp_entry.bind("<Return>", lambda e: self.run_explorer())
        
        self.exp_btn = ctk.CTkButton(self.tab_explorer, text="Calculate Value", height=40, command=self.run_explorer)
        self.exp_btn.grid(row=1, column=0, padx=40, pady=(0, 20))
        
        self.exp_out = ctk.CTkTextbox(self.tab_explorer, font=ctk.CTkFont(family="Consolas", size=16), corner_radius=15)
        self.exp_out.grid(row=2, column=0, padx=40, pady=20, sticky="nsew")
        self.tab_explorer.grid_rowconfigure(2, weight=1)

    def log(self, msg):
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_box.see("end")

    def start_optimization(self):
        try:
            start = int(self.start_entry.get())
            end = int(self.end_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid range inputs")
            return

        allow_neg = bool(self.neg_switch.get())

        if not allow_neg:
            if end < 0:
                messagebox.showerror("Error", "Negatives disabled. Please enable to run this calculation.")
                return
            if start < 0:
                should_continue = messagebox.askokcancel(
                    "Warning", 
                    "Negatives are disabled.\n\nThis calculation will run without the negative portions (0 and above).\n\nDo you want to continue?"
                )
                if not should_continue:
                    self.reset_ui()
                    return
                start = 0

        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_lbl.configure(text="Optimizing... (Continuous Mode)", text_color="#2CC985")
        self.log_box.delete("1.0", "end")
        self.log(f"Starting optimization ({start} to {end})...")
        
        self.start_time = time.time()
        self.update_timer()  # Start the smooth timer
        
        threading.Thread(target=self.run_optimizer_thread, args=(start, end), daemon=True).start()

    def update_timer(self):
        if self.is_running:
            elapsed = int(time.time() - self.start_time)
            mins, secs = divmod(elapsed, 60)
            hrs, mins = divmod(mins, 60)
            
            if hrs > 0:
                time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            else:
                time_str = f"{mins:02d}:{secs:02d}"
                
            self.stat_time.configure(text=time_str)
            self.after(100, self.update_timer)

    def stop_optimization(self):
        self.is_running = False
        self.log("Stopping requested...")
        self.status_lbl.configure(text="Stopping...", text_color="orange")

    def run_optimizer_thread(self, start, end):
        try:
            def callback(data):
                if not self.is_running:
                    raise StopIteration
                
                # Update UI immediately (or let Tkinter handle the queue)
                self.after(0, lambda: self.update_progress(data))

            self.optimizer = Optimizer(
                start, end,
                space_operator=self.space_opt.get(),
                hyphen_operator=self.hyphen_opt.get(),
                cpu_usage=self.cpu_opt.get(),
                allow_negative=bool(self.neg_switch.get()),
                callback=callback
            )
            
            result = self.optimizer.solve()
            
            self.after(0, lambda: self.finish_optimization(result))
            
        except Exception as e:
            self.after(0, lambda: self.log(f"Error: {e}"))
            self.after(0, self.reset_ui)

    def update_progress(self, data):
        if 'check_stop' in data:
            return

        err = data.get('error')
        if err is not None and isinstance(err, (int, float)):
            self.big_error_lbl.configure(text=f"{err:.6f}")
            
            # Color code error
            if err < 1e-9: color = "#2CC985" # Green
            elif err < 1: color = "#F1C40F" # Yellow
            else: color = "#FF4757" # Red
            self.big_error_lbl.configure(text_color=color)
        
        # Update stats (all fields optional)
        if 'attempts' in data:
            self.stat_attempts.configure(text=f"{data['attempts']}")
        
        if 'attempts_per_sec' in data or 'speed' in data:
            aps = data.get('attempts_per_sec', data.get('speed', 0.0))
            self.stat_speed.configure(text=f"{aps:.1f} it/s")
        
        # Time is handled by update_timer now, but we can respect override if needed
        # if 'time' in data: ...
        
        if 'workers' in data:
            self.stat_workers.configure(text=f"{data['workers']}")
        
        # ETA (seconds -> mm:ss or h:mm:ss) - may be None
        if 'eta' in data or 'eta_seconds' in data:
            eta = data.get('eta') or data.get('eta_seconds')
            if eta is None:
                eta_text = '—'
            else:
                try:
                    eta_s = int(max(0, float(eta)))
                    if eta_s >= 3600:
                        h = eta_s // 3600
                        m = (eta_s % 3600) // 60
                        s = eta_s % 60
                        eta_text = f"{h}h {m:02d}m {s:02d}s"
                    else:
                        em, es = divmod(eta_s, 60)
                        eta_text = f"{em:02d}:{es:02d}"
                except Exception:
                    eta_text = '—'
            self.stat_eta.configure(text=eta_text)

        # Auto worker info (separate small update)
        if 'auto_worker_info' in data:
            info = data['auto_worker_info']
            try:
                w = info.get('workers')
                cpu = info.get('cpu_percent')
                reason = info.get('reason')
                self.status_lbl.configure(text=f"Auto workers: {w} (CPU {cpu:.0f}%)", text_color="gray70")
                # self.log(f"Auto worker decision: workers={w}, cpu={cpu:.1f}%, reason={reason}") # Too spammy
            except Exception:
                pass
        # Any general log messages
        if 'log' in data:
            try:
                self.log(data['log'])
            except Exception:
                pass
        
        # Update letters live (only when 'x' is present)
        if 'x' in data:
            letters_used = data.get('letters_used', getattr(self.optimizer, 'letters_used', [True]*26))
            for i, x in enumerate(data['x']):
                l = chr(65+i)
                try:
                    used = bool(letters_used[i])
                except Exception:
                    used = True

                if not used:
                    # Show explicit N/A for letters that never appear
                    self.letter_widgets[l].configure(text="N/A", text_color="gray60")
                else:
                    try:
                        if x is None or (isinstance(x, float) and (math.isinf(x) or math.isnan(x))):
                            self.letter_widgets[l].configure(text="unknown")
                        else:
                            self.letter_widgets[l].configure(text=f"{x:.2f}", text_color="#2CC985")
                    except Exception:
                        self.letter_widgets[l].configure(text=str(x))

    def finish_optimization(self, result):
        # Detailed finish summary
        success = result.get('success', False)
        message = result.get('message', '')
        attempts = result.get('attempts', None)
        duration = result.get('duration', None)

        self.log(f"Optimization Finished — Success: {success} — {message}")
        if attempts is not None and duration is not None and duration > 0:
            self.log(f"Attempts: {attempts} — Duration: {duration:.2f}s — Avg: {attempts/duration:.2f} it/s")

        # Update final progress and show result (include letters_used)
        self.update_progress({
            'error': result.get('fun', 0.0),
            'x': result.get('x', np.zeros(26)),
            'letters_used': result.get('letters_used', getattr(self.optimizer, 'letters_used', [True]*26))
        })
        self.reset_ui()

        # Populate results area with detailed validation
        self.results_box.delete("1.0", "end")
        parser = SpellingParser(letter_values=result.get('letter_map', {}))

        # If optimizer adjusted start/end due to negatives, use the optimizer if available
        start = getattr(self.optimizer, 'start', int(self.start_entry.get()))
        end = getattr(self.optimizer, 'end', int(self.end_entry.get()))

        correct_count = 0
        total = 0

        for num in range(start, end + 1):
            spelling = number_to_words(num)
            val, expl = parser.calculate_spelled_value(spelling)
            err = (val - num) ** 2

            icon = "✅" if err < 0.001 else "❌"
            if err < 0.001:
                correct_count += 1
            total += 1

            self.results_box.insert("end", f"{icon} {num}: {spelling}\n")
            self.results_box.insert("end", f"   {expl}\n")
            self.results_box.insert("end", f"   Error: {err:.8f}\n\n")

        if total > 0:
            self.log(f"Accuracy: {correct_count}/{total} ({correct_count/total*100:.1f}%)")
        self.main_view.set("Results Analysis")

    def reset_ui(self):
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_lbl.configure(text="Idle", text_color="gray70")

    def run_explorer(self):
        txt = self.exp_entry.get()
        if not txt: return
        
        # Get current letters
        letters = {}
        for l, w in self.letter_widgets.items():
            try:
                letters[l] = float(w.cget("text"))
            except:
                letters[l] = 1.0
                
        parser = SpellingParser(letter_values=letters)
        
        try:
            # Try as number first
            num = int(txt)
            spelling = number_to_words(num)
            val, expl = parser.calculate_spelled_value(spelling)
            target = num
        except ValueError:
            # Try as words
            spelling = txt.upper()
            val, expl = parser.calculate_spelled_value(spelling)
            target = None
            
        self.exp_out.delete("1.0", "end")
        self.exp_out.insert("end", f"Input: {txt}\n")
        self.exp_out.insert("end", f"Spelling: {spelling}\n")
        self.exp_out.insert("end", f"Calculated: {val:.6f}\n")
        
        if target is not None:
            err = (val - target) ** 2
            self.exp_out.insert("end", f"Target: {target}\n")
            self.exp_out.insert("end", f"Error: {err:.8f}\n")
            
        self.exp_out.insert("end", f"\nBreakdown:\n{expl}")

if __name__ == "__main__":
    # Fix for multiprocessing on Windows
    multiprocessing.freeze_support()
    app = App()
    app.mainloop()
