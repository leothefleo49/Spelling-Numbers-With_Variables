"""
Spelling Numbers Application - Modern UI with Dark Mode & Performance Controls
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import multiprocessing as mp
import traceback
from logger_setup import get_logger
from optimizer import LetterValueOptimizer
from spelling_parser import SpellingParser
from number_to_words import number_to_words


class ModernSpellingApp:
    """Modern app with dark mode, scrolling, and CPU controls"""
    
    LIGHT_THEME = {
        'bg': '#F0F2F5', 'card': '#FFFFFF', 'card_border': '#D1D5DB',
        'primary': '#4A6FA5', 'primary_hover': '#3A5F95', 'secondary': '#6BA3CF',
        'accent': '#DC3545', 'success': '#28A745', 'warning': '#FFC107',
        'text': '#1F2937', 'text_secondary': '#6B7280',
        'input_bg': '#FFFFFF', 'input_border': '#D1D5DB',
        'console_bg': '#F9FAFB', 'console_text': '#374151',
        'stat_green_bg': '#D1FAE5', 'stat_green_text': '#059669',
        'stat_blue_bg': '#DBEAFE', 'stat_blue_text': '#2563EB',
        'stat_orange_bg': '#FEF3C7', 'stat_orange_text': '#D97706',
        'shadow': '#E5E7EB'
    }
    
    DARK_THEME = {
        'bg': '#1A1D23', 'card': '#25292F', 'card_border': '#3E4450',
        'primary': '#5B9BD5', 'primary_hover': '#4A8AC5', 'secondary': '#70AD47',
        'accent': '#E74C3C', 'success': '#2ECC71', 'warning': '#F39C12',
        'text': '#E8EAED', 'text_secondary': '#9AA0A6',
        'input_bg': '#2D3139', 'input_border': '#4A5261',
        'console_bg': '#1E1E1E', 'console_text': '#D4D4D4',
        'stat_green_bg': '#1E3A32', 'stat_green_text': '#2ECC71',
        'stat_blue_bg': '#1E2838', 'stat_blue_text': '#5B9BD5',
        'stat_orange_bg': '#3A2E1E', 'stat_orange_text': '#F39C12',
        'shadow': '#0D0F12'
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("Spelling Numbers Calculator - Advanced Edition")
        self.root.minsize(900, 600)
        
        # Responsive sizing
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = min(int(sw * 0.7), 1400), min(int(sh * 0.8), 900)
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        
        # Theme
        self.is_dark_mode = tk.BooleanVar(value=True)
        self.colors = self.DARK_THEME.copy()
        self.root.configure(bg=self.colors['bg'])
        
        # Fullscreen state
        self.is_fullscreen = False
        
        # State
        self.optimizer = None
        self.is_solving = False
        self.solution = None
        # Logger
        self.logger = get_logger('app_gui')
        
        # Config vars
        self.decimal_places_var = tk.IntVar(value=4)
        self.auto_decimal_var = tk.BooleanVar(value=True)  # Auto enabled by default
        self.allow_negative_var = tk.BooleanVar(value=True)
        self.space_operator_var = tk.StringVar(value='auto')
        self.hyphen_operator_var = tk.StringVar(value='minus')
        self.cpu_usage_var = tk.StringVar(value='auto')
        
        # Build UI
        self.create_header()
        self.setup_notebook()
        self.build_setup_tab()
        self.build_solving_tab()
        self.build_results_tab()
        
        self.notebook.tab(1, state='disabled')
        self.notebook.tab(2, state='disabled')
        
        # Scrolling
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        widget = event.widget
        while widget != self.root:
            if isinstance(widget, (tk.Canvas, scrolledtext.ScrolledText)):
                try:
                    if isinstance(widget, tk.Canvas):
                        widget.yview_scroll(int(-1*(event.delta/120)), "units")
                    else:
                        widget.yview_scroll(int(-1*(event.delta/120)), "units")
                except:
                    pass
                return
            try:
                widget = widget.master
            except:
                break
    
    def toggle_theme(self):
        """Toggle dark/light mode"""
        self.is_dark_mode.set(not self.is_dark_mode.get())
        self.colors = self.DARK_THEME if self.is_dark_mode.get() else self.LIGHT_THEME
        
        # Store current state
        current_tab = self.notebook.index(self.notebook.select()) if hasattr(self, 'notebook') else 0
        
        # Destroy and rebuild
        for w in self.root.winfo_children():
            w.destroy()
        
        # Reinitialize
        self.__init__(self.root)
        
        # Restore tab if possible
        try:
            self.notebook.select(current_tab)
        except:
            pass
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        
        # ESC key to exit fullscreen
        if self.is_fullscreen:
            self.root.bind('<Escape>', lambda e: self.toggle_fullscreen())
        else:
            self.root.unbind('<Escape>')
    
    def create_header(self):
        """Create header with theme toggle"""
        header = tk.Frame(self.root, bg=self.colors['primary'], height=70)
        header.grid(row=0, column=0, sticky='ew')
        header.grid_propagate(False)
        
        title_frame = tk.Frame(header, bg=self.colors['primary'])
        title_frame.pack(side='left', padx=20, pady=10)
        
        tk.Label(title_frame, text="✨ Spelling Numbers Calculator",
                font=('Segoe UI', 22, 'bold'), fg='white',
                bg=self.colors['primary']).pack(anchor='w')
        
        tk.Label(title_frame, text="AI-Powered Optimizer with Dark Mode & Performance Controls",
                font=('Segoe UI', 10), fg='#E8EAED',
                bg=self.colors['primary']).pack(anchor='w')
        
        controls_frame = tk.Frame(header, bg=self.colors['primary'])
        controls_frame.pack(side='right', padx=20)
        
        # Fullscreen toggle
        self.is_fullscreen = False
        fullscreen_btn = tk.Button(controls_frame, text="⛶ Fullscreen",
                                   command=self.toggle_fullscreen, font=('Segoe UI', 10, 'bold'),
                                   bg=self.colors['bg'], fg=self.colors['text'],
                                   relief='flat', padx=15, pady=8, cursor='hand2', bd=0)
        fullscreen_btn.pack(side='left', padx=(0, 10))
        fullscreen_btn.bind('<Enter>', lambda e: fullscreen_btn.config(bg=self.colors['card']))
        fullscreen_btn.bind('<Leave>', lambda e: fullscreen_btn.config(bg=self.colors['bg']))
        
        # Theme toggle
        icon = "🌙" if not self.is_dark_mode.get() else "☀️"
        text = "Dark" if not self.is_dark_mode.get() else "Light"
        
        theme_btn = tk.Button(controls_frame, text=f"{icon} {text}",
                             command=self.toggle_theme, font=('Segoe UI', 10, 'bold'),
                             bg=self.colors['bg'], fg=self.colors['text'],
                             relief='flat', padx=15, pady=8, cursor='hand2', bd=0)
        theme_btn.pack(side='left')
        theme_btn.bind('<Enter>', lambda e: theme_btn.config(bg=self.colors['card']))
        theme_btn.bind('<Leave>', lambda e: theme_btn.config(bg=self.colors['bg']))
    
    def setup_notebook(self):
        """Setup tabbed interface with modern styling"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.colors['bg'], borderwidth=0, relief='flat')
        style.configure('TNotebook.Tab', padding=[25, 15], font=('Segoe UI', 11, 'bold'),
                       background=self.colors['card'], foreground=self.colors['text'],
                       borderwidth=2, relief='flat')
        style.map('TNotebook.Tab', 
                 background=[('selected', self.colors['primary']), ('active', self.colors['primary_hover'])],
                 foreground=[('selected', 'white'), ('active', 'white')],
                 expand=[('selected', [2, 2, 2, 0])])
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky='nsew', padx=15, pady=(10, 15))
        
        self.setup_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.solving_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.results_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        
        self.notebook.add(self.setup_tab, text="⚙️  Setup")
        self.notebook.add(self.solving_tab, text="⚡  Solving")
        self.notebook.add(self.results_tab, text="📊  Results")
    
    def create_card(self, parent, title=None, pack_opt=None):
        """Create card container with modern styling"""
        if pack_opt is None:
            pack_opt = {'pady': 10, 'padx': 15, 'fill': 'both', 'expand': True}
        
        # Outer frame for shadow effect
        shadow = tk.Frame(parent, bg=self.colors.get('shadow', self.colors['card_border']))
        shadow.pack(**pack_opt)
        
        card = tk.Frame(shadow, bg=self.colors['card'], relief='flat', bd=0,
                       highlightbackground=self.colors['card_border'], highlightthickness=2)
        card.pack(padx=(0, 2), pady=(0, 2), fill='both', expand=True)
        
        if title:
            header = tk.Frame(card, bg=self.colors['primary'], height=45)
            header.pack(fill='x')
            header.pack_propagate(False)
            tk.Label(header, text=title, font=('Segoe UI', 12, 'bold'),
                    fg='white', bg=self.colors['primary']).pack(pady=12, padx=15, anchor='w')
        
        content = tk.Frame(card, bg=self.colors['card'])
        content.pack(fill='both', expand=True, padx=20, pady=15)
        return content
    
    def create_button(self, parent, text, command, color='primary', **kw):
        """Create styled button with modern effects"""
        bg = self.colors[color] if color in self.colors else self.colors['primary']
        hover = self.colors.get(f'{color}_hover', self.colors['primary_hover'])
        
        # Button shadow frame
        shadow_frame = tk.Frame(parent, bg=self.colors.get('shadow', self.colors['card_border']))
        
        btn = tk.Button(shadow_frame, text=text, command=command, bg=bg, fg='white',
                       font=('Segoe UI', 12, 'bold'), relief='flat', bd=0,
                       padx=35, pady=14, cursor='hand2', **kw)
        btn.pack(padx=(0, 2), pady=(0, 2))
        
        def on_enter(e):
            btn.config(bg=hover)
            shadow_frame.config(bg=hover)
        
        def on_leave(e):
            btn.config(bg=bg)
            shadow_frame.config(bg=self.colors.get('shadow', self.colors['card_border']))
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        shadow_frame.bind('<Enter>', on_enter)
        shadow_frame.bind('<Leave>', on_leave)
        
        return shadow_frame
    
    def create_scrollable_frame(self, parent):
        """Create scrollable frame with better mousewheel handling"""
        container = tk.Frame(parent, bg=self.colors['bg'])
        container.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(container, bg=self.colors['bg'], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors['bg'])
        
        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.update_idletasks()
        
        scrollable.bind("<Configure>", on_configure)
        frame_id = canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(frame_id, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Better mousewheel binding
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
        
        def bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        def unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")  
        
        canvas.bind('<Enter>', bind_mousewheel)
        canvas.bind('<Leave>', unbind_mousewheel)
        
        # Force update after packing
        canvas.update_idletasks()
        
        return scrollable
    
    def build_setup_tab(self):
        """Build setup tab"""
        sf = self.create_scrollable_frame(self.setup_tab)
        
        # Welcome
        w = self.create_card(sf, None, {'pady': 15, 'padx': 15, 'fill': 'x'})
        tk.Label(w, text="🎯 Configure Optimization", font=('Segoe UI', 18, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(pady=(0, 8))
        tk.Label(w, text="Find optimal letter values (A-Z) for number spellings",
                font=('Segoe UI', 11), fg=self.colors['text_secondary'],
                bg=self.colors['card']).pack()
        
        # Range
        rc = self.create_card(sf, "📏 Number Range")
        rf = tk.Frame(rc, bg=self.colors['card'])
        rf.pack(fill='x', pady=8)
        rf.grid_columnconfigure(1, weight=1)
        rf.grid_columnconfigure(3, weight=1)
        
        tk.Label(rf, text="Start:", font=('Segoe UI', 10, 'bold'),
                bg=self.colors['card'], fg=self.colors['text']).grid(row=0, column=0, sticky='w', padx=(0, 10), pady=8)
        self.start_entry = self.create_entry(rf)
        self.start_entry.grid(row=0, column=1, sticky='ew', padx=(0, 20), pady=8)
        self.start_entry.insert(0, "-100")
        
        tk.Label(rf, text="End:", font=('Segoe UI', 10, 'bold'),
                bg=self.colors['card'], fg=self.colors['text']).grid(row=0, column=2, sticky='w', padx=(0, 10), pady=8)
        self.end_entry = self.create_entry(rf)
        self.end_entry.grid(row=0, column=3, sticky='ew', pady=8)
        self.end_entry.insert(0, "100")
        
        # Algorithm
        ac = self.create_card(sf, "🧬 Algorithm")
        af = tk.Frame(ac, bg=self.colors['card'])
        af.pack(fill='x', pady=8)
        af.grid_columnconfigure(1, weight=1)
        af.grid_columnconfigure(3, weight=1)
        
        tk.Label(af, text="Population:", font=('Segoe UI', 10, 'bold'),
                bg=self.colors['card'], fg=self.colors['text']).grid(row=0, column=0, sticky='w', padx=(0, 10), pady=8)
        self.pop_entry = self.create_entry(af)
        self.pop_entry.grid(row=0, column=1, sticky='ew', padx=(0, 20), pady=8)
        self.pop_entry.insert(0, "100")
        
        tk.Label(af, text="💡 Larger = better", font=('Segoe UI', 9),
                fg=self.colors['text_secondary'], bg=self.colors['card']).grid(row=0, column=2, columnspan=2, sticky='w', padx=5)
        
        tk.Label(af, text="Generations:", font=('Segoe UI', 10, 'bold'),
                bg=self.colors['card'], fg=self.colors['text']).grid(row=1, column=0, sticky='w', padx=(0, 10), pady=8)
        self.gen_entry = self.create_entry(af)
        self.gen_entry.grid(row=1, column=1, sticky='ew', padx=(0, 20), pady=8)
        self.gen_entry.insert(0, "100")
        
        tk.Label(af, text="💡 More = better convergence", font=('Segoe UI', 9),
                fg=self.colors['text_secondary'], bg=self.colors['card']).grid(row=1, column=2, columnspan=2, sticky='w', padx=5)

        # Method selector
        tk.Label(af, text="Method:", font=('Segoe UI', 10, 'bold'),
            bg=self.colors['card'], fg=self.colors['text']).grid(row=2, column=0, sticky='w', padx=(0,10), pady=8)
        self.method_var = tk.StringVar(value='genetic')
        method_combo = ttk.Combobox(af, textvariable=self.method_var,
                        values=['genetic','linear'], state='readonly', font=('Segoe UI',10))
        method_combo.grid(row=2, column=1, sticky='ew', padx=(0,20), pady=8)
        tk.Label(af, text="linear = analytic (fast, additive)", font=('Segoe UI', 9),
            fg=self.colors['text_secondary'], bg=self.colors['card']).grid(row=2, column=2, columnspan=2, sticky='w', padx=5)
        
        # CPU Performance
        cpu_card = self.create_card(sf, "⚡ Performance Control")
        total_cores = mp.cpu_count()
        
        tk.Label(cpu_card, text=f"System: {total_cores} CPU cores detected",
                font=('Segoe UI', 10), fg=self.colors['text_secondary'],
                bg=self.colors['card']).pack(pady=(0, 10))
        
        cpu_frame = tk.Frame(cpu_card, bg=self.colors['card'])
        cpu_frame.pack(fill='x', pady=8)
        
        tk.Label(cpu_frame, text="CPU Usage:", font=('Segoe UI', 10, 'bold'),
                bg=self.colors['card'], fg=self.colors['text']).pack(side='left', padx=(0, 10))
        
        cpu_opts = ['auto', '25%', '50%', '75%', '100%'] + [str(i) for i in range(1, total_cores+1)]
        cpu_combo = ttk.Combobox(cpu_frame, textvariable=self.cpu_usage_var,
                                values=cpu_opts, state='readonly', width=10, font=('Segoe UI', 10))
        cpu_combo.pack(side='left', padx=5)
        cpu_combo.bind('<<ComboboxSelected>>', self.update_cpu_info)
        
        self.cpu_info = tk.Label(cpu_frame, text="Auto: uses all but 1 core",
                                font=('Segoe UI', 9), fg=self.colors['success'],
                                bg=self.colors['card'])
        self.cpu_info.pack(side='left', padx=10)
        
        # Add advanced settings
        self.add_setup_advanced(sf)
    
    def create_entry(self, parent):
        """Create styled entry"""
        e = tk.Entry(parent, font=('Segoe UI', 11), bg=self.colors['input_bg'],
                    fg=self.colors['text'], insertbackground=self.colors['text'],
                    relief='solid', bd=1, highlightthickness=1,
                    highlightbackground=self.colors['input_border'],
                    highlightcolor=self.colors['primary'])
        return e
    
    def update_cpu_info(self, event=None):
        """Update CPU usage info"""
        val = self.cpu_usage_var.get()
        total = mp.cpu_count()
        if val == 'auto':
            cores = max(1, total - 1)
            self.cpu_info.config(text=f"Auto: uses {cores}/{total} cores", fg=self.colors['success'])
        elif '%' in val:
            pct = int(val[:-1])
            cores = max(1, int(total * pct / 100))
            self.cpu_info.config(text=f"{pct}% = {cores}/{total} cores", fg=self.colors['warning'])
        else:
            cores = int(val)
            self.cpu_info.config(text=f"Using {cores}/{total} cores", fg=self.colors['accent'])
    
    def add_setup_advanced(self, sf):
        """Add advanced settings to setup"""
        # Advanced
        adv = self.create_card(sf, "⚙️ Advanced")
        
        # Auto-decimals toggle (prominent)
        auto_frame = tk.Frame(adv, bg=self.colors['stat_green_bg'], relief='solid', bd=2,
                             highlightbackground=self.colors['success'], highlightthickness=1)
        auto_frame.pack(fill='x', pady=(0, 15), padx=5)
        
        auto_inner = tk.Frame(auto_frame, bg=self.colors['stat_green_bg'])
        auto_inner.pack(pady=15, padx=20)
        
        tk.Checkbutton(auto_inner, text="🤖 Auto-Adaptive Decimals (Recommended)",
                      variable=self.auto_decimal_var,
                      font=('Segoe UI', 12, 'bold'), bg=self.colors['stat_green_bg'],
                      fg=self.colors['stat_green_text'],
                      activebackground=self.colors['stat_green_bg'],
                      selectcolor=self.colors['input_bg'],
                      command=self.toggle_decimal_auto).pack()
        
        tk.Label(auto_inner, text="Automatically adjusts precision 0→100 decimals as needed for best results",
                font=('Segoe UI', 9), bg=self.colors['stat_green_bg'],
                fg=self.colors['stat_green_text']).pack(pady=(5, 0))
        
        # Manual decimal control
        df = tk.Frame(adv, bg=self.colors['card'])
        df.pack(fill='x', pady=12)
        df.grid_columnconfigure(1, weight=1)
        
        tk.Label(df, text="Manual Decimals:", font=('Segoe UI', 10, 'bold'),
                bg=self.colors['card'], fg=self.colors['text']).grid(row=0, column=0, sticky='w', pady=5)
        
        sc = tk.Frame(df, bg=self.colors['card'])
        sc.grid(row=0, column=1, sticky='ew', padx=15)
        
        dec_inner = tk.Frame(sc, bg=self.colors['card'])
        dec_inner.pack(side='left', fill='x', expand=True)
        
        self.decimal_scale = tk.Scale(dec_inner, from_=0, to=100, orient='horizontal',
                                      variable=self.decimal_places_var, font=('Segoe UI', 9),
                                      bg=self.colors['card'], fg=self.colors['text'],
                                      troughcolor=self.colors['input_bg'],
                                      activebackground=self.colors['primary'],
                                      highlightthickness=0, command=self.update_decimal_warning)
        self.decimal_scale.pack(side='left', fill='x', expand=True)
        
        self.decimal_label = tk.Label(sc, text="4 decimals", font=('Segoe UI', 10, 'bold'),
                                      bg=self.colors['card'], fg=self.colors['primary'])
        self.decimal_label.pack(side='left', padx=15)
        
        self.decimal_warning = tk.Label(adv, text="⚠️ Moderate impact",
                                       font=('Segoe UI', 10), fg=self.colors['warning'],
                                       bg=self.colors['card'])
        self.decimal_warning.pack(pady=(0, 15))
        
        # Negative
        nf = tk.Frame(adv, bg=self.colors['card'])
        nf.pack(fill='x', pady=8)
        
        tk.Label(nf, text="Constraints:", font=('Segoe UI', 10, 'bold'),
                bg=self.colors['card'], fg=self.colors['text']).pack(side='left', padx=(0, 15))
        
        tk.Checkbutton(nf, text="Allow Negative Values", variable=self.allow_negative_var,
                      font=('Segoe UI', 10), bg=self.colors['card'], fg=self.colors['text'],
                      activebackground=self.colors['card'], activeforeground=self.colors['text'],
                      selectcolor=self.colors['input_bg']).pack(side='left')
        
        tk.Label(nf, text="💡 For negative numbers", font=('Segoe UI', 9),
                fg=self.colors['text_secondary'], bg=self.colors['card']).pack(side='left', padx=10)
        
        # Operators
        opc = self.create_card(sf, "🔧 Operators")
        of = tk.Frame(opc, bg=self.colors['card'])
        of.pack(fill='x', pady=8)
        of.grid_columnconfigure(1, weight=1)
        of.grid_columnconfigure(3, weight=1)
        
        tk.Label(of, text="Space:", font=('Segoe UI', 10, 'bold'),
                bg=self.colors['card'], fg=self.colors['text']).grid(row=0, column=0, sticky='w', padx=(0, 10), pady=8)
        ttk.Combobox(of, textvariable=self.space_operator_var,
                    values=['auto', 'multiply', 'add', 'subtract', 'divide'],
                    state='readonly', font=('Segoe UI', 10)).grid(row=0, column=1, sticky='ew', padx=(0, 20), pady=8)
        
        tk.Label(of, text="Hyphen:", font=('Segoe UI', 10, 'bold'),
                bg=self.colors['card'], fg=self.colors['text']).grid(row=1, column=0, sticky='w', padx=(0, 10), pady=8)
        ttk.Combobox(of, textvariable=self.hyphen_operator_var,
                    values=['minus', 'multiply', 'add', 'divide'],
                    state='readonly', font=('Segoe UI', 10)).grid(row=1, column=1, sticky='ew', padx=(0, 20), pady=8)
        
        # Start button
        bf = tk.Frame(sf, bg=self.colors['bg'])
        bf.pack(pady=25)
        self.calc_button = self.create_button(bf, "🚀 Start Calculation", self.start_optimization, 'success')
        self.calc_button.pack()
        
        tk.Frame(sf, bg=self.colors['bg'], height=20).pack()
    
    def toggle_decimal_auto(self):
        """Toggle auto-adaptive decimals"""
        if self.auto_decimal_var.get():
            self.decimal_scale.config(state='disabled')
            self.decimal_label.config(text="AUTO", fg=self.colors['success'])
            self.decimal_warning.config(text="🤖 Adapts 0→100 decimals intelligently", fg=self.colors['success'])
        else:
            self.decimal_scale.config(state='normal')
            self.update_decimal_warning(self.decimal_places_var.get())
    
    def update_decimal_warning(self, value):
        """Update decimal warning"""
        if self.auto_decimal_var.get():
            return
        d = int(float(value))
        self.decimal_label.config(text=f"{d} decimal{'s' if d != 1 else ''}")
        if d == 0:
            self.decimal_warning.config(text="⚡ Integers - fastest!", fg=self.colors['success'])
        elif d <= 2:
            self.decimal_warning.config(text="✓ Good balance", fg=self.colors['success'])
        elif d <= 4:
            self.decimal_warning.config(text="⚠️ Moderate impact", fg=self.colors['warning'])
        else:
            self.decimal_warning.config(text="🔥 High precision - slower!", fg=self.colors['accent'])

    
    def start_optimization(self):
        """Start optimization with CPU control"""
        try:
            start, end = int(self.start_entry.get()), int(self.end_entry.get())
            pop, gen = int(self.pop_entry.get()), int(self.gen_entry.get())
            dec = 'auto' if self.auto_decimal_var.get() else self.decimal_places_var.get()
            neg = self.allow_negative_var.get()
            sp_op, hy_op = self.space_operator_var.get(), self.hyphen_operator_var.get()
            cpu = self.cpu_usage_var.get()
            
            if start >= end or pop < 10 or gen < 1:
                messagebox.showerror("Error", "Invalid parameters")
                return
            
            if dec != 'auto' and dec > 4:
                if not messagebox.askyesno("Warning", f"{dec} decimals will be slower. Continue?"):
                    return
            
            eval_mode = 'linear' if getattr(self, 'method_var', None) and self.method_var.get() == 'linear' else 'product'
            self.optimizer = LetterValueOptimizer(start, end, pop, 0.1, dec, neg, sp_op, hy_op, cpu, evaluation_mode=eval_mode)
            self.is_solving = True
            self.max_generations = gen
            
            self.notebook.tab(1, state='normal')
            self.notebook.select(1)
            self.notebook.tab(0, state='disabled')
            
            # Clear and initialize log
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, "🚀 Starting intelligent optimization...\n\n")
            self.log_text.insert(tk.END, "🧠 Analyzing constraints and logical deductions...\n")
            self.log_text.insert(tk.END, f"   Found {len(self.optimizer.letter_constraints)} fixed letters\n")
            self.log_text.insert(tk.END, f"   Found {len(self.optimizer.letter_hints)} constrained ranges\n\n")
            self.log_text.insert(tk.END, f"Range: {start} to {end}\n")
            self.log_text.insert(tk.END, f"Population: {pop} | Generations: {gen}\n")
            self.log_text.insert(tk.END, f"Decimals: {dec} (0-100 adaptive) | Negatives: {neg}\n")
            self.log_text.insert(tk.END, f"Operators: Space={sp_op}, Hyphen={hy_op}\n")
            self.log_text.insert(tk.END, f"CPU: {cpu}\n")
            self.log_text.insert(tk.END, f"Method: {eval_mode}\n")
            self.log_text.insert(tk.END, "="*60 + "\n\n")
            
            self.progress_bar['value'] = 0
            self.progress_bar['maximum'] = gen
            
            threading.Thread(target=self.run_optimization, daemon=True).start()
        except Exception as e:
            # Log and surface startup errors
            self.logger.exception("Failed to start optimization")
            messagebox.showerror("Error", f"{e}\nSee error.log for details.")
    
    def run_optimization(self):
        """Run optimization loop with progress updates"""
        try:
            # Verify optimizer is initialized
            if not self.optimizer or not hasattr(self.optimizer, 'population'):
                raise RuntimeError("Optimizer not properly initialized")
            
            if not self.optimizer.population:
                raise RuntimeError("Optimizer population is empty")
            
            for gen in range(self.max_generations):
                if not self.is_solving:
                    self.root.after(0, lambda: self.log_text.insert(tk.END, "\n⏹️ Stopped by user\n"))
                    break
                
                stats = self.optimizer.evolve_generation()
                self.root.after(0, self.update_progress, stats)
            
            if self.is_solving:
                self.root.after(0, self.optimization_complete)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            # Log full stack trace
            self.logger.exception("Unhandled error during optimization loop")
            self.root.after(0, lambda: self.log_text.insert(tk.END, f"\n❌ ERROR:\n{error_details}\n"))
            self.root.after(0, lambda e=e: messagebox.showerror("Optimization Error", f"Error: {str(e)}\n\nSee error.log for full details."))
            self.root.after(0, self.reset_to_setup)
    
    def update_progress(self, stats):
        """Update progress UI with stats"""
        self.gen_label.config(text=f"{stats['generation']} / {self.max_generations}")
        self.solved_label.config(text=f"{stats['solved_count']} / {stats['total_numbers']}")
        self.fitness_label.config(text=f"{stats['best_fitness']:.2f}")
        
        self.progress_bar['value'] = stats['generation']
        
        percentage = (stats['solved_count'] / stats['total_numbers'] * 100) if stats['total_numbers'] > 0 else 0
        
        log_msg = (f"[Gen {stats['generation']:3d}] "
                  f"Solved: {stats['solved_count']:3d}/{stats['total_numbers']:3d} ({percentage:.1f}%) | "
                  f"Error: {stats['best_fitness']:8.2f}")
        
        # Add adaptive info
        if 'decimal_places' in stats:
            log_msg += f" | Dec: {stats['decimal_places']}"
        if stats.get('decimal_changed', False):
            log_msg += f" ⬆️ INCREASED PRECISION"
        if 'cpu_cores' in stats and self.optimizer and hasattr(self.optimizer, 'dynamic_cpu') and self.optimizer.dynamic_cpu:
            log_msg += f" | CPU: {stats['cpu_cores']} cores"
        
        log_msg += "\n"
        self.log_text.insert(tk.END, log_msg)
        self.log_text.see(tk.END)
    
    def stop_optimization(self):
        """Stop the optimization"""
        self.is_solving = False
        self.log_text.insert(tk.END, "\n⏹️ Stopping optimization...\n")
        
        if self.optimizer and self.optimizer.best_solution:
            self.root.after(100, self.optimization_complete)
        else:
            self.root.after(100, self.reset_to_setup)
    
    def reset_to_setup(self):
        """Reset to setup tab"""
        self.is_solving = False
        self.optimizer = None
        self.solution = None
        
        self.notebook.tab(0, state='normal')
        self.notebook.tab(1, state='disabled')
        self.notebook.tab(2, state='disabled')
        self.notebook.select(0)
    
    def optimization_complete(self):
        """Handle completion and populate results"""
        self.is_solving = False
        
        if not self.optimizer:
            self.reset_to_setup()
            return
        
        self.solution = self.optimizer.get_solution_details()
        
        if not self.solution:
            messagebox.showerror("Error", "No solution found")
            self.reset_to_setup()
            return
        
        # Update summary
        pct = (self.solution['solved_count'] / self.solution['total_count'] * 100) if self.solution['total_count'] > 0 else 0
        self.results_summary.config(
            text=f"Solved {self.solution['solved_count']} of {self.solution['total_count']} numbers ({pct:.1f}%) | Total Error: {self.solution['total_error']:.4f}")
        
        # Update letter values
        for letter, value in self.solution['letter_values'].items():
            if letter in self.letter_labels:
                self.letter_labels[letter].config(text=f"{value:7.4f}")
        
        # Clear and populate results tree
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        for result in self.solution['results']:
            status = "✓ Solved" if result['is_solved'] else "✗ Error"
            tag = 'solved' if result['is_solved'] else 'unsolved'
            
            self.results_tree.insert('', 'end', values=(
                result['number'],
                result['spelling'],
                f"{result['spelled_value']:.4f}",
                f"{result['error']:.6f}",
                status
            ), tags=(tag,))
        
        # Color coding
        self.results_tree.tag_configure('solved', foreground=self.colors['success'])
        self.results_tree.tag_configure('unsolved', foreground=self.colors['accent'])
        
        self.notebook.tab(2, state='normal')
        self.notebook.select(2)
        messagebox.showinfo("Complete", f"Solved {self.solution['solved_count']} of {self.solution['total_count']} numbers!\n\nAccuracy: {pct:.1f}%")
    
    def build_solving_tab(self):
        """Build solving tab with progress tracking"""
        self.solving_tab.grid_rowconfigure(0, weight=1)
        self.solving_tab.grid_columnconfigure(0, weight=1)
        
        # Progress card
        pc = self.create_card(self.solving_tab, "⚡ Optimization Progress",
                             {'pady': 15, 'padx': 15, 'fill': 'both', 'expand': True})
        
        # Stats grid
        sf = tk.Frame(pc, bg=self.colors['card'])
        sf.pack(fill='x', pady=15)
        sf.grid_columnconfigure(0, weight=1)
        sf.grid_columnconfigure(1, weight=1)
        sf.grid_columnconfigure(2, weight=1)
        
        # Generation stat
        gen_stat = tk.Frame(sf, bg=self.colors['stat_green_bg'],
                           highlightbackground=self.colors['card_border'], highlightthickness=1)
        gen_stat.grid(row=0, column=0, padx=8, pady=5, sticky='ew')
        tk.Label(gen_stat, text="Generation", font=('Segoe UI', 10),
                bg=self.colors['stat_green_bg'], fg=self.colors['stat_green_text']).pack(pady=(10, 2))
        self.gen_label = tk.Label(gen_stat, text="0 / 0", font=('Segoe UI', 20, 'bold'),
                                 bg=self.colors['stat_green_bg'], fg=self.colors['stat_green_text'])
        self.gen_label.pack(pady=(2, 10))
        
        # Solved stat
        solved_stat = tk.Frame(sf, bg=self.colors['stat_blue_bg'],
                              highlightbackground=self.colors['card_border'], highlightthickness=1)
        solved_stat.grid(row=0, column=1, padx=8, pady=5, sticky='ew')
        tk.Label(solved_stat, text="Numbers Solved", font=('Segoe UI', 10),
                bg=self.colors['stat_blue_bg'], fg=self.colors['stat_blue_text']).pack(pady=(10, 2))
        self.solved_label = tk.Label(solved_stat, text="0 / 0", font=('Segoe UI', 20, 'bold'),
                                     bg=self.colors['stat_blue_bg'], fg=self.colors['stat_blue_text'])
        self.solved_label.pack(pady=(2, 10))
        
        # Fitness stat
        fitness_stat = tk.Frame(sf, bg=self.colors['stat_orange_bg'],
                               highlightbackground=self.colors['card_border'], highlightthickness=1)
        fitness_stat.grid(row=0, column=2, padx=8, pady=5, sticky='ew')
        tk.Label(fitness_stat, text="Total Error", font=('Segoe UI', 10),
                bg=self.colors['stat_orange_bg'], fg=self.colors['stat_orange_text']).pack(pady=(10, 2))
        self.fitness_label = tk.Label(fitness_stat, text="N/A", font=('Segoe UI', 20, 'bold'),
                                      bg=self.colors['stat_orange_bg'], fg=self.colors['stat_orange_text'])
        self.fitness_label.pack(pady=(2, 10))
        
        # Progress bar
        prog_cont = tk.Frame(pc, bg=self.colors['card'])
        prog_cont.pack(fill='x', pady=20)
        
        style = ttk.Style()
        style.configure("Custom.Horizontal.TProgressbar",
                       troughcolor=self.colors['input_bg'],
                       background=self.colors['success'],
                       thickness=25)
        
        self.progress_bar = ttk.Progressbar(prog_cont, style="Custom.Horizontal.TProgressbar",
                                           mode='determinate')
        self.progress_bar.pack(fill='x')
        
        # Console log
        log_frame = tk.LabelFrame(pc, text="📜 Console Log",
                                 font=('Segoe UI', 11, 'bold'),
                                 bg=self.colors['card'], fg=self.colors['text'],
                                 bd=1, relief='solid')
        log_frame.pack(fill='both', expand=True, pady=15)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, font=('Consolas', 9),
                                                  bg=self.colors['console_bg'],
                                                  fg=self.colors['console_text'],
                                                  insertbackground=self.colors['console_text'],
                                                  relief='flat', padx=10, pady=10)
        self.log_text.pack(fill='both', expand=True, padx=8, pady=8)
        # View Error Log button
        log_btn_frame = tk.Frame(log_frame, bg=self.colors['card'])
        log_btn_frame.pack(fill='x', padx=8, pady=(0,8))
        view_log_btn = self.create_button(log_btn_frame, "🪵 View error.log", self.view_error_log, 'warning')
        view_log_btn.pack(side='left')
        
        # Stop button
        bf = tk.Frame(self.solving_tab, bg=self.colors['bg'])
        bf.pack(pady=15)
        self.stop_button = self.create_button(bf, "⏹️ Stop Optimization",
                                             self.stop_optimization, 'accent')
        self.stop_button.pack()

    def view_error_log(self):
        """Open and display error.log contents"""
        import os
        log_path = os.path.join(os.getcwd(), 'error.log')
        win = tk.Toplevel(self.root)
        win.title('error.log')
        win.geometry('700x500')
        win.configure(bg=self.colors['bg'])
        txt = scrolledtext.ScrolledText(win, font=('Consolas', 10), bg=self.colors['console_bg'], fg=self.colors['console_text'])
        txt.pack(fill='both', expand=True)
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                txt.insert('1.0', content)
            except Exception as e:
                txt.insert('1.0', f'Failed to read log: {e}')
        else:
            txt.insert('1.0', 'No error.log file found yet.')
    
    def build_results_tab(self):
        """Build comprehensive results tab"""
        sf = self.create_scrollable_frame(self.results_tab)
        
        # Title
        title_card = self.create_card(sf, None, {'pady': 15, 'padx': 15, 'fill': 'x'})
        tk.Label(title_card, text="📊 Optimization Results", font=('Segoe UI', 18, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(pady=(0, 5))
        
        self.results_summary = tk.Label(title_card, text="", font=('Segoe UI', 11),
                                       fg=self.colors['text_secondary'], bg=self.colors['card'])
        self.results_summary.pack()
        
        # Letter Values Card
        letter_card = self.create_card(sf, "🔤 Optimized Letter Values")
        
        lf = tk.Frame(letter_card, bg=self.colors['card'])
        lf.pack(fill='both', expand=True, pady=10)
        
        # Create grid for letter values (5 columns)
        self.letter_labels = {}
        for i in range(26):
            letter = chr(65 + i)
            row, col = i // 5, i % 5
            
            lf.grid_columnconfigure(col, weight=1)
            
            frame = tk.Frame(lf, bg=self.colors['input_bg'], relief='solid', bd=1)
            frame.grid(row=row, column=col, padx=5, pady=3, sticky='ew')
            
            tk.Label(frame, text=letter, font=('Segoe UI', 10, 'bold'),
                    bg=self.colors['input_bg'], fg=self.colors['primary']).pack(side='left', padx=(8, 4))
            
            val_label = tk.Label(frame, text="0.0000", font=('Consolas', 10),
                               bg=self.colors['input_bg'], fg=self.colors['text'])
            val_label.pack(side='left', padx=(4, 8))
            self.letter_labels[letter] = val_label
        
        # Numbers Results Card
        results_card = self.create_card(sf, "📊 Detailed Number Results")
        
        # Create treeview for results
        tree_frame = tk.Frame(results_card, bg=self.colors['card'])
        tree_frame.pack(fill='both', expand=True, pady=10)
        
        # Style for treeview
        style = ttk.Style()
        style.configure("Results.Treeview",
                       background=self.colors['input_bg'],
                       foreground=self.colors['text'],
                       fieldbackground=self.colors['input_bg'],
                       font=('Consolas', 9))
        style.configure("Results.Treeview.Heading",
                       background=self.colors['primary'],
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'))
        
        columns = ('number', 'spelling', 'calculated', 'error', 'status')
        self.results_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                        style="Results.Treeview", height=15)
        
        self.results_tree.heading('number', text='Number')
        self.results_tree.heading('spelling', text='Spelling')
        self.results_tree.heading('calculated', text='Calculated Value')
        self.results_tree.heading('error', text='Error')
        self.results_tree.heading('status', text='Status')
        
        self.results_tree.column('number', width=80, anchor='center')
        self.results_tree.column('spelling', width=250, anchor='w')
        self.results_tree.column('calculated', width=120, anchor='center')
        self.results_tree.column('error', width=100, anchor='center')
        self.results_tree.column('status', width=100, anchor='center')
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.results_tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')
        
        # Explanation frame (for selected number)
        exp_card = self.create_card(sf, "🔍 Calculation Explanation")
        
        self.explanation_text = scrolledtext.ScrolledText(exp_card, font=('Consolas', 9),
                                                         bg=self.colors['console_bg'],
                                                         fg=self.colors['console_text'],
                                                         height=8, wrap='word')
        self.explanation_text.pack(fill='both', expand=True, pady=10)
        
        self.results_tree.bind('<<TreeviewSelect>>', self.on_result_select)
        
        # Buttons
        btn_frame = tk.Frame(sf, bg=self.colors['bg'])
        btn_frame.pack(pady=20)
        
        self.create_button(btn_frame, "🔄 New Optimization", self.new_optimization, 'primary').pack(side='left', padx=5)
        self.create_button(btn_frame, "💾 Export Results", self.export_results, 'secondary').pack(side='left', padx=5)
        
        tk.Frame(sf, bg=self.colors['bg'], height=20).pack()
    
    def on_result_select(self, event):
        """Show explanation for selected result"""
        selection = self.results_tree.selection()
        if not selection or not self.solution:
            return
        
        item = self.results_tree.item(selection[0])
        number = int(item['values'][0])
        
        # Find the result
        result = next((r for r in self.solution['results'] if r['number'] == number), None)
        if result:
            self.explanation_text.delete(1.0, tk.END)
            self.explanation_text.insert(tk.END, f"Number: {result['number']}\n")
            self.explanation_text.insert(tk.END, f"Spelling: {result['spelling']}\n")
            self.explanation_text.insert(tk.END, f"Calculated Value: {result['spelled_value']:.4f}\n")
            self.explanation_text.insert(tk.END, f"Error: {result['error']:.6f}\n")
            self.explanation_text.insert(tk.END, f"\nCalculation:\n{result['explanation']}")
    
    def new_optimization(self):
        """Start a new optimization"""
        self.reset_to_setup()
    
    def export_results(self):
        """Export results to file"""
        if not self.solution:
            return
        
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                               filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("SPELLING NUMBERS OPTIMIZATION RESULTS\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(f"Solved: {self.solution['solved_count']}/{self.solution['total_count']} numbers\n")
                    f.write(f"Total Error: {self.solution['total_error']:.4f}\n\n")
                    
                    f.write("LETTER VALUES:\n")
                    f.write("-" * 60 + "\n")
                    for letter, value in sorted(self.solution['letter_values'].items()):
                        f.write(f"{letter}: {value:8.4f}\n")
                    
                    f.write("\n\nDETAILED RESULTS:\n")
                    f.write("-" * 60 + "\n")
                    for result in self.solution['results']:
                        status = "✓ SOLVED" if result['is_solved'] else "✗ UNSOLVED"
                        f.write(f"\n{result['number']:4d} | {status}\n")
                        f.write(f"  Spelling: {result['spelling']}\n")
                        f.write(f"  Calculated: {result['spelled_value']:.4f}\n")
                        f.write(f"  Error: {result['error']:.6f}\n")
                
                messagebox.showinfo("Success", f"Results exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")


def main():
    root = tk.Tk()
    app = ModernSpellingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()




