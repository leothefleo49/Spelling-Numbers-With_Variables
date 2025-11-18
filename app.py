"""
Spelling Numbers Application - Main GUI
Interactive application to find optimal letter values for number spellings.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from optimizer import LetterValueOptimizer
from spelling_parser import SpellingParser
from number_to_words import number_to_words


class SpellingNumbersApp:
    """Main application window"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Spelling Numbers with Variables Calculator")
        self.root.geometry("900x700")
        
        # State
        self.optimizer = None
        self.is_solving = False
        self.solution = None
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.setup_tab = ttk.Frame(self.notebook)
        self.solving_tab = ttk.Frame(self.notebook)
        self.results_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.setup_tab, text="Setup")
        self.notebook.add(self.solving_tab, text="Solving")
        self.notebook.add(self.results_tab, text="Results")
        
        # Build each tab
        self.build_setup_tab()
        self.build_solving_tab()
        self.build_results_tab()
        
        # Disable tabs initially
        self.notebook.tab(1, state='disabled')
        self.notebook.tab(2, state='disabled')
    
    def build_setup_tab(self):
        """Build the setup/input tab"""
        # Title
        title = tk.Label(self.setup_tab, 
                        text="Spelling Numbers with Variables",
                        font=('Arial', 18, 'bold'))
        title.pack(pady=20)
        
        # Description
        desc_frame = tk.Frame(self.setup_tab)
        desc_frame.pack(pady=10, padx=20, fill='x')
        
        desc_text = """
This application finds optimal values for each letter (A-Z) that "solve" 
number spellings within a range. A number is "solved" when the product 
of its letters' values equals the number itself.

Example: If O*N*E = 1, then "ONE" is solved.

The AI will find letter values that maximize solved numbers in your range.
        """
        
        desc_label = tk.Label(desc_frame, text=desc_text, 
                             justify='left', wraplength=800)
        desc_label.pack()
        
        # Input frame
        input_frame = tk.LabelFrame(self.setup_tab, text="Configuration", 
                                    font=('Arial', 12, 'bold'))
        input_frame.pack(pady=20, padx=40, fill='x')
        
        # Start range
        start_frame = tk.Frame(input_frame)
        start_frame.pack(pady=10, padx=20, fill='x')
        
        tk.Label(start_frame, text="Start Range:", 
                font=('Arial', 11)).pack(side='left', padx=5)
        self.start_entry = tk.Entry(start_frame, font=('Arial', 11), width=15)
        self.start_entry.pack(side='left', padx=5)
        self.start_entry.insert(0, "-100")
        
        # End range
        end_frame = tk.Frame(input_frame)
        end_frame.pack(pady=10, padx=20, fill='x')
        
        tk.Label(end_frame, text="End Range:", 
                font=('Arial', 11)).pack(side='left', padx=5)
        self.end_entry = tk.Entry(end_frame, font=('Arial', 11), width=15)
        self.end_entry.pack(side='left', padx=5)
        self.end_entry.insert(0, "100")
        
        # Population size
        pop_frame = tk.Frame(input_frame)
        pop_frame.pack(pady=10, padx=20, fill='x')
        
        tk.Label(pop_frame, text="Population Size:", 
                font=('Arial', 11)).pack(side='left', padx=5)
        self.pop_entry = tk.Entry(pop_frame, font=('Arial', 11), width=15)
        self.pop_entry.pack(side='left', padx=5)
        self.pop_entry.insert(0, "100")
        
        tk.Label(pop_frame, text="(Higher = better results, slower)", 
                font=('Arial', 9), fg='gray').pack(side='left', padx=5)
        
        # Generations
        gen_frame = tk.Frame(input_frame)
        gen_frame.pack(pady=10, padx=20, fill='x')
        
        tk.Label(gen_frame, text="Generations:", 
                font=('Arial', 11)).pack(side='left', padx=5)
        self.gen_entry = tk.Entry(gen_frame, font=('Arial', 11), width=15)
        self.gen_entry.pack(side='left', padx=5)
        self.gen_entry.insert(0, "100")
        
        tk.Label(gen_frame, text="(Higher = better results, slower)", 
                font=('Arial', 9), fg='gray').pack(side='left', padx=5)
        
        # Calculate button
        button_frame = tk.Frame(self.setup_tab)
        button_frame.pack(pady=30)
        
        self.calc_button = tk.Button(button_frame, text="Start Calculation", 
                                     font=('Arial', 14, 'bold'),
                                     bg='#4CAF50', fg='white',
                                     padx=30, pady=10,
                                     command=self.start_optimization)
        self.calc_button.pack()
    
    def build_solving_tab(self):
        """Build the solving/progress tab"""
        # Title
        title = tk.Label(self.solving_tab, 
                        text="Optimization in Progress...",
                        font=('Arial', 16, 'bold'))
        title.pack(pady=20)
        
        # Status frame
        status_frame = tk.LabelFrame(self.solving_tab, text="Current Status",
                                     font=('Arial', 12, 'bold'))
        status_frame.pack(pady=20, padx=40, fill='both', expand=True)
        
        # Progress info
        self.progress_frame = tk.Frame(status_frame)
        self.progress_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Generation counter
        gen_frame = tk.Frame(self.progress_frame)
        gen_frame.pack(pady=5, fill='x')
        tk.Label(gen_frame, text="Generation:", 
                font=('Arial', 11)).pack(side='left', padx=5)
        self.gen_label = tk.Label(gen_frame, text="0", 
                                  font=('Arial', 11, 'bold'))
        self.gen_label.pack(side='left')
        
        # Solved counter
        solved_frame = tk.Frame(self.progress_frame)
        solved_frame.pack(pady=5, fill='x')
        tk.Label(solved_frame, text="Numbers Solved:", 
                font=('Arial', 11)).pack(side='left', padx=5)
        self.solved_label = tk.Label(solved_frame, text="0 / 0", 
                                     font=('Arial', 11, 'bold'),
                                     fg='green')
        self.solved_label.pack(side='left')
        
        # Fitness
        fitness_frame = tk.Frame(self.progress_frame)
        fitness_frame.pack(pady=5, fill='x')
        tk.Label(fitness_frame, text="Total Fitness (Error):", 
                font=('Arial', 11)).pack(side='left', padx=5)
        self.fitness_label = tk.Label(fitness_frame, text="N/A", 
                                      font=('Arial', 11, 'bold'))
        self.fitness_label.pack(side='left')
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(self.progress_frame, 
                                           mode='determinate',
                                           length=400)
        self.progress_bar.pack(pady=20)
        
        # Log
        log_label = tk.Label(self.progress_frame, text="Progress Log:",
                           font=('Arial', 11, 'bold'))
        log_label.pack(pady=(20, 5))
        
        self.log_text = scrolledtext.ScrolledText(self.progress_frame,
                                                  height=15,
                                                  font=('Courier', 9))
        self.log_text.pack(fill='both', expand=True, pady=5)
        
        # Stop button
        self.stop_button = tk.Button(self.solving_tab, text="Stop Optimization",
                                     font=('Arial', 12),
                                     bg='#f44336', fg='white',
                                     command=self.stop_optimization)
        self.stop_button.pack(pady=10)
    
    def build_results_tab(self):
        """Build the results tab"""
        # Title
        title_frame = tk.Frame(self.results_tab)
        title_frame.pack(pady=10, fill='x')
        
        title = tk.Label(title_frame, 
                        text="Optimization Results",
                        font=('Arial', 16, 'bold'))
        title.pack()
        
        self.results_summary = tk.Label(title_frame, text="",
                                        font=('Arial', 11))
        self.results_summary.pack()
        
        # Create paned window for split view
        paned = tk.PanedWindow(self.results_tab, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel: Letter values
        left_frame = tk.LabelFrame(paned, text="Letter Values (A-Z)",
                                  font=('Arial', 11, 'bold'))
        paned.add(left_frame, width=300)
        
        self.letter_values_text = scrolledtext.ScrolledText(left_frame,
                                                           height=25,
                                                           font=('Courier', 10))
        self.letter_values_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Right panel: Explorer
        right_frame = tk.LabelFrame(paned, text="Number Explorer",
                                   font=('Arial', 11, 'bold'))
        paned.add(right_frame, width=550)
        
        # Explorer input
        explorer_input_frame = tk.Frame(right_frame)
        explorer_input_frame.pack(pady=10, padx=10, fill='x')
        
        tk.Label(explorer_input_frame, text="Enter a number:",
                font=('Arial', 10)).pack(side='left', padx=5)
        
        self.explorer_entry = tk.Entry(explorer_input_frame, 
                                      font=('Arial', 11), width=15)
        self.explorer_entry.pack(side='left', padx=5)
        self.explorer_entry.bind('<Return>', lambda e: self.explore_number())
        
        explore_btn = tk.Button(explorer_input_frame, text="Explore",
                               command=self.explore_number)
        explore_btn.pack(side='left', padx=5)
        
        # Explorer output
        self.explorer_text = scrolledtext.ScrolledText(right_frame,
                                                      height=25,
                                                      font=('Courier', 10),
                                                      wrap='word')
        self.explorer_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Bottom buttons
        button_frame = tk.Frame(self.results_tab)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="New Calculation",
                 font=('Arial', 11),
                 command=self.reset_app).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="Export Results",
                 font=('Arial', 11),
                 command=self.export_results).pack(side='left', padx=5)
    
    def start_optimization(self):
        """Start the optimization process"""
        try:
            # Get parameters
            start = int(self.start_entry.get())
            end = int(self.end_entry.get())
            pop_size = int(self.pop_entry.get())
            generations = int(self.gen_entry.get())
            
            if start >= end:
                messagebox.showerror("Error", "Start range must be less than end range")
                return
            
            if pop_size < 10:
                messagebox.showerror("Error", "Population size must be at least 10")
                return
            
            if generations < 1:
                messagebox.showerror("Error", "Generations must be at least 1")
                return
            
            # Create optimizer
            self.optimizer = LetterValueOptimizer(start, end, pop_size)
            self.is_solving = True
            self.max_generations = generations
            
            # Switch to solving tab
            self.notebook.tab(1, state='normal')
            self.notebook.select(1)
            self.notebook.tab(0, state='disabled')
            
            # Clear log
            self.log_text.delete(1.0, tk.END)
            self.progress_bar['value'] = 0
            self.progress_bar['maximum'] = generations
            
            # Start optimization in background thread
            thread = threading.Thread(target=self.run_optimization)
            thread.daemon = True
            thread.start()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
    
    def run_optimization(self):
        """Run optimization in background thread"""
        def callback(stats):
            if not self.is_solving:
                return False  # Stop signal
            
            # Update UI
            self.root.after(0, self.update_progress, stats)
            return True
        
        try:
            # Run optimization
            if self.optimizer is None:
                raise RuntimeError("Optimizer not initialized")
            for gen in range(self.max_generations):
                if not self.is_solving:
                    break
                
                stats = self.optimizer.evolve_generation() if self.optimizer else None
                if stats is None:
                    raise RuntimeError("Failed to generate stats - optimizer missing")
                callback(stats)
            
            # Optimization complete
            if self.is_solving:
                self.root.after(0, self.optimization_complete)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, self.reset_app)
    
    def update_progress(self, stats):
        """Update progress UI"""
        self.gen_label.config(text=f"{stats['generation']} / {self.max_generations}")
        self.solved_label.config(text=f"{stats['solved_count']} / {stats['total_numbers']}")
        self.fitness_label.config(text=f"{stats['best_fitness']:.2f}")
        
        self.progress_bar['value'] = stats['generation']
        
        # Add to log
        log_msg = (f"Gen {stats['generation']:3d}: "
                  f"Solved {stats['solved_count']:3d}/{stats['total_numbers']:3d}, "
                  f"Fitness: {stats['best_fitness']:8.2f}, "
                  f"Max Error: {stats['max_error']:8.2f}\n")
        
        self.log_text.insert(tk.END, log_msg)
        self.log_text.see(tk.END)
    
    def stop_optimization(self):
        """Stop the optimization"""
        self.is_solving = False
        self.log_text.insert(tk.END, "\n--- Optimization stopped by user ---\n")
        
        if self.optimizer and self.optimizer.best_solution:
            self.optimization_complete()
        else:
            self.reset_app()
    
    def optimization_complete(self):
        """Handle optimization completion"""
        self.is_solving = False
        
        # Get solution details
        if self.optimizer:
            self.solution = self.optimizer.get_solution_details()
        else:
            self.solution = None
        
        # Switch to results tab
        self.notebook.tab(2, state='normal')
        self.notebook.select(2)
        
        # Update results
        self.display_results()
    
    def display_results(self):
        """Display optimization results"""
        if not self.solution:
            return
        
        # Summary
        solved = self.solution['solved_count']
        total = self.solution['total_count']
        percentage = (solved / total * 100) if total > 0 else 0
        
        summary = f"Solved {solved} out of {total} numbers ({percentage:.1f}%)"
        self.results_summary.config(text=summary, fg='green' if percentage > 50 else 'orange')
        
        # Letter values
        self.letter_values_text.delete(1.0, tk.END)
        self.letter_values_text.insert(tk.END, "Letter Values:\n")
        self.letter_values_text.insert(tk.END, "=" * 25 + "\n")
        
        for letter in sorted(self.solution['letter_values'].keys()):
            value = self.solution['letter_values'][letter]
            self.letter_values_text.insert(tk.END, f"{letter}: {value:9.4f}\n")
        
        self.letter_values_text.insert(tk.END, "\n" + "=" * 25 + "\n")
        self.letter_values_text.insert(tk.END, f"Total Error: {self.solution['total_error']:.2f}\n")
        
        # Set explorer default
        if self.solution['results']:
            # Find first solved number
            for result in self.solution['results']:
                if result['is_solved']:
                    self.explorer_entry.delete(0, tk.END)
                    self.explorer_entry.insert(0, str(result['number']))
                    self.explore_number()
                    break
    
    def explore_number(self):
        """Explore a specific number"""
        if not self.solution:
            return
        
        try:
            number = int(self.explorer_entry.get())
            
            # Find result
            result = None
            for r in self.solution['results']:
                if r['number'] == number:
                    result = r
                    break
            
            if not result:
                self.explorer_text.delete(1.0, tk.END)
                self.explorer_text.insert(tk.END, 
                    f"Number {number} is not in the calculated range.")
                return
            
            # Display detailed breakdown
            self.explorer_text.delete(1.0, tk.END)
            
            self.explorer_text.insert(tk.END, "=" * 60 + "\n")
            self.explorer_text.insert(tk.END, f"TARGET NUMBER: {result['number']}\n")
            self.explorer_text.insert(tk.END, "=" * 60 + "\n\n")
            
            self.explorer_text.insert(tk.END, f"Spelling: {result['spelling']}\n\n")
            
            # Parse and show calculation
            parser = SpellingParser(self.solution['letter_values'])
            components = parser.parse_components(result['spelling'])
            
            self.explorer_text.insert(tk.END, "Components:\n")
            for word, magnitude in components:
                word_val = parser.word_product(word)
                letters = [c for c in word if c.isalpha()]
                letter_str = " × ".join(letters)
                self.explorer_text.insert(tk.END, 
                    f"  {word} (magnitude {magnitude})\n")
                self.explorer_text.insert(tk.END, 
                    f"    = {letter_str}\n")
                self.explorer_text.insert(tk.END, 
                    f"    = {word_val:.4f}\n\n")
            
            self.explorer_text.insert(tk.END, "-" * 60 + "\n")
            self.explorer_text.insert(tk.END, "Calculation:\n")
            self.explorer_text.insert(tk.END, f"  {result['explanation']}\n\n")
            
            self.explorer_text.insert(tk.END, "-" * 60 + "\n")
            self.explorer_text.insert(tk.END, f"Spelled Value: {result['spelled_value']:.4f}\n")
            self.explorer_text.insert(tk.END, f"Target Value:  {result['number']}\n")
            self.explorer_text.insert(tk.END, f"Error:         {result['error']:.4f}\n\n")
            
            if result['is_solved']:
                self.explorer_text.insert(tk.END, "✓ SOLVED! ", 'success')
                self.explorer_text.tag_config('success', foreground='green', font=('Arial', 11, 'bold'))
            else:
                diff = abs(result['spelled_value'] - result['number'])
                self.explorer_text.insert(tk.END, f"✗ Not solved (off by {diff:.4f})", 'fail')
                self.explorer_text.tag_config('fail', foreground='orange', font=('Arial', 11, 'bold'))
            
        except ValueError:
            self.explorer_text.delete(1.0, tk.END)
            self.explorer_text.insert(tk.END, "Please enter a valid integer.")
    
    def export_results(self):
        """Export results to a file"""
        if not self.solution:
            return
        
        try:
            if not self.optimizer:
                messagebox.showerror("Error", "No optimizer context for export")
                return
            filename = f"spelling_results_{getattr(self.optimizer,'start_range','X')}_to_{getattr(self.optimizer,'end_range','Y')}.txt"
            
            with open(filename, 'w') as f:
                f.write("Spelling Numbers with Variables - Results\n")
                f.write("=" * 70 + "\n\n")
                
                f.write(f"Range: {getattr(self.optimizer,'start_range','?')} to {getattr(self.optimizer,'end_range','?')}\n")
                f.write(f"Solved: {self.solution['solved_count']} / {self.solution['total_count']}\n")
                f.write(f"Total Error: {self.solution['total_error']:.2f}\n\n")
                
                f.write("Letter Values:\n")
                f.write("-" * 30 + "\n")
                for letter in sorted(self.solution['letter_values'].keys()):
                    value = self.solution['letter_values'][letter]
                    f.write(f"{letter}: {value:9.4f}\n")
                
                f.write("\n" + "=" * 70 + "\n")
                f.write("Detailed Results:\n")
                f.write("=" * 70 + "\n\n")
                
                for result in self.solution['results']:
                    status = "✓ SOLVED" if result['is_solved'] else "✗ Not Solved"
                    f.write(f"{result['number']:4d}: {result['spelling']}\n")
                    f.write(f"      Spelled Value: {result['spelled_value']:.4f}\n")
                    f.write(f"      Error: {result['error']:.4f} {status}\n\n")
            
            messagebox.showinfo("Success", f"Results exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")
    
    def reset_app(self):
        """Reset the application"""
        self.is_solving = False
        self.optimizer = None
        self.solution = None
        
        self.notebook.tab(0, state='normal')
        self.notebook.tab(1, state='disabled')
        self.notebook.tab(2, state='disabled')
        self.notebook.select(0)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = SpellingNumbersApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
