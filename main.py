# === IMPORTS ===
#
# --- Standard Library ---
import os
import time
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --- Third-Party Libraries ---
import docx
import pdfplumber
import matplotlib.ticker as mticker
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sv_ttk  # Import the theme

# === ALGORITHM IMPLEMENTATIONS ===
# (No changes in this section)
def _is_word_boundary(text, start, end):
    before = text[start - 1] if start > 0 else " "
    after = text[end] if end < len(text) else " "
    return (not before.isalnum()) and (not after.isalnum())
def brute_force_search(text, pattern):
    n = len(text); m = len(pattern)
    if m == 0: return 0, 0
    if n < m: return 0, 0
    comparisons = 0; found_count = 0
    for i in range(n - m + 1):
        j = 0
        while j < m:
            comparisons += 1
            if text[i + j] != pattern[j]: break
            j += 1
        if j == m and _is_word_boundary(text, i, i + m):
            found_count += 1
    return found_count, comparisons
def rabin_karp_search(text, pattern):
    n = len(text); m = len(pattern)
    if m == 0: return 0, 0
    if n < m: return 0, 0
    comparisons = 0; found_count = 0
    base = 256; mod = 2305843009213693951  
    pat_hash = 0; win_hash = 0
    for i in range(m):
        pat_hash = (pat_hash * base + ord(pattern[i])) % mod
        win_hash = (win_hash * base + ord(text[i])) % mod
    power = pow(base, m - 1, mod)
    if pat_hash == win_hash:
        match = True
        for j in range(m):
            comparisons += 1
            if text[j] != pattern[j]: match = False; break
        if match and _is_word_boundary(text, 0, m):
            found_count += 1
    for i in range(1, n - m + 1):
        lead_char_val = ord(text[i - 1])
        new_char_val = ord(text[i + m - 1])
        win_hash = (win_hash - (lead_char_val * power) % mod + mod) % mod
        win_hash = (win_hash * base) % mod
        win_hash = (win_hash + new_char_val) % mod
        if win_hash == pat_hash:
            match = True
            for j in range(m):
                comparisons += 1
                if text[i + j] != pattern[j]: match = False; break
            if match and _is_word_boundary(text, i, i + m):
                found_count += 1
    return found_count, comparisons
def kmp_search(text, pattern):
    n = len(text); m = len(pattern)
    if m == 0: return 0, 0
    if n < m: return 0, 0
    lps = [0] * m; length = 0; i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1; lps[i] = length; i += 1
        else:
            if length != 0: length = lps[length - 1]
            else: lps[i] = 0; i += 1
    comparisons = 0; found_count = 0; i = 0; j = 0
    while i < n:
        comparisons += 1
        if text[i] == pattern[j]:
            i += 1; j += 1
            if j == m:
                if _is_word_boundary(text, i - j, i):
                    found_count += 1
                j = lps[j - 1]
        else:
            if j != 0: j = lps[j - 1]
            else: i += 1
    return found_count, comparisons

# === FILE EXTRACTION UTILITIES ===
# (No changes in this section)
def extract_text_from_pdf(pdf_file_path):
    text = ""
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text: text += page_text + "\n"
        return text
    except Exception as e:
        print(f"PDF Error: {e}"); return None 
def extract_text_from_docx(docx_file_path):
    text = ""
    try:
        doc = docx.Document(docx_file_path)
        for para in doc.paragraphs: text += para.text + "\n"
        return text
    except Exception as e:
        print(f"DOCX Error: {e}"); return None

# === MAIN APPLICATION CLASS ===

