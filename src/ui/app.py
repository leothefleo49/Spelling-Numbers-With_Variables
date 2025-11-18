import customtkinter as ctk
import threading
import time
from tkinter import messagebox
import sys
import os

# Add src to path to import core modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.optimizer import Optimizer
from src.core.parser import SpellingParser
from src.core.number_to_words import number_to_words

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Spelling Numbers Solver")
        self.geometry("1100x700")

        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Solver Settings", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Range Inputs
        self.start_label = ctk.CTkLabel(self.sidebar_frame, text="Start Range:", anchor="w")
        self.start_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        self.start_entry = ctk.CTkEntry(self.sidebar_frame)
        self.start_entry.grid(row=2, column=0, padx=20, pady=(0, 10))
        self.start_entry.insert(0, "-10")

        self.end_label = ctk.CTkLabel(self.sidebar_frame, text="End Range:", anchor="w")
        self.end_label.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        self.end_entry = ctk.CTkEntry(self.sidebar_frame)
        self.end_entry.grid(row=4, column=0, padx=20, pady=(0, 10))
        self.end_entry.insert(0, "10")

        # Advanced Settings
        self.adv_label = ctk.CTkLabel(self.sidebar_frame, text="Advanced Settings", font=ctk.CTkFont(size=16, weight="bold"))
        self.adv_label.grid(row=5, column=0, padx=20, pady=(20, 10))

        # Space Operator
        self.space_label = ctk.CTkLabel(self.sidebar_frame, text="Space Operator:", anchor="w")
        self.space_label.grid(row=6, column=0, padx=20, pady=(5, 0), sticky="w")
        self.space_opt = ctk.CTkOptionMenu(self.sidebar_frame, values=["auto", "multiply", "add"])
        self.space_opt.grid(row=7, column=0, padx=20, pady=(0, 10))
        self.space_opt.set("auto")

        # Hyphen Operator
        self.hyphen_label = ctk.CTkLabel(self.sidebar_frame, text="Hyphen Operator:", anchor="w")
        self.hyphen_label.grid(row=8, column=0, padx=20, pady=(5, 0), sticky="w")
        self.hyphen_opt = ctk.CTkOptionMenu(self.sidebar_frame, values=["minus", "add", "multiply"])
        self.hyphen_opt.grid(row=9, column=0, padx=20, pady=(0, 10))
        self.hyphen_opt.set("minus")

        # CPU Usage
        self.cpu_label = ctk.CTkLabel(self.sidebar_frame, text="CPU Usage (Workers):", anchor="w")
        self.cpu_label.grid(row=10, column=0, padx=20, pady=(5, 0), sticky="w")
        self.cpu_opt = ctk.CTkOptionMenu(self.sidebar_frame, values=["auto", "max", "1", "2", "4", "8", "16"])
        self.cpu_opt.grid(row=11, column=0, padx=20, pady=(0, 10))
        self.cpu_opt.set("auto")

        # Allow Negative
        self.neg_switch = ctk.CTkSwitch(self.sidebar_frame, text="Allow Negative Letters")
        self.neg_switch.grid(row=12, column=0, padx=20, pady=(10, 20))
        self.neg_switch.select()

        # Buttons
        self.start_button = ctk.CTkButton(self.sidebar_frame, text="Start Optimization", command=self.start_optimization)
        self.start_button.grid(row=13, column=0, padx=20, pady=20)

        self.stop_button = ctk.CTkButton(self.sidebar_frame, text="Stop", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.stop_optimization, state="disabled")
        self.stop_button.grid(row=14, column=0, padx=20, pady=(0, 20))

        # Status
        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Status: Idle", text_color="gray")
        self.status_label.grid(row=15, column=0, padx=20, pady=10)

        # Main Content
        self.tabview = ctk.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        self.tabview.add("Progress")
        self.tabview.add("Results")
        self.tabview.add("Explorer")

        # Progress Tab
        self.setup_progress_tab()
        
        # Results Tab
        self.setup_results_tab()

        # Explorer Tab
        self.setup_explorer_tab()

        self.optimizer = None
        self.is_running = False

    def setup_progress_tab(self):
        self.tabview.tab("Progress").grid_columnconfigure(0, weight=1)
        
        self.progress_frame = ctk.CTkFrame(self.tabview.tab("Progress"))
        self.progress_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.progress_frame.grid_columnconfigure(0, weight=1)

        self.error_label = ctk.CTkLabel(self.progress_frame, text="Current Error: --", font=ctk.CTkFont(size=24))
        self.error_label.grid(row=0, column=0, pady=20)

        self.log_textbox = ctk.CTkTextbox(self.tabview.tab("Progress"), width=400)
        self.log_textbox.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        self.tabview.tab("Progress").grid_rowconfigure(1, weight=1)

    def setup_results_tab(self):
        self.tabview.tab("Results").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Results").grid_rowconfigure(1, weight=1)

        self.letters_frame = ctk.CTkScrollableFrame(self.tabview.tab("Results"), height=200, orientation="horizontal")
        self.letters_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        self.letter_labels = {}
        for i in range(26):
            l = chr(65+i)
            lbl = ctk.CTkLabel(self.letters_frame, text=f"{l}: --", font=ctk.CTkFont(family="Consolas", size=14))
            lbl.pack(side="left", padx=10)
            self.letter_labels[l] = lbl

        self.results_textbox = ctk.CTkTextbox(self.tabview.tab("Results"), font=ctk.CTkFont(family="Consolas", size=12))
        self.results_textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

    def setup_explorer_tab(self):
        self.tabview.tab("Explorer").grid_columnconfigure(0, weight=1)
        
        self.exp_entry = ctk.CTkEntry(self.tabview.tab("Explorer"), placeholder_text="Enter a number (e.g. 123)")
        self.exp_entry.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.exp_btn = ctk.CTkButton(self.tabview.tab("Explorer"), text="Calculate", command=self.run_explorer)
        self.exp_btn.grid(row=1, column=0, padx=20, pady=10)
        
        self.exp_result = ctk.CTkTextbox(self.tabview.tab("Explorer"), font=ctk.CTkFont(family="Consolas", size=14))
        self.exp_result.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        self.tabview.tab("Explorer").grid_rowconfigure(2, weight=1)

    def log(self, message):
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")

    def start_optimization(self):
        try:
            start = int(self.start_entry.get())
            end = int(self.end_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid range")
            return

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text="Status: Optimizing...", text_color="orange")
        self.log_textbox.delete("1.0", "end")
        self.log(f"Starting optimization for range {start} to {end}...")

        self.is_running = True
        threading.Thread(target=self.run_optimizer, args=(start, end), daemon=True).start()

    def stop_optimization(self):
        self.is_running = False
        self.log("Stopping...")

    def run_optimizer(self, start, end):
        try:
            def callback(data):
                if not self.is_running:
                    raise StopIteration
                
                # Update UI periodically
                # Use after() to schedule UI updates on the main thread to avoid freezing
                if int(data['time'] * 10) % 5 == 0: # throttle updates
                    self.after(0, lambda: self.error_label.configure(text=f"Error: {data['error']:.4f}"))
                    self.after(0, lambda: self.log(f"Time: {data['time']:.1f}s | Error: {data['error']:.6f}"))
            
            space_op = self.space_opt.get()
            hyphen_op = self.hyphen_opt.get()
            cpu_usage = self.cpu_opt.get()
            allow_neg = bool(self.neg_switch.get())

            self.optimizer = Optimizer(start, end, 
                                       space_operator=space_op, 
                                       hyphen_operator=hyphen_op,
                                       cpu_usage=cpu_usage,
                                       allow_negative=allow_neg,
                                       callback=callback)
            result = self.optimizer.solve()
            
            if self.is_running:
                self.after(0, lambda: self.on_optimization_complete(result))
            
        except StopIteration:
            self.after(0, lambda: self.log("Optimization stopped by user."))
        except Exception as e:
            self.after(0, lambda: self.log(f"Error: {str(e)}"))
        finally:
            self.after(0, self.reset_ui_state)

    def reset_ui_state(self):
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_label.configure(text="Status: Idle", text_color="gray")

    def on_optimization_complete(self, result):
        self.log(f"Optimization Complete! Success: {result['success']}")
        self.log(f"Final Error: {result['fun']:.6f}")
        self.log(f"Iterations: {result['nit']}")
        
        # Update letters
        letter_map = result['letter_map']
        for l, val in letter_map.items():
            self.letter_labels[l].configure(text=f"{l}: {val:.4f}")
        
        # Update results text
        self.results_textbox.delete("1.0", "end")
        parser = SpellingParser(letter_values=letter_map)
        
        solved_count = 0
        total_count = 0
        
        start_range = self.optimizer.start if self.optimizer else int(self.start_entry.get())
        end_range = self.optimizer.end if self.optimizer else int(self.end_entry.get())

        for num in range(start_range, end_range + 1):
            spelling = number_to_words(num)
            val, expl = parser.calculate_spelled_value(spelling)
            err = (val - num) ** 2
            status = "✅" if err < 0.01 else "❌"
            if err < 0.01: solved_count += 1
            total_count += 1
            
            self.results_textbox.insert("end", f"{status} {num}: {spelling}\n")
            self.results_textbox.insert("end", f"   Calc: {val:.4f} (Err: {err:.6f})\n")
            self.results_textbox.insert("end", f"   {expl}\n\n")
            
        self.log(f"Solved: {solved_count}/{total_count}")
        self.tabview.set("Results")

    def run_explorer(self):
        try:
            num = int(self.exp_entry.get())
            spelling = number_to_words(num)
            
            # Get current letters
            letters = {}
            for l, lbl in self.letter_labels.items():
                txt = lbl.cget("text")
                val = float(txt.split(": ")[1]) if ": " in txt and "--" not in txt else 1.0
                letters[l] = val
            
            parser = SpellingParser(letter_values=letters)
            val, expl = parser.calculate_spelled_value(spelling)
            
            self.exp_result.delete("1.0", "end")
            self.exp_result.insert("end", f"Number: {num}\n")
            self.exp_result.insert("end", f"Spelling: {spelling}\n")
            self.exp_result.insert("end", f"Value: {val:.6f}\n")
            self.exp_result.insert("end", f"Error: {(val-num)**2:.6f}\n\n")
            self.exp_result.insert("end", f"Explanation:\n{expl}")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid number")

if __name__ == "__main__":
    app = App()
    app.mainloop()
