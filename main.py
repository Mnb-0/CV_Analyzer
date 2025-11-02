import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import json
import os
import pdfplumber
import docx
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import re # Using regex for simple word splitting in algorithms

# --- Algorithm Implementations ---
# Implemented: Brute Force (with whole-word check), Rabin-Karp (rolling hash + verification),
# and KMP (prefix function / LPS). Each returns (found_boolean, num_comparisons).

def _is_word_boundary(text, start, end):
    """
    Check simple whole-word boundary: character before start and after end are non-alphanumeric
    start: index where match begins
    end: index where match ends (exclusive)
    """
    before = text[start - 1] if start > 0 else " "
    after = text[end] if end < len(text) else " "
    return (not before.isalnum()) and (not after.isalnum())

def brute_force_search(text, pattern):
    """
    Brute force search that verifies whole-word boundaries.
    Counts character comparisons (each == check increments comparisons).
    Returns (found_boolean, num_comparisons)
    """
    n = len(text)
    m = len(pattern)

    # Edge cases
    if m == 0:
        return True, 0
    if n < m:
        return False, 0

    comparisons = 0
    found = False

    # Slide window
    for i in range(0, n - m + 1):
        j = 0
        while j < m:
            comparisons += 1
            if text[i + j] != pattern[j]:
                break
            j += 1
        if j == m:
            # verify whole word
            if _is_word_boundary(text, i, i + m):
                found = True
                # We can return early since the caller only needs to know if it's found
                return True, comparisons

    return found, comparisons

def rabin_karp_search(text, pattern):
    """
    Rabin-Karp with rolling hash + verification.
    We use a large prime modulus and base for the rolling hash.
    comparisons counts character equality checks (only during verification),
    not hash computations.
    Returns (found_boolean, num_comparisons)
    """
    n = len(text)
    m = len(pattern)

    if m == 0:
        return True, 0
    if n < m:
        return False, 0

    comparisons = 0

    # Parameters for rolling hash
    base = 256
    mod = 2305843009213693951  # 2^61 - 1, a large Mersenne-ish prime, fits Python ints

    # Compute hash for pattern and first window
    pat_hash = 0
    win_hash = 0
    for i in range(m):
        pat_hash = (pat_hash * base + ord(pattern[i])) % mod
        win_hash = (win_hash * base + ord(text[i])) % mod

    # Precompute base^(m-1) % mod for removing leading char
    power = pow(base, m - 1, mod)

    # Check first window
    if pat_hash == win_hash:
        # verify char-by-char (count comparisons)
        match = True
        for j in range(m):
            comparisons += 1
            if text[j] != pattern[j]:
                match = False
                break
        if match and _is_word_boundary(text, 0, m):
            return True, comparisons

    # Slide window
    for i in range(1, n - m + 1):
        # Remove leading char, add trailing char
        lead = ord(text[i - 1])
        newc = ord(text[i + m - 1])
        win_hash = (win_hash - (lead * power) % mod + mod) % mod
        win_hash = (win_hash * base + newc) % mod

        if win_hash == pat_hash:
            # verify char-by-char to avoid spurious matches
            match = True
            for j in range(m):
                comparisons += 1
                if text[i + j] != pattern[j]:
                    match = False
                    break
            if match and _is_word_boundary(text, i, i + m):
                return True, comparisons

    return False, comparisons

def kmp_search(text, pattern):
    """
    Knuth-Morris-Pratt search with LPS (prefix function).
    Counts character comparisons (each equality check increments comparisons).
    Returns (found_boolean, num_comparisons)
    """
    n = len(text)
    m = len(pattern)

    if m == 0:
        return True, 0
    if n < m:
        return False, 0

    # Build LPS array
    lps = [0] * m
    length = 0  # length of the previous longest prefix suffix
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
                # no i increment here
            else:
                lps[i] = 0
                i += 1

    # Search
    comparisons = 0
    i = 0  # index for text
    j = 0  # index for pattern
    while i < n:
        comparisons += 1
        if text[i] == pattern[j]:
            i += 1
            j += 1
            if j == m:
                # found at i - j
                start = i - j
                if _is_word_boundary(text, start, start + m):
                    return True, comparisons
                # prepare for next potential match
                j = lps[j - 1]
        else:
            if j != 0:
                j = lps[j - 1]
                # note: we do NOT increment i here
            else:
                i += 1

    return False, comparisons

# --- Text Extraction Functions ---