class CVAnalyzerApp:
    
    ALGORITHMS = {
        "Brute Force": brute_force_search,
        "Rabin-Karp": rabin_karp_search,
        "Knuth-Morris-Pratt (KMP)": kmp_search
    }
    
    # Weights for weighted scoring
    MANDATORY_WEIGHT = 0.70  # 70%
    PREFERRED_WEIGHT = 0.30  # 30%

    def __init__(self, root):
        """Constructor for the main application."""
        self.root = root
        self.root.title("Intelligent CV Analyzer")
        self.root.geometry("1100x750")

        # --- Application State Variables ---
        self.cv_filepath = ""
        self.cv_text_content = ""
        self.performance_data = []
        self.batch_results_data = []
        
        self.mandatory_keywords = set()
        self.preferred_keywords = set()
        self.all_keywords_list = []
        
        self.batch_queue = queue.Queue()
        self.batch_thread = None

        self.penalty_var = tk.DoubleVar(value=20.0) # Default 20% penalty

        # --- Main Layout ---
        self.main_paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_paned_window.pack(fill=tk.BOTH, expand=True)

        self.input_frame = ttk.Frame(self.main_paned_window, width=350, relief=tk.RIDGE)
        self.input_frame.pack_propagate(False) 
        self.main_paned_window.add(self.input_frame, weight=1)

        self.output_frame = ttk.Frame(self.main_paned_window, width=750)
        self.main_paned_window.add(self.output_frame, weight=3)

        # --- Output Tabs (Order changed) ---
        self.notebook = ttk.Notebook(self.output_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab_results = ttk.Frame(self.notebook)
        self.tab_batch_results = ttk.Frame(self.notebook)
        self.tab_performance_table = ttk.Frame(self.notebook)
        self.tab_performance_chart = ttk.Frame(self.notebook)
        self.tab_cv_text = ttk.Frame(self.notebook)
        self.tab_about = ttk.Frame(self.notebook) 

        self.notebook.add(self.tab_results, text="Keyword Results")
        self.notebook.add(self.tab_batch_results, text="Batch Results")
        self.notebook.add(self.tab_performance_table, text="Performance Table")
        self.notebook.add(self.tab_performance_chart, text="Performance Chart")
        self.notebook.add(self.tab_cv_text, text="Extracted CV Text")
        self.notebook.add(self.tab_about, text="About")

        # --- Build Widgets ---
        self.create_input_widgets()
        self.create_results_tab_widgets()
        self.create_batch_results_tab_widgets()
        self.create_performance_table_tab_widgets()
        self.create_performance_chart_tab_widgets()
        self.create_cv_text_tab_widgets()
        self.create_about_tab_widgets()
        
        self.input_frame.grid_rowconfigure(3, weight=0) # Make options frame static
        self.input_frame.grid_rowconfigure(4, weight=1) # Make action frame container expand
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        # --- Status Bar ---
        self.status_bar_frame = ttk.Frame(root, relief=tk.SUNKEN, padding="2 5")
        self.status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = ttk.Label(self.status_bar_frame, text="Ready.")
        self.status_label.pack(side=tk.LEFT)
        
        self.check_batch_queue()
        
    # --- GUI Widget Builders ---
    
    def create_input_widgets(self):
        """Populates the left-hand input frame with all controls."""
        self.input_frame.grid_propagate(False)

        # Group 1: Job Selection
        job_frame = ttk.LabelFrame(self.input_frame, text="1. Job Position")
        job_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")
        job_frame.grid_columnconfigure(0, weight=1)

        self.job_options = [
            "Senior AI/ML Engineer (Agentic AI)", "Computer Vision Engineer", "Data Scientist"
        ]
        self.selected_job = tk.StringVar()
        self.job_dropdown = ttk.Combobox(
            job_frame, textvariable=self.selected_job, values=self.job_options, state="readonly"
        )
        self.job_dropdown.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.job_dropdown.bind("<<ComboboxSelected>>", self.load_job_keywords)
        
        # Group 2: Keywords
        keywords_frame = ttk.LabelFrame(self.input_frame, text="2. Job Keywords (auto-loaded)")
        keywords_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        keywords_frame.grid_rowconfigure(0, weight=1)
        keywords_frame.grid_columnconfigure(0, weight=1)
        keywords_frame.config(height=200) 
        
        self.keywords_text = tk.Text(keywords_frame, height=10, width=35, state=tk.DISABLED, wrap=tk.WORD, 
                                     font=('TkDefaultFont', 9))
        self.keywords_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Group 3: CV Upload
        cv_frame = ttk.LabelFrame(self.input_frame, text="3. CV")
        cv_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        cv_frame.grid_columnconfigure(0, weight=1)
        
        self.load_cv_button = ttk.Button(cv_frame, text="Load CV File", command=self.load_cv)
        self.load_cv_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.cv_filename_label = ttk.Label(cv_frame, text="No file loaded.", wraplength=300)
        self.cv_filename_label.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")
        
        # Group 4: Scoring Options
        options_frame = ttk.LabelFrame(self.input_frame, text="4. Scoring Options")
        options_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        options_frame.grid_columnconfigure(0, weight=1)

        self.penalty_label = ttk.Label(options_frame, text="Mandatory Skill Penalty: 20.0%")
        self.penalty_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.penalty_slider = ttk.Scale(
            options_frame,
            from_=0.0,
            to=100.0,
            orient=tk.HORIZONTAL,
            variable=self.penalty_var,
            command=self.update_penalty_label # Update label on slide
        )
        self.penalty_slider.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        # Group 5: Actions
        action_frame = ttk.Frame(self.input_frame)
        action_frame.grid(row=4, column=0, padx=10, pady=(20, 10), sticky="sew")
        action_frame.grid_columnconfigure(0, weight=1)

        self.analyze_button = ttk.Button(
            action_frame, text="Analyze CV", command=self.run_analysis, style="Accent.TButton"
        )
        self.analyze_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.batch_button = ttk.Button(
            action_frame,
            text="Run Batch Analysis",
            command=self.start_batch_analysis_thread
        )
        self.batch_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    def update_penalty_label(self, value):
        """Callback to update the penalty label as the slider moves."""
        self.penalty_label.config(text=f"Mandatory Skill Penalty: {float(value):.1f}%")

    def create_results_tab_widgets(self):
        """Populates the 'Keyword Results' tab."""
        top_frame = ttk.Frame(self.tab_results)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        self.score_label = ttk.Label(
            top_frame, text="Relevance Score: --%", font=('TkDefaultFont', 14, 'bold')
        )
        self.score_label.pack(side=tk.LEFT, padx=10)

        self.export_button = ttk.Button(
            top_frame,
            text="Export Report (.txt)",
            command=self.export_single_report,
            state=tk.DISABLED
        )
        self.export_button.pack(side=tk.RIGHT, padx=10)

        lists_frame = ttk.Frame(self.tab_results)
        lists_frame.pack(fill="both", expand=True, padx=10, pady=10)
        lists_frame.grid_columnconfigure(0, weight=1)
        lists_frame.grid_columnconfigure(1, weight=1)
        lists_frame.grid_rowconfigure(1, weight=1)
        
        ttk.Label(lists_frame, text="✅ Matched Keywords", font=('TkDefaultFont', 12, 'bold')).grid(
            row=0, column=0, pady=5)
        self.matched_list = tk.Listbox(lists_frame, background="#e0ffe0", foreground="#006400")
        self.matched_list.grid(row=1, column=0, sticky="nsew", padx=5)
        
        ttk.Label(lists_frame, text="❌ Missing Keywords", font=('TkDefaultFont', 12, 'bold')).grid(
            row=0, column=1, pady=5)
        self.missing_list = tk.Listbox(lists_frame, background="#ffe0e0", foreground="#a00000")
        self.missing_list.grid(row=1, column=1, sticky="nsew", padx=5)

    def create_batch_results_tab_widgets(self):
        """Populates the 'Batch Results' tab with a sortable Treeview."""
        info_label = ttk.Label(self.tab_batch_results, 
                               text="Ranked list of all CVs from 'data/cvs' folder. Click headers to sort.",
                               font=('TkDefaultFont', 9, 'italic'))
        info_label.pack(side=tk.TOP, fill="x", padx=10, pady=(10, 5))
        self.batch_table = ttk.Treeview(
            self.tab_batch_results, columns=("CV Name", "Score"), show="headings"
        )
        self.batch_table.heading("CV Name", text="CV Name", 
                                 command=lambda: self.sort_treeview_column(self.batch_table, "CV Name", False))
        self.batch_table.heading("Score", text="Relevance Score (%)", 
                                 command=lambda: self.sort_treeview_column(self.batch_table, "Score", True))
        self.batch_table.column("CV Name", width=400)
        self.batch_table.column("Score", width=150, anchor=tk.E)
        self.batch_table.pack(fill="both", expand=True, padx=10, pady=(5, 10))

    def create_performance_table_tab_widgets(self):
        """Populates the 'Performance Table' tab with a Treeview."""
        self.perf_table = ttk.Treeview(
            self.tab_performance_table, columns=("Algorithm", "Time", "Comparisons"), show="headings"
        )
        self.perf_table.heading("Algorithm", text="Algorithm")
        self.perf_table.heading("Time", text="Execution Time (ms)")
        self.perf_table.heading("Comparisons", text="Total Comparisons")
        self.perf_table.column("Algorithm", width=200)
        self.perf_table.column("Time", width=150, anchor=tk.E)
        self.perf_table.column("Comparisons", width=150, anchor=tk.E)
        self.perf_table.pack(fill="both", expand=True, padx=10, pady=10)

    def create_performance_chart_tab_widgets(self):
        """Populates the 'Performance Chart' tab with a Matplotlib canvas."""
        self.chart_frame = ttk.Frame(self.tab_performance_chart)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax1 = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ax1.set_title("Performance Comparison")
        self.ax1.set_ylabel("Execution Time (ms)")
        self.fig.tight_layout()

    def create_cv_text_tab_widgets(self):
        """Populates the 'Extracted CV Text' tab with a scrollable Text widget."""
        # --- FIX: Manually set theme colors for tk.Text ---
        style = ttk.Style()
        bg_color = style.lookup('TFrame', 'background')
        fg_color = style.lookup('TLabel', 'foreground')

        self.cv_text_widget = tk.Text(
            self.tab_cv_text, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            bg=bg_color,
            fg=fg_color,
            relief=tk.FLAT
        )
        # --- END FIX ---
        
        self.cv_text_scrollbar = ttk.Scrollbar(
            self.tab_cv_text, orient=tk.VERTICAL, command=self.cv_text_widget.yview
        )
        self.cv_text_widget.configure(yscrollcommand=self.cv_text_scrollbar.set)
        self.cv_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cv_text_widget.pack(fill="both", expand=True, padx=5, pady=5)

    # --- UPDATED: create_about_tab_widgets (FIXED) ---
    def create_about_tab_widgets(self):
        """Populates the 'About' tab with help text."""
        about_text_content = f"""
        Intelligent CV Analyzer (v2.1)
        ----------------------------------

        This application analyzes CVs against job descriptions using three string-matching algorithms.

        ALGORITHMS:
        1.  Brute Force: A straightforward algorithm that checks the pattern against every possible position in the text.
        2.  Rabin-Karp: Uses a 'rolling hash' to quickly find potential matches, then verifies them.
        3.  Knuth-Morris-Pratt (KMP): Uses a pre-computed 'LPS' array to skip sections of the text intelligently.

        SCORING:
        The "Relevance Score" is a weighted average based on the keywords found:
        -   Mandatory Skills: {self.MANDATORY_WEIGHT * 100:.0f}% of the total score
        -   Preferred Skills: {self.PREFERRED_WEIGHT * 100:.0f}% of the total score

        -   PENALTY: If any *mandatory* skill is missing, the final score is penalized.
        -   You can control this penalty using the "Scoring Options" slider.
        -   (e.g., A 20% penalty means the final score is multiplied by 0.80).

        SEARCH:
        -   Search is always case-insensitive.

        FILE LOCATIONS:
        -   Job Descriptions: Loaded from `data/job_descriptions/*.json`
        -   Batch CVs: Loaded from `data/cvs/`
        -   Batch Report: Saved to `data/cv_batch_report.json`
        """
        
        text_frame = ttk.Frame(self.tab_about, padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # --- FIX: Get theme-aware colors ---
        # The tk.Text widget doesn't auto-style, so we must set its
        # background and foreground manually by querying the theme.
        style = ttk.Style()
        # Get the background color of a standard TFrame
        bg_color = style.lookup('TFrame', 'background')
        # Get the foreground (text) color of a standard TLabel
        fg_color = style.lookup('TLabel', 'foreground')

        about_text = tk.Text(
            text_frame, 
            wrap=tk.WORD, 
            state=tk.NORMAL, 
            bg=bg_color,       # <--- CHANGED: Use theme background
            fg=fg_color,       # <--- NEW: Use theme foreground
            relief=tk.FLAT,    # Remove border
            font=('TkDefaultFont', 10),
            padx=5,            # Add a little internal padding
            insertbackground=fg_color # Make the cursor visible if enabled
        )
        # --- END FIX ---
        
        about_text.insert("1.0", about_text_content)
        about_text.config(state=tk.DISABLED) # Make read-only
        
        about_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=about_text.yview)
        about_text.configure(yscrollcommand=about_scrollbar.set)
        
        about_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        about_text.pack(fill="both", expand=True, padx=5, pady=5)

    # --- Core Logic & Event Handlers ---
    
    def load_job_keywords(self, event=None):
        """Loads keywords from JSON into the text box AND instance variables."""
        selected_job_title = self.selected_job.get()
        if not selected_job_title: return
        filename_map = {
            "Senior AI/ML Engineer (Agentic AI)": "agentic_ai_engineer.json",
            "Computer Vision Engineer": "computer_vision_engineer.json",
            "Data Scientist": "data_scientist.json"
        }
        if selected_job_title not in filename_map:
            messagebox.showerror("Error", "Invalid job selection.")
            return
        file_path = os.path.join("data", "job_descriptions", filename_map[selected_job_title])
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"Job description file not found:\n{file_path}")
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f: data = json.load(f)

            self.mandatory_keywords = set(data.get("required_skills", []))
            self.preferred_keywords = set(data.get("preferred_skills", []))
            tools = set(data.get("tools_and_frameworks", []))
            all_keywords_set = self.mandatory_keywords | self.preferred_keywords | tools
            self.all_keywords_list = sorted(list(all_keywords_set))

            if not self.all_keywords_list:
                messagebox.showwarning("Warning", f"No keywords found in '{file_path}'.")
                return

            self.keywords_text.config(state=tk.NORMAL)
            self.keywords_text.delete("1.0", tk.END)
            
            self.keywords_text.insert(tk.END, "# --- MANDATORY SKILLS ---\n")
            for kw in sorted(list(self.mandatory_keywords)):
                self.keywords_text.insert(tk.END, kw + "\n")
            
            self.keywords_text.insert(tk.END, "\n# --- PREFERRED SKILLS ---\n")
            for kw in sorted(list(self.preferred_keywords - self.mandatory_keywords)):
                self.keywords_text.insert(tk.END, kw + "\n")

            other_tools = tools - self.mandatory_keywords - self.preferred_keywords
            if other_tools:
                self.keywords_text.insert(tk.END, "\n# --- OTHER TOOLS ---\n")
                for kw in sorted(list(other_tools)):
                    self.keywords_text.insert(tk.END, kw + "\n")
            self.keywords_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load job description from JSON:\n{e}")

    def load_cv(self):
        """Event handler for the 'Load CV File' button."""
        filepath = filedialog.askopenfilename(
            title="Select CV File",
            filetypes=(("PDF Files", "*.pdf"), ("Word Documents", "*.docx"), ("All Files", "*.*"))
        )
        if not filepath: return
        self.cv_filepath = filepath
        filename = os.path.basename(filepath)
        self.cv_filename_label.config(text=f"Loaded: {filename}")
        self.cv_text_content = ""
        if filepath.endswith(".pdf"): self.cv_text_content = extract_text_from_pdf(filepath)
        elif filepath.endswith(".docx"): self.cv_text_content = extract_text_from_docx(filepath)
        else: messagebox.showwarning("Warning", "Unknown file type."); return
            
        if self.cv_text_content:
            self.cv_text_widget.config(state=tk.NORMAL)
            self.cv_text_widget.delete("1.0", tk.END)
            self.cv_text_widget.insert("1.0", self.cv_text_content)
            self.cv_text_widget.config(state=tk.DISABLED)
            self.export_button.config(state=tk.DISABLED)
        else:
            self.cv_filename_label.config(text="Failed to read text from file.")

    def run_analysis(self):
        """Event handler for the 'Analyze CV' button. (Runs on main thread)"""
        self.status_label.config(text="Analyzing...")
        self.root.update_idletasks()
        
        if not self.selected_job.get() or not self.all_keywords_list:
            messagebox.showerror("Error", "Please select a job position first.")
            self.status_label.config(text="Error. Ready.")
            return
        if not self.cv_filepath:
            messagebox.showerror("Error", "Please load a CV file first.")
            self.status_label.config(text="Error. Ready.")
            return
        if not self.cv_text_content:
            messagebox.showerror("Error", "Could not read text from CV.")
            self.status_label.config(text="Error. Ready.")
            return

        self.performance_data.clear()
        cv_text_to_search = self.cv_text_content.lower()
        
        final_score = 0.0
        
        for algo_name, algo_func in self.ALGORITHMS.items():
            matched_keywords_list = []
            missing_keywords_list = []
            matched_mandatory = 0
            matched_preferred = 0
            total_comparisons = 0
            start_time = time.perf_counter()
            
            for keyword in self.all_keywords_list:
                keyword_to_find = keyword.lower()
                found_count, comparisons = algo_func(cv_text_to_search, keyword_to_find)
                total_comparisons += comparisons
                
                if found_count > 0:
                    matched_keywords_list.append(keyword)
                    if keyword in self.mandatory_keywords: matched_mandatory += 1
                    elif keyword in self.preferred_keywords: matched_preferred += 1
                else:
                    missing_keywords_list.append(keyword)
            
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000
            
            # --- UPDATED: Weighted Scoring Logic with Penalty Slider ---
            score_mand = 100.0
            if self.mandatory_keywords:
                score_mand = (matched_mandatory / len(self.mandatory_keywords)) * 100
            score_pref = 100.0
            if self.preferred_keywords:
                score_pref = (matched_preferred / len(self.preferred_keywords)) * 100

            weighted_score = (score_mand * self.MANDATORY_WEIGHT) + (score_pref * self.PREFERRED_WEIGHT)

            if matched_mandatory < len(self.mandatory_keywords):
                penalty_percent = self.penalty_var.get()
                penalty_multiplier = 1.0 - (penalty_percent / 100.0)
                weighted_score *= penalty_multiplier
            
            final_score = weighted_score
            
            self.performance_data.append({
                "name": algo_name, "time": execution_time_ms, "comparisons": total_comparisons,
                "score": final_score, "matched": matched_keywords_list, "missing": missing_keywords_list
            })

        if not self.performance_data:
            messagebox.showinfo("Info", "Analysis complete, but no data was generated.")
            self.status_label.config(text="Ready.")
            return

        self.score_label.config(text=f"Relevance Score: {final_score:.2f}%")
        first_result = self.performance_data[0]
        self.matched_list.delete(0, tk.END)
        for item in first_result['matched']: self.matched_list.insert(tk.END, item)
        self.missing_list.delete(0, tk.END)
        for item in first_result['missing']: self.missing_list.insert(tk.END, item)
        self.update_performance_table()
        self.update_performance_chart()
        self.notebook.select(self.tab_results)
        self.export_button.config(state=tk.NORMAL)
        self.status_label.config(text="Analysis complete. Ready.")
        
    # --- THREADING FUNCTIONS ---
    
    def start_batch_analysis_thread(self):
        """Validates inputs and starts the batch analysis worker thread."""
        if self.batch_thread and self.batch_thread.is_alive():
            messagebox.showwarning("In Progress", "Batch analysis is already running.")
            return

        if not self.selected_job.get() or not self.all_keywords_list:
            messagebox.showerror("Error", "Please select a job position first.")
            return
            
        penalty_value = self.penalty_var.get()

        self.status_label.config(text="Running batch analysis... This may take a while.")
        self.batch_button.config(state=tk.DISABLED)
        self.analyze_button.config(state=tk.DISABLED)

        self.batch_thread = threading.Thread(
            target=self.run_batch_analysis_worker, 
            args=(
                self.mandatory_keywords.copy(), 
                self.preferred_keywords.copy(), 
                self.all_keywords_list.copy(),
                penalty_value
            ),
            daemon=True
        )
        self.batch_thread.start()

    def run_batch_analysis_worker(self, mandatory_keywords, preferred_keywords, all_keywords, penalty_value):
        """This is the main batch logic. Runs on a WORKER thread."""
        try:
            cvs_dir = os.path.join("data", "cvs")
            if not os.path.exists(cvs_dir):
                raise FileNotFoundError(f"CVs folder not found: {cvs_dir}")
            files = [f for f in os.listdir(cvs_dir) if f.lower().endswith((".pdf", ".docx"))]
            if not files:
                raise FileNotFoundError("No CV files found in data/cvs")

            json_report_data = []
            batch_ui_data = []
            unique_names = sorted(list(set(os.path.splitext(f)[0] for f in files)))
            score_algo_func = self.ALGORITHMS["Knuth-Morris-Pratt (KMP)"]

            for name in unique_names:
                pdf_path = os.path.join(cvs_dir, name + ".pdf"); docx_path = os.path.join(cvs_dir, name + ".docx")
                text = None
                if os.path.exists(pdf_path): text = extract_text_from_pdf(pdf_path)
                elif os.path.exists(docx_path): text = extract_text_from_docx(docx_path)
                if not text: continue
                
                text_to_search = text.lower()
                
                # 1. Calculate Weighted Score
                matched_mandatory = 0; matched_preferred = 0
                scoring_keywords = mandatory_keywords | preferred_keywords
                
                for keyword in scoring_keywords:
                    kw_find = keyword.lower()
                    found_count, _ = score_algo_func(text_to_search, kw_find)
                    if found_count > 0:
                        if keyword in mandatory_keywords: matched_mandatory += 1
                        elif keyword in preferred_keywords: matched_preferred += 1
                
                score_mand = 100.0
                if mandatory_keywords: score_mand = (matched_mandatory / len(mandatory_keywords)) * 100
                score_pref = 100.0
                if preferred_keywords: score_pref = (matched_preferred / len(preferred_keywords)) * 100
                
                cv_score = (score_mand * self.MANDATORY_WEIGHT) + (score_pref * self.PREFERRED_WEIGHT)
                if matched_mandatory < len(mandatory_keywords):
                    penalty_multiplier = 1.0 - (penalty_value / 100.0)
                    cv_score *= penalty_multiplier
                
                batch_ui_data.append({"cv_name": name, "score": cv_score})

                # 2. Calculate Performance
                json_entry = {"cv_name": name, "score": cv_score, "results": []}
                for algo_name, algo_func in self.ALGORITHMS.items():
                    total_comparisons = 0
                    start = time.perf_counter()
                    for kw in all_keywords: 
                        kw_find = kw.lower()
                        _, comps = algo_func(text_to_search, kw_find)
                        total_comparisons += comps
                    end = time.perf_counter()
                    exec_time = (end - start) * 1000
                    json_entry["results"].append({
                        "algorithm": algo_name, "time_ms": exec_time, "comparisons": total_comparisons
                    })
                json_report_data.append(json_entry)
            
            # 3. Save report
            output_path = os.path.join("data", "cv_batch_report.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_report_data, f, indent=4)
            
            # 4. Put success message on the queue
            self.batch_queue.put({
                "status": "SUCCESS", "ui_data": batch_ui_data, "report_path": output_path
            })
        except Exception as e:
            self.batch_queue.put({"status": "ERROR", "message": str(e)})

    def check_batch_queue(self):
        """Checks the queue for messages from the worker thread."""
        try:
            result = self.batch_queue.get(block=False)
            if result["status"] == "SUCCESS":
                self.batch_results_data = result["ui_data"]
                self.update_batch_results_tab()
                self.notebook.select(self.tab_batch_results)
                messagebox.showinfo(
                    "Batch Analysis Complete", 
                    f"Ranked results updated.\nFull performance report saved to:\n{result['report_path']}"
                )
                self.status_label.config(text="Batch analysis complete. Ready.")
            elif result["status"] == "ERROR":
                messagebox.showerror("Batch Analysis Error", result["message"])
                self.status_label.config(text="Error during batch analysis. Ready.")
            self.batch_button.config(state=tk.NORMAL)
            self.analyze_button.config(state=tk.NORMAL)
        except queue.Empty:
            pass # No message
        finally:
            self.root.after(100, self.check_batch_queue)

    # --- END THREADING FUNCTIONS ---

    def update_performance_table(self):
        """Refreshes the 'Performance Table' tab with new data."""
        for item in self.perf_table.get_children(): self.perf_table.delete(item)
        for result in self.performance_data:
            self.perf_table.insert("", tk.END, values=(
                result['name'], f"{result['time']:.4f}", f"{result['comparisons']:,}"
            ))

    def update_performance_chart(self):
        """Refreshes the 'Performance Chart' tab with new data."""
        self.ax1.clear()
        if not self.performance_data:
            self.ax1.set_title("No Performance Data to Display")
            self.canvas.draw()
            return
        algo_names = [r['name'] for r in self.performance_data]
        times = [r['time'] for r in self.performance_data]
        comparisons = [r['comparisons'] for r in self.performance_data]
        self.ax1.bar(algo_names, times, color='skyblue', label='Time (ms)')
        self.ax1.set_ylabel('Execution Time (ms)', color='skyblue')
        self.ax1.tick_params(axis='y', labelcolor='skyblue')
        self.ax1.set_title("Algorithm Performance Comparison")
        ax2 = self.ax1.twinx() 
        ax2.plot(algo_names, comparisons, color='red', marker='o', linestyle='--', label='Comparisons')
        ax2.set_ylabel('Total Comparisons', color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        ax2.get_yaxis().set_major_formatter(
            mticker.FuncFormatter(lambda x, p: format(int(x), ','))
        )
        self.fig.tight_layout()
        self.canvas.draw()

    def update_batch_results_tab(self):
        """Refreshes the 'Batch Results' tab with new data, sorted by score."""
        for item in self.batch_table.get_children(): self.batch_table.delete(item)
        sorted_data = sorted(self.batch_results_data, key=lambda x: x['score'], reverse=True)
        for result in sorted_data:
            self.batch_table.insert("", tk.END, values=(
                result['cv_name'], f"{result['score']:.2f}"
            ))

    def sort_treeview_column(self, tv, col, reverse):
        """Helper to sort a Treeview column when the header is clicked."""
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        try: l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError: l.sort(key=lambda t: t[0], reverse=reverse)
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
        tv.heading(col, command=lambda: self.sort_treeview_column(tv, col, not reverse))

    def export_single_report(self):
        """Saves the current analysis results to a text file."""
        if not self.performance_data:
            messagebox.showerror("Error", "No analysis data to export.")
            return
        try:
            filename = os.path.basename(self.cv_filepath)
            score = self.score_label.cget("text")
            matched = self.matched_list.get(0, tk.END)
            missing = self.missing_list.get(0, tk.END)
            report_content = f"ANALYSIS REPORT FOR: {filename}\n"
            report_content += "===================================\n"
            report_content += f"{score}\n\n"
            report_content += "--- MATCHED KEYWORDS ---\n"
            if matched:
                for item in matched: report_content += f"- {item}\n"
            else: report_content += "None\n"
            report_content += "\n--- MISSING KEYWORDS ---\n"
            if missing:
                for item in missing: report_content += f"- {item}\n"
            else: report_content += "None\n"
            report_content += "\n\n--- ALGORITHM PERFORMANCE ---\n"
            report_content += f"{'Algorithm':<25} | {'Time (ms)':<15} | {'Comparisons':<15}\n"
            report_content += "-"*60 + "\n"
            for result in self.performance_data:
                report_content += f"{result['name']:<25} | {result['time']:<15.4f} | {result['comparisons']:,<15}\n"
            
            save_path = filedialog.asksaveasfilename(
                title="Save Report",
                initialfile=f"CV_Report_{filename}.txt",
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            if not save_path: return
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            messagebox.showinfo("Export Successful", f"Report saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export report: {e}")

# === APPLICATION ENTRY POINT ===

if __name__ == "__main__":
    root = tk.Tk()
    app = CVAnalyzerApp(root)
    
    # --- Set the theme ---
    # Call this *after* creating the app instance
    sv_ttk.set_theme("light") # You can change "dark" to "light"
    
    root.mainloop()
