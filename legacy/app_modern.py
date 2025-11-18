"""
Spelling Numbers Application - Modern UI reimagined with ttkbootstrap styling.
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttkb
from tkinter import ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
import threading
import time
import os
from logger_setup import get_logger
from optimizer import LetterValueOptimizer
from spelling_parser import SpellingParser
from number_to_words import number_to_words
import string


class ModernSpellingApp:
    """Modern app with ttkbootstrap styling and glassy layout"""
    
    LIGHT_THEME = {
        'bg': '#E9EEF6', 'card': '#F7F9FC', 'card_border': '#D6DFEB',
        'primary': '#3465FE', 'primary_hover': '#264FD9', 'secondary': '#3FD6C6',
        'accent': '#FF7F50', 'success': '#2EC27E', 'warning': '#FFCB42',
        'text': '#12263F', 'text_secondary': '#4B5C79',
        'input_bg': '#FFFFFF', 'input_border': '#C0CCDA',
        'console_bg': '#10121A', 'console_text': '#E4E8F1',
        'stat_green_bg': '#CFF6E4', 'stat_green_text': '#146C43',
        'stat_blue_bg': '#D7E2FF', 'stat_blue_text': '#1E2A78',
        'stat_orange_bg': '#FFE6C7', 'stat_orange_text': '#7A3000',
        'shadow': '#B2BCCF', 'button_text': '#F8FBFF',
        'knob_on': '#2EC27E', 'knob_off': '#5E6784', 'knob_core': '#FFFFFF'
    }
    
    DARK_THEME = {
        'bg': '#0F1522', 'card': '#181F2F', 'card_border': '#273044',
        'primary': '#5A79FF', 'primary_hover': '#4059E9', 'secondary': '#2EC27E',
        'accent': '#FF8C69', 'success': '#2EC27E', 'warning': '#FFCB42',
        'text': '#F5F7FA', 'text_secondary': '#8A93AB',
        'input_bg': '#151B28', 'input_border': '#2F3A54',
        'console_bg': '#0A0E17', 'console_text': '#E0E5F2',
        'stat_green_bg': '#102923', 'stat_green_text': '#3DE0A1',
        'stat_blue_bg': '#111E34', 'stat_blue_text': '#7EA8FF',
        'stat_orange_bg': '#2F1E11', 'stat_orange_text': '#FFCB42',
        'shadow': '#080B12', 'button_text': '#F3F6FF',
        'knob_on': '#2EC27E', 'knob_off': '#404A66', 'knob_core': '#C7CFEC'
    }

    def _configure_styles(self):
        palette = self.colors
        self.style.configure('Glass.TFrame', background=palette['card'], borderwidth=0)
        self.style.configure('GlassBorder.TFrame', background=palette['card'], borderwidth=1, relief='flat')
        self.style.configure('Glass.TLabel', background=palette['card'], foreground=palette['text'])
        self.style.configure('GlassHeader.TLabel', background=palette['primary'], foreground=palette['button_text'], font=('Segoe UI', 12, 'bold'))
        self.style.configure('GlassPrimary.TButton', font=('Segoe UI', 11, 'bold'), padding=10)
        self.style.map('GlassPrimary.TButton', background=[('active', palette['primary_hover'])])
        self.style.configure('GlassSecondary.TButton', font=('Segoe UI', 11, 'bold'), padding=10)
        self.style.configure('Glass.TNotebook', background=palette['bg'])
        self.style.configure('Glass.TNotebook.Tab', padding=[20, 10], font=('Segoe UI', 11, 'bold'))
        self.style.map('Glass.TNotebook.Tab', background=[('selected', palette['primary'])], foreground=[('selected', palette['button_text'])])
        self.style.configure('Glass.Horizontal.TProgressbar', background=palette['success'])
    
    def __init__(self, root):
        self.root = root
        self.style = ttkb.Style()
        self.theme_map = {'dark': 'darkly', 'light': 'flatly'}
        self.active_theme = 'dark'
        self.style.theme_use(self.theme_map[self.active_theme])
        self.root.title("Spelling Numbers Calculator - Advanced Edition")
        self.root.minsize(900, 600)
        
        # Responsive sizing
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = min(int(sw * 0.7), 1400), min(int(sh * 0.8), 900)
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        
        # Theme
        self.is_dark_mode = tk.BooleanVar(value=True)
        self.colors = self.DARK_THEME.copy()
        self._configure_styles()
        self.root.configure(bg=self.colors['bg'])
        
        # Fullscreen state
        self.is_fullscreen = False
        
        # State
        self.optimizer = None
        self.is_solving = False
        self.solution = None
        self.start_time = None
        # Logger
        self.logger = get_logger('app_gui')
        
        # Config vars - Auto enabled by default for everything
        self.decimal_places_var = tk.IntVar(value=4)
        self.auto_decimal_var = tk.BooleanVar(value=True)  # Auto enabled by default
        self.allow_negative_var = tk.BooleanVar(value=True)  # Always enabled by default
        self.space_operator_var = tk.StringVar(value='auto')
        self.hyphen_operator_var = tk.StringVar(value='add')  # Fixed to add for accuracy
        self.cpu_usage_var = tk.StringVar(value='auto')
        self.evaluation_mode_var = tk.StringVar(value='product')
        
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
            if isinstance(widget, (tk.Canvas, ScrolledText)):
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
        
        # Update all widgets recursively instead of destroying
        def update_colors(widget):
            try:
                if isinstance(widget, tk.Frame):
                    widget.configure(bg=self.colors['bg'])
                elif isinstance(widget, tk.Label):
                    widget.configure(bg=self.colors.get('card', self.colors['bg']), fg=self.colors['text'])
                elif isinstance(widget, tk.Button):
                    pass  # Buttons handled by their own bindings
                for child in widget.winfo_children():
                    update_colors(child)
            except:
                pass
        
        try:
            update_colors(self.root)
            self.root.configure(bg=self.colors['bg'])
            messagebox.showinfo("Theme", f"{'Dark' if self.is_dark_mode.get() else 'Light'} mode enabled. Restart for full effect.")
        except Exception as e:
            self.logger.exception("Theme toggle failed")
    
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
        header = ttkb.Frame(self.root, padding=15, bootstyle="primary")
        header.grid(row=0, column=0, sticky='ew')
        header.grid_propagate(False)
        
        title_frame = ttkb.Frame(header, padding=(5, 0))
        title_frame.pack(side='left', padx=10)
        
        header_text = self.colors.get('button_text', '#F6F7FB')
        sub_text = self.colors.get('text_secondary', '#DDE1EA')
        ttkb.Label(title_frame, text="✨ Spelling Numbers Calculator",
            font=('Segoe UI', 22, 'bold'), foreground=header_text).pack(anchor='w')
        
        ttkb.Label(title_frame, text="AI-Powered Optimizer with Dark Mode & Performance Controls",
            font=('Segoe UI', 10), foreground=sub_text).pack(anchor='w')
        
        controls_frame = ttkb.Frame(header)
        controls_frame.pack(side='right', padx=10)
        
        # Fullscreen toggle
        self.is_fullscreen = False
        fullscreen_btn = ttkb.Button(controls_frame, text="⛶ Fullscreen", command=self.toggle_fullscreen,
                         bootstyle="light-outline", padding=(12, 6))
        fullscreen_btn.pack(side='left', padx=(0, 10))
        
        icon = "🌙" if not self.is_dark_mode.get() else "☀️"
        text = "Dark" if not self.is_dark_mode.get() else "Light"
        theme_btn = ttkb.Button(controls_frame, text=f"{icon} {text}", command=self.toggle_theme,
                    bootstyle="secondary-outline", padding=(12, 6))
        theme_btn.pack(side='left')
    
    def setup_notebook(self):
        """Setup tabbed interface with modern styling"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.colors['bg'], borderwidth=0, relief='flat')
        style.configure('TNotebook.Tab', padding=[25, 15], font=('Segoe UI', 11, 'bold'),
                       background=self.colors['card'], foreground=self.colors['text'],
                       borderwidth=2, relief='flat')
        accent_text = self.colors.get('button_text', '#F6F7FB')
        style.map('TNotebook.Tab', 
             background=[('selected', self.colors['primary']), ('active', self.colors['primary_hover'])],
             foreground=[('selected', accent_text), ('active', accent_text)],
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
        
        shadow = ttkb.Frame(parent, padding=2, bootstyle="dark")
        shadow.pack(**pack_opt)
        card = ttkb.Frame(shadow, padding=0, style='Glass.TFrame')
        card.pack(fill='both', expand=True)
        
        if title:
            header = ttkb.Frame(card, padding=(15, 8), bootstyle="primary")
            header.pack(fill='x')
            ttkb.Label(header, text=title, font=('Segoe UI', 12, 'bold'),
                       foreground=self.colors.get('button_text', '#F6F7FB')).pack(anchor='w')
        
        content = ttkb.Frame(card, padding=15, style='Glass.TFrame')
        content.pack(fill='both', expand=True)
        return content
    
    def create_button(self, parent, text, command, color='primary', **kw):
        """Create ttkbootstrap button with modern effects"""
        bootstyle = {
            'primary': 'primary-outline',
            'secondary': 'secondary-outline',
            'accent': 'danger-outline',
            'warning': 'warning-outline',
            'success': 'success-outline'
        }.get(color, 'primary-outline')
        btn = ttkb.Button(parent, text=text, command=command, bootstyle=bootstyle,
                          padding=(25, 12), cursor='hand2', **kw)
        btn.pack(side='left', padx=6, pady=4)
        return btn
    
    def create_toggle_button(self, parent, var, callback=None):
        """Create modern iOS-style toggle switch"""
        toggle_frame = tk.Frame(parent, bg=self.colors['card'], cursor='hand2')
        toggle_frame.pack(side='left')
        
        width, height = 72, 34
        padding = 4
        knob_width = 28
        off_x = padding
        on_x = width - padding - knob_width
        knob_colors = {
            'on': self.colors.get('knob_on', '#34D399'),
            'off': self.colors.get('knob_off', '#4B5563'),
            'core': self.colors.get('knob_core', '#C7D2FE')
        }
        
        canvas = tk.Canvas(toggle_frame, width=width, height=height,
                           bg=self.colors['card'], highlightthickness=0, cursor='hand2')
        canvas.pack()

        bg_rect = canvas.create_rectangle(padding, padding, width - padding, height - padding,
                                          fill=self.colors['input_border'], outline='', width=0)
        glow = canvas.create_oval(padding - 6, padding - 6, width - padding + 6, height - padding + 6,
                                  fill=self.colors.get('success', '#34D399'), outline='', state='hidden')
        knob = canvas.create_oval(off_x, padding, off_x + knob_width, height - padding,
                                  fill=knob_colors['core'], outline='' , width=0)
        knob_ring = canvas.create_oval(off_x + 2, padding + 2, off_x + knob_width - 2, height - padding - 2,
                           outline=self.colors.get('shadow', '#151823'), width=1, fill='')
        text_id = canvas.create_text(width // 2, height // 2, text="OFF",
                                     font=('Segoe UI', 8, 'bold'),
                                     fill=self.colors['text_secondary'])

        knob_state = {'x': off_x}

        def set_knob_position(x_val):
            canvas.coords(knob, x_val, padding, x_val + knob_width, height - padding)
            canvas.coords(knob_ring, x_val + 2, padding + 2, x_val + knob_width - 2, height - padding - 2)

        def animate_knob(target_x):
            start_x = knob_state['x']
            delta = target_x - start_x
            steps = 8
            if abs(delta) < 1:
                knob_state['x'] = target_x
                set_knob_position(target_x)
                return

            def _step(frame=1):
                if frame > steps:
                    knob_state['x'] = target_x
                    set_knob_position(target_x)
                    return
                new_x = start_x + (delta * frame / steps)
                knob_state['x'] = new_x
                set_knob_position(new_x)
                canvas.after(12, lambda: _step(frame + 1))

            _step()

        def update_toggle(animate=True):
            is_on = bool(var.get())
            bg_color = self.colors['success'] if is_on else self.colors['input_border']
            canvas.itemconfig(bg_rect, fill=bg_color)
            canvas.itemconfig(glow, state='normal' if is_on else 'hidden')
            canvas.itemconfig(knob, fill=knob_colors['core'])
            canvas.itemconfig(knob_ring, outline=knob_colors['on'] if is_on else knob_colors['off'])
            canvas.itemconfig(text_id, text="ON" if is_on else "OFF",
                             fill=self.colors.get('button_text', '#F6F7FB') if is_on else self.colors['text_secondary'])
            target = on_x if is_on else off_x
            if animate:
                animate_knob(target)
            else:
                knob_state['x'] = target
                set_knob_position(target)

        def toggle():
            var.set(not var.get())
            update_toggle()
            if callback:
                callback()

        canvas.bind('<Button-1>', lambda e: toggle())
        toggle_frame.bind('<Button-1>', lambda e: toggle())

        update_toggle(animate=False)
        return toggle_frame
    
    def on_auto_toggle(self, dec_entry):
        """Handle auto decimal toggle"""
        dec_entry.config(state='disabled' if self.auto_decimal_var.get() else 'normal')
    
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
        """Build setup tab with presets and validation"""
        sf = self.create_scrollable_frame(self.setup_tab)
        
        # Range card with presets
        range_card = self.create_card(sf, "📏 Number Range")
        range_grid = tk.Frame(range_card, bg=self.colors['card'])
        range_grid.pack(fill='x', pady=10)
        range_grid.columnconfigure(1, weight=1)
        
        tk.Label(range_grid, text="Start:", font=('Segoe UI', 11), bg=self.colors['card'], fg=self.colors['text']).grid(row=0, column=0, sticky='w', pady=5)
        self.start_var = tk.IntVar(value=-10)
        start_entry = tk.Entry(range_grid, textvariable=self.start_var, font=('Segoe UI', 11), bg=self.colors['input_bg'], fg=self.colors['text'], relief='solid', bd=1)
        start_entry.grid(row=0, column=1, sticky='ew', padx=5)
        
        tk.Label(range_grid, text="End:", font=('Segoe UI', 11), bg=self.colors['card'], fg=self.colors['text']).grid(row=1, column=0, sticky='w', pady=5)
        self.end_var = tk.IntVar(value=10)
        end_entry = tk.Entry(range_grid, textvariable=self.end_var, font=('Segoe UI', 11), bg=self.colors['input_bg'], fg=self.colors['text'], relief='solid', bd=1)
        end_entry.grid(row=1, column=1, sticky='ew', padx=5)
        
        # Presets
        preset_frame = tk.Frame(range_card, bg=self.colors['card'])
        preset_frame.pack(fill='x', pady=10)
        presets = [("0-10", 0, 10), ("-10 to 10", -10, 10), ("0-100", 0, 100), ("-100 to 100", -100, 100)]
        for text, start, end in presets:
            btn = self.create_button(preset_frame, text, lambda s=start, e=end: self.set_preset(s, e), 'secondary')
        
        # Population and generations
        param_card = self.create_card(sf, "🧬 Algorithm Parameters")
        param_grid = tk.Frame(param_card, bg=self.colors['card'])
        param_grid.pack(fill='x', pady=10)
        param_grid.columnconfigure(1, weight=1)
        
        tk.Label(param_grid, text="Population Size:", font=('Segoe UI', 11), bg=self.colors['card'], fg=self.colors['text']).grid(row=0, column=0, sticky='w', pady=5)
        self.pop_var = tk.IntVar(value=100)
        pop_entry = tk.Entry(param_grid, textvariable=self.pop_var, font=('Segoe UI', 11), bg=self.colors['input_bg'], fg=self.colors['text'], relief='solid', bd=1)
        pop_entry.grid(row=0, column=1, sticky='ew', padx=5)
        
        tk.Label(param_grid, text="Max Generations:", font=('Segoe UI', 11), bg=self.colors['card'], fg=self.colors['text']).grid(row=1, column=0, sticky='w', pady=5)
        self.gen_var = tk.IntVar(value=100)
        gen_entry = tk.Entry(param_grid, textvariable=self.gen_var, font=('Segoe UI', 11), bg=self.colors['input_bg'], fg=self.colors['text'], relief='solid', bd=1)
        gen_entry.grid(row=1, column=1, sticky='ew', padx=5)
        
        # Advanced options
        adv_card = self.create_card(sf, "⚙️ Advanced Options")
        adv_grid = tk.Frame(adv_card, bg=self.colors['card'])
        adv_grid.pack(fill='x', pady=10)
        adv_grid.columnconfigure(1, weight=1)
        
        row = 0
        tk.Label(adv_grid, text="Decimal Places:", font=('Segoe UI', 11), bg=self.colors['card'], fg=self.colors['text']).grid(row=row, column=0, sticky='w', pady=5)
        dec_entry = tk.Entry(adv_grid, textvariable=self.decimal_places_var, font=('Segoe UI', 11), bg=self.colors['input_bg'], fg=self.colors['text'], relief='solid', bd=1, state='disabled' if self.auto_decimal_var.get() else 'normal')
        dec_entry.grid(row=row, column=1, sticky='ew', padx=5)
        row += 1
        
        # Modern toggle switch for Auto Decimal
        toggle_frame = tk.Frame(adv_grid, bg=self.colors['card'])
        toggle_frame.grid(row=row, column=0, columnspan=2, sticky='w', pady=8)
        tk.Label(toggle_frame, text="Auto Decimal:", font=('Segoe UI', 11, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(side='left', padx=(0, 10))
        self.auto_toggle_btn = self.create_toggle_button(toggle_frame, self.auto_decimal_var, lambda: self.on_auto_toggle(dec_entry))
        row += 1
        
        # Modern toggle switch for Allow Negative Values
        neg_toggle_frame = tk.Frame(adv_grid, bg=self.colors['card'])
        neg_toggle_frame.grid(row=row, column=0, columnspan=2, sticky='w', pady=8)
        tk.Label(neg_toggle_frame, text="Allow Negative Values:", font=('Segoe UI', 11, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(side='left', padx=(0, 10))
        self.neg_toggle_btn = self.create_toggle_button(neg_toggle_frame, self.allow_negative_var, None)
        row += 1
        
        tk.Label(adv_grid, text="Space Operator:", font=('Segoe UI', 11), bg=self.colors['card'], fg=self.colors['text']).grid(row=row, column=0, sticky='w', pady=5)
        space_combo = ttk.Combobox(adv_grid, textvariable=self.space_operator_var, values=['auto', 'multiply', 'add', 'divide', 'subtract'], state='readonly')
        space_combo.grid(row=row, column=1, sticky='ew', padx=5)
        row += 1
        
        tk.Label(adv_grid, text="Hyphen Operator:", font=('Segoe UI', 11), bg=self.colors['card'], fg=self.colors['text']).grid(row=row, column=0, sticky='w', pady=5)
        hyphen_combo = ttk.Combobox(adv_grid, textvariable=self.hyphen_operator_var, values=['add', 'minus', 'multiply', 'divide'], state='readonly')
        hyphen_combo.grid(row=row, column=1, sticky='ew', padx=5)
        row += 1
        
        tk.Label(adv_grid, text="Evaluation Mode:", font=('Segoe UI', 11), bg=self.colors['card'], fg=self.colors['text']).grid(row=row, column=0, sticky='w', pady=5)
        mode_combo = ttk.Combobox(adv_grid, textvariable=self.evaluation_mode_var, values=['product', 'linear'], state='readonly')
        mode_combo.grid(row=row, column=1, sticky='ew', padx=5)
        row += 1
        
        tk.Label(adv_grid, text="CPU Usage:", font=('Segoe UI', 11), bg=self.colors['card'], fg=self.colors['text']).grid(row=row, column=0, sticky='w', pady=5)
        cpu_combo = ttk.Combobox(adv_grid, textvariable=self.cpu_usage_var, values=['auto', '50%', '75%', '100%'], state='readonly')
        cpu_combo.grid(row=row, column=1, sticky='ew', padx=5)
        
        # Start button
        btn_frame = tk.Frame(sf, bg=self.colors['bg'])
        btn_frame.pack(pady=20)
        self.start_button = self.create_button(btn_frame, "🚀 Start Optimization", self.start_optimization, 'primary')
    
    def set_preset(self, start, end):
        self.start_var.set(start)
        self.end_var.set(end)

    def start_optimization(self):
        """Validate and start optimization in background thread"""
        try:
            start = self.start_var.get()
            end = self.end_var.get()
            if start > end:
                raise ValueError("Start range must be less than or equal to end range")
            pop = self.pop_var.get()
            if pop < 10 or pop > 10000:
                raise ValueError("Population size must be between 10 and 10000")
            gens = self.gen_var.get()
            if gens < 10 or gens > 10000:
                raise ValueError("Max generations must be between 10 and 10000")
            if not self.auto_decimal_var.get():
                dec = int(self.decimal_places_var.get())
                if dec < 0 or dec > 20:
                    raise ValueError("Decimal places must be between 0 and 20")
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return
        
        self.is_solving = True
        self.notebook.tab(0, state='disabled')
        self.notebook.tab(1, state='normal')
        self.notebook.tab(2, state='disabled')
        self.notebook.select(1)
        self.progress_bar['value'] = 0
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, "🚀 Starting optimization...\n")
        self.log_text.insert(tk.END, f"📊 Range: {start} to {end} ({end-start+1} numbers)\n")
        self.log_text.insert(tk.END, f"👥 Population: {pop} | 🔄 Generations: {gens}\n")
        self.log_text.insert(tk.END, "=" * 60 + "\n")
        self.start_time = time.time()
        self.time_label = tk.Label(self.solving_tab, text="Time: 0s", font=('Segoe UI', 10), bg=self.colors['bg'], fg=self.colors['text_secondary'])
        self.time_label.pack(pady=5)
        
        threading.Thread(target=self.run_optimization, daemon=True).start()

    def run_optimization(self):
        try:
            self.optimizer = LetterValueOptimizer(
                self.start_var.get(), self.end_var.get(),
                population_size=self.pop_var.get(),
                decimal_places='auto' if self.auto_decimal_var.get() else self.decimal_places_var.get(),
                allow_negative_values=self.allow_negative_var.get(),
                space_operator=self.space_operator_var.get(),
                hyphen_operator=self.hyphen_operator_var.get(),
                cpu_usage=self.cpu_usage_var.get(),
                evaluation_mode=self.evaluation_mode_var.get()
            )
            
            def callback(stats):
                if stats is None:
                    return
                progress = (stats.get('generation', 0) / max(1, self.gen_var.get())) * 100
                # Force immediate UI update
                self.root.after(0, lambda s=stats, p=progress: self.update_progress(p, s))
                self.root.update_idletasks()
            
            self.best_solution = self.optimizer.optimize(max_generations=self.gen_var.get(), callback=callback)
            self.solution = self.optimizer.get_solution_details()
            self.root.after(0, self.finish_optimization)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, self.reset_to_setup)

    def update_progress(self, progress, stats):
        try:
            self.progress_bar['value'] = progress
            gen = stats.get('generation', 0)
            solved = stats.get('solved_count', 0)
            total = stats.get('total_numbers', 0)
            fitness = stats.get('best_fitness', 0.0)
            
            self.gen_label['text'] = f"{gen} / {self.gen_var.get()}"
            self.solved_label['text'] = f"{solved} / {total}"
            self.fitness_label['text'] = f"{fitness:.2f}"
            
            elapsed = 0
            if self.start_time is not None:
                elapsed = time.time() - self.start_time
            self.time_label['text'] = f"Time: {int(elapsed)}s"
            
            # Add progress log with color
            log_msg = f"⚡ Gen {gen}: Solved {solved}/{total} | Error {fitness:.2f}\n"
            self.log_text.insert(tk.END, log_msg)
            self.log_text.see(tk.END)
            
            # Force immediate refresh
            self.root.update()
        except Exception as e:
            self.logger.exception("Update progress failed")

    def finish_optimization(self):
        self.is_solving = False
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        # Add completion message
        self.log_text.insert(tk.END, "=" * 60 + "\n")
        self.log_text.insert(tk.END, f"✅ Optimization complete in {int(elapsed)}s!\n")
        if self.solution:
            solved = self.solution.get('solved_count', 0)
            total = self.solution.get('total_count', 0)
            self.log_text.insert(tk.END, f"🎯 Final: {solved}/{total} numbers solved\n")
        self.log_text.see(tk.END)
        
        self.notebook.tab(0, state='normal')
        self.notebook.tab(2, state='normal')
        self.notebook.select(2)
        self.display_results()
        if hasattr(self, 'time_label'):
            self.time_label.destroy()

    def stop_optimization(self):
        self.is_solving = False
        if getattr(self, 'optimizer', None) is not None:
            try:
                if hasattr(self.optimizer, 'is_solving'):
                    self.optimizer.is_solving = False  # type: ignore
            except Exception:
                pass
        self.log_text.insert(tk.END, "\n⏹️ Optimization stopped by user.\n")
        self.finish_optimization()

    def display_results(self):
        # Safe-guard when no solution available
        if not self.solution or not isinstance(self.solution, dict):
            self.results_summary['text'] = "No solution available"
            return

        # Update summary
        self.results_summary['text'] = f"Solved {self.solution.get('solved_count',0)} / {self.solution.get('total_count',0)} numbers | Total Error: {self.solution.get('total_error',0.0):.4f}"

        # Update letter values (create labels if missing)
        if not hasattr(self, 'letter_labels') or not self.letter_labels:
            # create minimal letters panel
            letters_frame = getattr(self, 'letters_frame', None)
            if letters_frame is None:
                letters_frame = tk.Frame(self.results_tab, bg=self.colors['bg'])
                letters_frame.pack(side='left', fill='y', padx=10, pady=10)
                self.letters_frame = letters_frame
            self.letter_labels = {}
            for i, ch in enumerate(string.ascii_uppercase):
                lbl = tk.Label(letters_frame, text=f"{ch}: --", font=('Segoe UI', 10), bg=self.colors['card'], fg=self.colors['text'])
                lbl.grid(row=i//6, column=i%6, sticky='w', padx=6, pady=2)
                self.letter_labels[ch] = lbl

        letter_values = self.solution.get('letter_values', {})
        for ch, lbl in self.letter_labels.items():
            value = letter_values.get(ch, 0.0)
            try:
                lbl['text'] = f"{ch}: {value:.4f}"
            except Exception:
                pass

        # Update treeview
        if hasattr(self, 'results_tree'):
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            for result in self.solution.get('results', []):
                status = "Solved" if result.get('is_solved') else "Unsolved"
                num = result.get('number', '')
                spelling = result.get('spelling', '')
                sv = result.get('spelled_value', 0.0)
                err = result.get('error', 0.0)
                self.results_tree.insert('', 'end', values=(num, spelling, f"{sv:.4f}", f"{err:.6f}", status))

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
    
    def calculate_explorer(self):
        try:
            if not hasattr(self, 'explorer_input'):
                messagebox.showerror("Error", "Explorer not initialized")
                return
                
            num = int(self.explorer_input.get())
            spelling = number_to_words(num)

            decimals = 'auto' if self.auto_decimal_var.get() else int(self.decimal_places_var.get())
            if decimals == 'auto':
                decimals = 4  # default

            letter_values = {}
            if self.solution and isinstance(self.solution, dict):
                letter_values = self.solution.get('letter_values', {})
            
            if not letter_values:
                letter_values = {chr(65 + i): 1.0 for i in range(26)}

            # Use proper SpellingParser signature
            parser = SpellingParser(letter_values, self.space_operator_var.get(), self.hyphen_operator_var.get(), decimals)
            value, exp = parser.calculate_spelled_value(spelling)

            error = (value - num) ** 2
            
            # ensure explorer_text exists
            if not hasattr(self, 'explorer_text'):
                self.explorer_text = ScrolledText(self.results_tab, font=('Consolas', 10), bg=self.colors['console_bg'], fg=self.colors['console_text'], height=6)
                self.explorer_text.pack(fill='both', expand=True, pady=(0,10))

            self.explorer_text.delete(1.0, tk.END)
            self.explorer_text.insert(tk.END, f"✓ Number: {num}\n✓ Spelling: {spelling}\n✓ Calculated: {value:.4f}\n✓ Error: {error:.6f}\n\n📝 Calculation:\n{exp}")
        except ValueError:
            messagebox.showerror("Invalid", "Enter a valid integer")
        except Exception as e:
            self.logger.exception("Explorer calculation failed")
            messagebox.showerror("Error", str(e))

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

    def view_error_log(self):
        """Open and display error.log contents"""
        log_path = os.path.join(os.getcwd(), 'error.log')
        win = tk.Toplevel(self.root)
        win.title('error.log')
        win.geometry('700x500')
        win.configure(bg=self.colors['bg'])
        txt = ScrolledText(win, font=('Consolas', 10), bg=self.colors['console_bg'], fg=self.colors['console_text'])
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
    
    def reset_to_setup(self):
        self.is_solving = False
        self.notebook.tab(0, state='normal')
        self.notebook.tab(1, state='disabled')
        self.notebook.tab(2, state='disabled')
        self.notebook.select(0)

    def build_solving_tab(self):
        """Build solving tab with stats and log"""
        sf = self.create_scrollable_frame(self.solving_tab)
        
        # Stats grid
        stats_grid = tk.Frame(sf, bg=self.colors['bg'])
        stats_grid.pack(fill='x', pady=10)
        stats_grid.grid_columnconfigure(0, weight=1)
        stats_grid.grid_columnconfigure(1, weight=1)
        stats_grid.grid_columnconfigure(2, weight=1)
        
        # Generation stat
        gen_stat = tk.Frame(stats_grid, bg=self.colors['stat_green_bg'],
                           highlightbackground=self.colors['card_border'], highlightthickness=1)
        gen_stat.grid(row=0, column=0, padx=8, pady=5, sticky='ew')
        tk.Label(gen_stat, text="Generation", font=('Segoe UI', 10),
                bg=self.colors['stat_green_bg'], fg=self.colors['stat_green_text']).pack(pady=(10, 2))
        self.gen_label = tk.Label(gen_stat, text="0 / 0", font=('Segoe UI', 20, 'bold'),
                                 bg=self.colors['stat_green_bg'], fg=self.colors['stat_green_text'])
        self.gen_label.pack(pady=(2, 10))
        
        # Solved stat
        solved_stat = tk.Frame(stats_grid, bg=self.colors['stat_blue_bg'],
                              highlightbackground=self.colors['card_border'], highlightthickness=1)
        solved_stat.grid(row=0, column=1, padx=8, pady=5, sticky='ew')
        tk.Label(solved_stat, text="Numbers Solved", font=('Segoe UI', 10),
                bg=self.colors['stat_blue_bg'], fg=self.colors['stat_blue_text']).pack(pady=(10, 2))
        self.solved_label = tk.Label(solved_stat, text="0 / 0", font=('Segoe UI', 20, 'bold'),
                                     bg=self.colors['stat_blue_bg'], fg=self.colors['stat_blue_text'])
        self.solved_label.pack(pady=(2, 10))
        
        # Fitness stat
        fitness_stat = tk.Frame(stats_grid, bg=self.colors['stat_orange_bg'],
                               highlightbackground=self.colors['card_border'], highlightthickness=1)
        fitness_stat.grid(row=0, column=2, padx=8, pady=5, sticky='ew')
        tk.Label(fitness_stat, text="Total Error", font=('Segoe UI', 10),
                bg=self.colors['stat_orange_bg'], fg=self.colors['stat_orange_text']).pack(pady=(10, 2))
        self.fitness_label = tk.Label(fitness_stat, text="N/A", font=('Segoe UI', 20, 'bold'),
                                      bg=self.colors['stat_orange_bg'], fg=self.colors['stat_orange_text'])
        self.fitness_label.pack(pady=(2, 10))
        
        # Progress bar
        prog_cont = tk.Frame(sf, bg=self.colors['card'])
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
        log_frame = tk.LabelFrame(sf, text="📜 Console Log",
                                 font=('Segoe UI', 11, 'bold'),
                                 bg=self.colors['card'], fg=self.colors['text'],
                                 bd=1, relief='solid')
        log_frame.pack(fill='both', expand=True, pady=15)
        
        self.log_text = ScrolledText(log_frame, font=('Consolas', 9),
                              bg=self.colors['console_bg'],
                              fg=self.colors['console_text'],
                              insertbackground=self.colors['console_text'],
                              relief='flat')
        self.log_text.pack(fill='both', expand=True, padx=8, pady=8)
        
        # Add startup message
        self.log_text.insert(tk.END, "🚀 Ready to optimize! Click 'Start Optimization' in Setup tab.\n")
        self.log_text.insert(tk.END, "=" * 60 + "\n")
        
        # View Error Log button
        log_btn_frame = tk.Frame(log_frame, bg=self.colors['card'])
        log_btn_frame.pack(fill='x', padx=8, pady=(0,8))
        view_log_btn = self.create_button(log_btn_frame, "🪵 View error.log", self.view_error_log, 'warning')
        
        # Stop button
        bf = tk.Frame(sf, bg=self.colors['bg'])
        bf.pack(pady=15)
        self.stop_button = self.create_button(bf, "⏹️ Stop Optimization",
                                             self.stop_optimization, 'accent')

    def build_results_tab(self):
        """Create the results UI (letters panel, results table, explanation & explorer)"""
        rt = self.results_tab
        sf = self.create_scrollable_frame(rt)

        # Summary
        summ_card = self.create_card(sf, "📈 Summary")
        self.results_summary = tk.Label(summ_card, text="No results yet", font=('Segoe UI', 11), bg=self.colors['card'], fg=self.colors['text'])
        self.results_summary.pack(anchor='w')

        # Letters values panel
        letters_card = self.create_card(sf, "🔤 Letter Values")
        letters_frame = tk.Frame(letters_card, bg=self.colors['card'])
        letters_frame.pack(fill='x')
        self.letters_frame = letters_frame
        self.letter_labels = {}
        for i, ch in enumerate(string.ascii_uppercase):
            lbl = tk.Label(letters_frame, text=f"{ch}: --", font=('Segoe UI', 10), bg=self.colors['card'], fg=self.colors['text'])
            lbl.grid(row=i//6, column=i%6, sticky='w', padx=6, pady=2)
            self.letter_labels[ch] = lbl

        # Results table
        table_card = self.create_card(sf, "📋 Detailed Results")
        cols = ('number', 'spelling', 'value', 'error', 'status')
        self.results_tree = ttk.Treeview(table_card, columns=cols, show='headings', height=12)
        for c, title in zip(cols, ("Number", "Spelling", "Calculated", "Error", "Status")):
            self.results_tree.heading(c, text=title)
            self.results_tree.column(c, width=120, anchor='w')
        vsb = ttk.Scrollbar(table_card, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=vsb.set)
        self.results_tree.pack(side='left', fill='both', expand=True, padx=(0,8))
        vsb.pack(side='right', fill='y')
        self.results_tree.bind('<<TreeviewSelect>>', self.on_result_select)

        # Explanation & Explorer
        expl_card = self.create_card(sf, "🧾 Explanation & Explorer")
        expl_top = tk.Frame(expl_card, bg=self.colors['card'])
        expl_top.pack(fill='x')
        explorer_lbl = tk.Label(expl_top, text="Enter number:", bg=self.colors['card'], fg=self.colors['text'])
        explorer_lbl.pack(side='left')
        self.explorer_input = tk.Entry(expl_top, font=('Segoe UI', 11), bg=self.colors['input_bg'], fg=self.colors['text'])
        self.explorer_input.pack(side='left', padx=8)
        exp_btn = self.create_button(expl_top, "Calculate", self.calculate_explorer, 'secondary')
        self.explanation_text = ScrolledText(expl_card, font=('Consolas', 10), bg=self.colors['console_bg'], fg=self.colors['console_text'], height=10)
        self.explanation_text.pack(fill='both', expand=True, pady=8)

        # Explorer result area
        self.explorer_text = ScrolledText(expl_card, font=('Consolas', 10), bg=self.colors['console_bg'], fg=self.colors['console_text'], height=6)
        self.explorer_text.pack(fill='both', expand=True, pady=(0,10))

def main():
    root = tk.Tk()
    app = ModernSpellingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()