def extract_text_from_pdf(pdf_file_path):
    """Extracts text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        messagebox.showerror("PDF Error", f"Error extracting text from PDF: {e}")
        return None

def extract_text_from_docx(docx_file_path):
    """Extracts text from a DOCX file."""
    text = ""
    try:
        doc = docx.Document(docx_file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        messagebox.showerror("DOCX Error", f"Error extracting text from DOCX: {e}")
        return None

# --- Main Application Class ---

class CVAnalyzerApp:
    
    ALGORITHMS = {
        "Brute Force": brute_force_search,
        "Rabin-Karp": rabin_karp_search,
        "Knuth-Morris-Pratt (KMP)": kmp_search
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Intelligent CV Analyzer")
        self.root.geometry("1000x700")

        self.cv_filepath = ""
        self.cv_text_content = ""
        self.performance_data = [] # To store results for chart

        # --- Main Layout ---
        # Use PanedWindow for resizable sections
        self.main_paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_paned_window.pack(fill=tk.BOTH, expand=True)

        # --- Left Panel: Inputs ---
        self.input_frame = ttk.Frame(self.main_paned_window, width=300, relief=tk.RIDGE)
        self.input_frame.pack_propagate(False) # Prevent frame from shrinking
        self.main_paned_window.add(self.input_frame, weight=1)

        # --- Right Panel: Outputs (with Tabs) ---
        self.output_frame = ttk.Frame(self.main_paned_window, width=700)
        self.main_paned_window.add(self.output_frame, weight=3)

        self.notebook = ttk.Notebook(self.output_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Create Output Tabs ---
        self.tab_results = ttk.Frame(self.notebook)
        self.tab_performance_table = ttk.Frame(self.notebook)
        self.tab_performance_chart = ttk.Frame(self.notebook)
        self.tab_cv_text = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_results, text="Keyword Results")
        self.notebook.add(self.tab_performance_table, text="Performance Table")
        self.notebook.add(self.tab_performance_chart, text="Performance Chart")
        self.notebook.add(self.tab_cv_text, text="Extracted CV Text")

        # --- Populate Input Frame (Left) ---
        self.create_input_widgets()

        # --- Populate Output Tabs (Right) ---
        self.create_results_tab_widgets()
        self.create_performance_table_tab_widgets()
        self.create_performance_chart_tab_widgets()
        self.create_cv_text_tab_widgets()
        
        # Configure resizing
        self.input_frame.grid_rowconfigure(1, weight=1)
        self.input_frame.grid_columnconfigure(0, weight=1)
        
    def load_job_keywords(self, event=None):
        """Load job keywords from the JSON file based on the selected position."""
        selected = self.selected_job.get()
        if not selected:
            return

        filename_map = {
            "Senior AI/ML Engineer (Agentic AI)": "agentic_ai_engineer.json",
            "Computer Vision Engineer": "computer_vision_engineer.json",
            "Data Scientist": "data_scientist.json"
        }

        file_path = os.path.join("data/job_descriptions", filename_map[selected])

        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"Job description file not found:\n{file_path}")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Combine all relevant keyword sources
            all_keywords = []
            for key in ["required_skills", "preferred_skills", "tools_and_frameworks"]:
                if key in data and isinstance(data[key], list):
                    all_keywords.extend(data[key])

            if not all_keywords:
                messagebox.showwarning("Warning", "No keywords found in job file.")
                return

            # Update text box
            self.keywords_text.config(state=tk.NORMAL)
            self.keywords_text.delete("1.0", tk.END)
            for kw in sorted(set(all_keywords)):
                self.keywords_text.insert(tk.END, kw + "\n")
            self.keywords_text.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load job description:\n{e}")


    def create_input_widgets(self):
        self.input_frame.grid_propagate(False)

        # --- Job Selection ---
        ttk.Label(self.input_frame, text="1. Select Job Position:").grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.job_options = [
            "Senior AI/ML Engineer (Agentic AI)",
            "Computer Vision Engineer",
            "Data Scientist"
        ]
        self.selected_job = tk.StringVar()
        self.job_dropdown = ttk.Combobox(self.input_frame, textvariable=self.selected_job, values=self.job_options, state="readonly")
        self.job_dropdown.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.job_dropdown.bind("<<ComboboxSelected>>", self.load_job_keywords)

        # --- Keywords Display (auto-loaded from JSON) ---
        ttk.Label(self.input_frame, text="2. Job Keywords (auto-loaded):").grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")
        self.keywords_text = tk.Text(self.input_frame, height=10, width=35, state=tk.DISABLED)
        self.keywords_text.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")

        # --- Upload CV Section ---
        ttk.Label(self.input_frame, text="3. Upload CV:").grid(row=4, column=0, padx=10, pady=(10, 5), sticky="w")
        self.load_cv_button = ttk.Button(self.input_frame, text="Load CV File", command=self.load_cv)
        self.load_cv_button.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        self.cv_filename_label = ttk.Label(self.input_frame, text="No file loaded.", wraplength=280)
        self.cv_filename_label.grid(row=6, column=0, padx=10, pady=5, sticky="w")

        # --- Options ---
        ttk.Label(self.input_frame, text="4. Options:").grid(row=7, column=0, padx=10, pady=(10, 5), sticky="w")
        self.case_sensitive_var = tk.BooleanVar(value=False)
        self.case_sensitive_check = ttk.Checkbutton(self.input_frame, text="Case Sensitive Search", variable=self.case_sensitive_var)
        self.case_sensitive_check.grid(row=8, column=0, padx=10, pady=5, sticky="w")

        # --- Analyze Button ---
        self.analyze_button = ttk.Button(self.input_frame, text="Analyze CV", command=self.run_analysis, style="Accent.TButton")
        self.analyze_button.grid(row=9, column=0, padx=10, pady=20, sticky="ew")

        # Style
        style = ttk.Style()
        style.configure("Accent.TButton", font=('TkDefaultFont', 12, 'bold'))

    def create_results_tab_widgets(self):
        # Frame for metrics
        metrics_frame = ttk.Frame(self.tab_results)
        metrics_frame.pack(fill="x", padx=10, pady=10)
        
        self.score_label = ttk.Label(metrics_frame, text="Relevance Score: --%", font=('TkDefaultFont', 14, 'bold'))
        self.score_label.pack(side=tk.LEFT, padx=10)

        # Frames for lists
        lists_frame = ttk.Frame(self.tab_results)
        lists_frame.pack(fill="both", expand=True, padx=10, pady=10)
        lists_frame.grid_columnconfigure(0, weight=1)
        lists_frame.grid_columnconfigure(1, weight=1)
        lists_frame.grid_rowconfigure(1, weight=1)
        
        ttk.Label(lists_frame, text="✅ Matched Keywords", font=('TkDefaultFont', 12, 'bold')).grid(row=0, column=0, pady=5)
        self.matched_list = tk.Listbox(lists_frame, background="#e0ffe0", foreground="#006400")
        self.matched_list.grid(row=1, column=0, sticky="nsew", padx=5)
        
        ttk.Label(lists_frame, text="❌ Missing Keywords", font=('TkDefaultFont', 12, 'bold')).grid(row=0, column=1, pady=5)
        self.missing_list = tk.Listbox(lists_frame, background="#ffe0e0", foreground="#a00000")
        self.missing_list.grid(row=1, column=1, sticky="nsew", padx=5)

    def create_performance_table_tab_widgets(self):
        # Create a Treeview to act as a table
        self.perf_table = ttk.Treeview(self.tab_performance_table, columns=("Algorithm", "Time", "Comparisons"), show="headings")
        self.perf_table.heading("Algorithm", text="Algorithm")
        self.perf_table.heading("Time", text="Execution Time (ms)")
        self.perf_table.heading("Comparisons", text="Total Comparisons")
        
        self.perf_table.column("Algorithm", width=200)
        self.perf_table.column("Time", width=150, anchor=tk.E)
        self.perf_table.column("Comparisons", width=150, anchor=tk.E)
        
        self.perf_table.pack(fill="both", expand=True, padx=10, pady=10)

    def create_performance_chart_tab_widgets(self):
        # This frame will hold the matplotlib canvas
        self.chart_frame = ttk.Frame(self.tab_performance_chart)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial empty chart
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax1 = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ax1.set_title("Performance Comparison")
        self.ax1.set_ylabel("Execution Time (ms)")
        self.fig.tight_layout()

    def create_cv_text_tab_widgets(self):
        self.cv_text_widget = tk.Text(self.tab_cv_text, wrap=tk.WORD, state=tk.DISABLED)
        self.cv_text_scrollbar = ttk.Scrollbar(self.tab_cv_text, orient=tk.VERTICAL, command=self.cv_text_widget.yview)
        self.cv_text_widget.configure(yscrollcommand=self.cv_text_scrollbar.set)
        
        self.cv_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cv_text_widget.pack(fill="both", expand=True, padx=5, pady=5)

    def load_cv(self):
        filepath = filedialog.askopenfilename(
            title="Select CV File",
            filetypes=(("PDF Files", "*.pdf"), ("Word Documents", "*.docx"), ("All Files", "*.*"))
        )
        if filepath:
            self.cv_filepath = filepath
            filename = filepath.split('/')[-1]
            self.cv_filename_label.config(text=f"Loaded: {filename}")
            
            # Extract text immediately
            self.cv_text_content = ""
            if filepath.endswith(".pdf"):
                self.cv_text_content = extract_text_from_pdf(filepath)
            elif filepath.endswith(".docx"):
                self.cv_text_content = extract_text_from_docx(filepath)
            
            if self.cv_text_content:
                # Update the CV text tab
                self.cv_text_widget.config(state=tk.NORMAL)
                self.cv_text_widget.delete("1.0", tk.END)
                self.cv_text_widget.insert("1.0", self.cv_text_content)
                self.cv_text_widget.config(state=tk.DISABLED)
            else:
                self.cv_filename_label.config(text="Failed to read file.")

    def run_analysis(self):
        # 1. Get inputs
        if not self.selected_job.get():
            messagebox.showerror("Error", "Please select a job position first.")
            return

        self.keywords_text.config(state=tk.NORMAL)
        keywords_raw = self.keywords_text.get("1.0", tk.END)
        self.keywords_text.config(state=tk.DISABLED)

        keywords = [k.strip() for k in keywords_raw.split("\n") if k.strip()]
        
        if not self.cv_filepath:
            messagebox.showerror("Error", "Please load a CV file first.")
            return
            
        if not keywords:
            messagebox.showerror("Error", "Please enter at least one keyword.")
            return

        if not self.cv_text_content:
            messagebox.showerror("Error", "Could not read text from CV. Please try re-loading.")
            return

        # 2. Run all algorithms for comparison
        self.performance_data = []
        all_matched_keywords = set()
        all_missing_keywords = set(keywords)
        
        is_case_sensitive = self.case_sensitive_var.get()
        
        # Prepare text based on case sensitivity
        cv_text_to_search = self.cv_text_content if is_case_sensitive else self.cv_text_content.lower()

        for algo_name, algo_func in self.ALGORITHMS.items():
            
            matched_for_this_algo = []
            missing_for_this_algo = []
            total_comparisons = 0
            
            start_time = time.perf_counter()
            
            for keyword in keywords:
                keyword_to_find = keyword if is_case_sensitive else keyword.lower()
                
                # Run the actual algorithm
                found, comparisons = algo_func(cv_text_to_search, keyword_to_find)
                
                total_comparisons += comparisons
                if found:
                    matched_for_this_algo.append(keyword)
                else:
                    missing_for_this_algo.append(keyword)
            
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000
            
            score = 0
            if keywords:
                score = (len(matched_for_this_algo) / len(keywords)) * 100
                
            # Store results
            self.performance_data.append({
                "name": algo_name,
                "time": execution_time_ms,
                "comparisons": total_comparisons,
                "score": score,
                "matched": matched_for_this_algo,
                "missing": missing_for_this_algo
            })
            
            # Update the master list (assuming all algos *should* find the same things)
            all_matched_keywords.update(matched_for_this_algo)
            all_missing_keywords.intersection_update(missing_for_this_algo)

        # 3. Update GUI Tabs
        if not self.performance_data:
            messagebox.showinfo("Info", "Analysis complete, but no data was generated.")
            return

        # Update Results Tab (use results from the first algorithm as representative)
        first_result = self.performance_data[0]
        self.score_label.config(text=f"Relevance Score: {first_result['score']:.2f}%")
        
        self.matched_list.delete(0, tk.END)
        for item in first_result['matched']:
            self.matched_list.insert(tk.END, item)
            
        self.missing_list.delete(0, tk.END)
        for item in first_result['missing']:
            self.missing_list.insert(tk.END, item)

        # Update Performance Table Tab
        self.update_performance_table()
        
        # Update Performance Chart Tab
        self.update_performance_chart()
        
        # Switch to the results tab
        self.notebook.select(self.tab_results)
        
    def update_performance_table(self):
        # Clear old data
        for item in self.perf_table.get_children():
            self.perf_table.delete(item)
            
        # Insert new data
        for result in self.performance_data:
            self.perf_table.insert("", tk.END, values=(
                result['name'],
                f"{result['time']:.4f}",
                f"{result['comparisons']:,}"
            ))

    def update_performance_chart(self):
        # Clear previous chart
        self.ax1.clear()
        
        if not self.performance_data:
            self.ax1.set_title("No Performance Data to Display")
            self.canvas.draw()
            return
            
        algo_names = [r['name'] for r in self.performance_data]
        times = [r['time'] for r in self.performance_data]
        comparisons = [r['comparisons'] for r in self.performance_data]
        
        # Bar chart for Time
        self.ax1.bar(algo_names, times, color='skyblue', label='Time (ms)')
        self.ax1.set_ylabel('Execution Time (ms)', color='skyblue')
        self.ax1.tick_params(axis='y', labelcolor='skyblue')
        self.ax1.set_title("Algorithm Performance Comparison")
        
        # Create a second Y-axis for Comparisons
        ax2 = self.ax1.twinx()
        ax2.plot(algo_names, comparisons, color='red', marker='o', linestyle='--', label='Comparisons')
        ax2.set_ylabel('Total Comparisons', color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        
        self.fig.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = CVAnalyzerApp(root)
    root.mainloop()
