# === IMPORTS ===
#
# --- Standard Library ---
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import json
import os

# --- Third-Party Libraries ---
import pdfplumber  # For reading text from PDF files
import docx        # For reading text from .docx files
from matplotlib.figure import Figure
import matplotlib.ticker as mticker  # For formatting chart ticks
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # For embedding charts in Tkinter

# === ALGORITHM IMPLEMENTATIONS ===
# This section contains the three string-matching algorithms
# required by the assignment, plus a helper function.
# Each search function returns a tuple: (found_boolean, num_comparisons)

def _is_word_boundary(text, start, end):
    """
    Helper function to check for simple whole-word boundaries.
    A match is considered "whole word" if the characters immediately
    before and after it are not alphanumeric.
    
    Args:
        text (str): The full text being searched.
        start (int): The starting index of the potential match.
        end (int): The (exclusive) ending index of the potential match.
        
    Returns:
        bool: True if it's a whole-word match, False otherwise.
    """
    # Check character before the match, or treat as boundary if at start
    before = text[start - 1] if start > 0 else " "
    # Check character after the match, or treat as boundary if at end
    after = text[end] if end < len(text) else " "
    
    return (not before.isalnum()) and (not after.isalnum())

def brute_force_search(text, pattern):
    """
    Performs a Brute Force string search.
    It verifies that any match found is a "whole word".
    
    Args:
        text (str): The text to search within.
        pattern (str): The pattern to find.
        
    Returns:
        tuple: (bool: True if found, int: number of character comparisons)
    """
    n = len(text)
    m = len(pattern)

    # Edge cases
    if m == 0: return True, 0
    if n < m: return False, 0

    comparisons = 0
    found = False

    # Slide the pattern window one character at a time
    for i in range(n - m + 1):
        j = 0
        # Check for a match at the current window position
        while j < m:
            comparisons += 1
            if text[i + j] != pattern[j]:
                break  # Mismatch, move window
            j += 1
        
        # If the inner loop completed, we found a character-for-character match
        if j == m:
            # Now, verify it's a whole word
            if _is_word_boundary(text, i, i + m):
                found = True
                # Since we only need to know *if* it exists, we can return early
                return True, comparisons

    # Return the final result after checking all windows
    return found, comparisons

def rabin_karp_search(text, pattern):
    """
    Performs a Rabin-Karp string search using a rolling hash.
    It verifies matches to prevent hash collisions (spurious hits)
    and checks for "whole word" boundaries.
    
    Args:
        text (str): The text to search within.
        pattern (str): The pattern to find.
        
    Returns:
        tuple: (bool: True if found, int: number of character comparisons)
    """
    n = len(text)
    m = len(pattern)

    # Edge cases
    if m == 0: return True, 0
    if n < m: return False, 0

    comparisons = 0

    # --- Hash Parameters ---
    # Base (number of characters in the alphabet, or a prime > alphabet size)
    base = 256
    # Modulus (a large prime number to prevent overflow and distribute hashes)
    # Using 2^61 - 1, a large Mersenne prime
    mod = 2305843009213693951  

    # --- Precomputation ---
    # 1. Compute hash for the pattern and the first text window
    pat_hash = 0
    win_hash = 0
    for i in range(m):
        pat_hash = (pat_hash * base + ord(pattern[i])) % mod
        win_hash = (win_hash * base + ord(text[i])) % mod

    # 2. Precompute (base^(m-1)) % mod
    # This is the "power" of the most significant character,
    # needed to remove it from the hash during rolling.
    power = pow(base, m - 1, mod)

    # --- Search ---
    # 1. Check the first window (i = 0)
    if pat_hash == win_hash:
        # Hash match! Must verify char-by-char to avoid collision.
        match = True
        for j in range(m):
            comparisons += 1
            if text[j] != pattern[j]:
                match = False
                break
        if match and _is_word_boundary(text, 0, m):
            return True, comparisons

    # 2. Slide the window from i = 1 to n - m
    for i in range(1, n - m + 1):
        # Calculate the rolling hash
        lead_char_val = ord(text[i - 1])
        new_char_val = ord(text[i + m - 1])
        
        # a. Remove the leading character's contribution
        win_hash = (win_hash - (lead_char_val * power) % mod + mod) % mod
        # b. Shift the hash left
        win_hash = (win_hash * base) % mod
        # c. Add the new trailing character's contribution
        win_hash = (win_hash + new_char_val) % mod

        # Check for hash match
        if win_hash == pat_hash:
            # Hash match! Verify char-by-char.
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
    Performs a Knuth-Morris-Pratt (KMP) string search using a
    Longest Proper Prefix which is also a Suffix (LPS) array.
    It verifies that any match found is a "whole word".
    
    Args:
        text (str): The text to search within.
        pattern (str): The pattern to find.
        
    Returns:
        tuple: (bool: True if found, int: number of character comparisons)
    """
    n = len(text)
    m = len(pattern)

    # Edge cases
    if m == 0: return True, 0
    if n < m: return False, 0

    # --- 1. Build the LPS (Longest Proper Prefix-Suffix) Array ---
    # lps[i] stores the length of the longest proper prefix of pattern[0..i]
    # which is also a suffix of pattern[0..i].
    lps = [0] * m
    length = 0  # Length of the previous longest prefix-suffix
    i = 1       # Start from the second character

    while i < m:
        if pattern[i] == pattern[length]:
            # Match: extend the previous prefix-suffix
            length += 1
            lps[i] = length
            i += 1
        else:
            # Mismatch
            if length != 0:
                # Fall back to the lps value of the previous character
                length = lps[length - 1]
                # Note: We do NOT increment 'i' here, we re-check
            else:
                # No prefix-suffix to fall back to
                lps[i] = 0
                i += 1

    # --- 2. Perform the Search ---
    comparisons = 0
    i = 0  # Index for text
    j = 0  # Index for pattern

    while i < n:
        comparisons += 1
        if text[i] == pattern[j]:
            # Characters match
            i += 1
            j += 1
            
            if j == m:
                # Full pattern match found!
                start_index = i - j
                # Verify whole word
                if _is_word_boundary(text, start_index, start_index + m):
                    return True, comparisons
                
                # We found a match, but it wasn't a whole word.
                # Continue searching by "shifting" the pattern using LPS.
                j = lps[j - 1]
        
        else:
            # Mismatch after j > 0 matches
            if j != 0:
                # Don't backtrack 'i', just shift 'j' using the LPS array
                j = lps[j - 1]
            else:
                # Mismatch at the very first character of the pattern
                # Move to the next character in the text
                i += 1

    return False, comparisons

# === FILE EXTRACTION UTILITIES ===
# These functions handle reading text from different file types.

def extract_text_from_pdf(pdf_file_path):
    """
    Extracts all text from a .pdf file using pdfplumber.
    Shows an error message box on failure.
    """
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
    """
    Extracts all text from a .docx file using python-docx.
    Shows an error message box on failure.
    """
    text = ""
    try:
        doc = docx.Document(docx_file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        messagebox.showerror("DOCX Error", f"Error extracting text from DOCX: {e}")
        return None

# === MAIN APPLICATION CLASS ===
# This class encapsulates the entire Tkinter GUI and its logic.

class CVAnalyzerApp:
    
    # Map algorithm names to their functions for easy access
    ALGORITHMS = {
        "Brute Force": brute_force_search,
        "Rabin-Karp": rabin_karp_search,
        "Knuth-Morris-Pratt (KMP)": kmp_search
    }

    def __init__(self, root):
        """
        Constructor for the main application.
        Sets up the main window and initializes the UI.
        """
        self.root = root
        self.root.title("Intelligent CV Analyzer")
        self.root.geometry("1000x700") # Set a default size

        # --- Application State Variables ---
        self.cv_filepath = ""         # Path to the loaded CV file
        self.cv_text_content = ""     # Extracted text from the CV
        self.performance_data = []    # Stores results from all algos for comparison

        # --- Main Layout ---
        # A PanedWindow creates a resizable divider between two frames
        self.main_paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_paned_window.pack(fill=tk.BOTH, expand=True)

        # 1. Left Panel (Inputs)
        self.input_frame = ttk.Frame(self.main_paned_window, width=300, relief=tk.RIDGE)
        # 'pack_propagate(False)' stops the frame from shrinking to fit its contents
        self.input_frame.pack_propagate(False) 
        self.main_paned_window.add(self.input_frame, weight=1) # 'weight=1' allows resizing

        # 2. Right Panel (Outputs)
        self.output_frame = ttk.Frame(self.main_paned_window, width=700)
        self.main_paned_window.add(self.output_frame, weight=3) # 'weight=3' gives it more space

        # --- Output Tabs ---
        # A Notebook widget holds all the output tabs
        self.notebook = ttk.Notebook(self.output_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create the individual frames for each tab
        self.tab_results = ttk.Frame(self.notebook)
        self.tab_performance_table = ttk.Frame(self.notebook)
        self.tab_performance_chart = ttk.Frame(self.notebook)
        self.tab_cv_text = ttk.Frame(self.notebook)

        # Add the tabs to the notebook
        self.notebook.add(self.tab_results, text="Keyword Results")
        self.notebook.add(self.tab_performance_table, text="Performance Table")
        self.notebook.add(self.tab_performance_chart, text="Performance Chart")
        self.notebook.add(self.tab_cv_text, text="Extracted CV Text")

        # --- Build Widgets ---
        # Call the methods to populate the frames and tabs
        self.create_input_widgets()
        self.create_results_tab_widgets()
        self.create_performance_table_tab_widgets()
        self.create_performance_chart_tab_widgets()
        self.create_cv_text_tab_widgets()
        
        # Configure grid resizing for the input frame's text area
        self.input_frame.grid_rowconfigure(3, weight=1) # Row 3 (keywords text) will expand
        self.input_frame.grid_columnconfigure(0, weight=1)
        
    def run_batch_analysis(self):
        cvs_dir = os.path.join("data", "cvs")
        if not os.path.exists(cvs_dir):
            messagebox.showerror("Error", f"No such folder: {cvs_dir}")
            return
        # gather all files (both .pdf and .docx)
        files = [f for f in os.listdir(cvs_dir) if f.lower().endswith((".pdf", ".docx"))]
        if not files:
            messagebox.showerror("Error", "No CV files found in data/cvs")
            return
        if not self.selected_job.get():
            messagebox.showerror("Error", "Please select a job position first.")
            return
        # load keywords from the job
        self.keywords_text.config(state=tk.NORMAL)
        keywords_raw = self.keywords_text.get("1.0", tk.END)
        self.keywords_text.config(state=tk.DISABLED)
        keywords = [k.strip() for k in keywords_raw.split("\n") if k.strip()]
        if not keywords:
            messagebox.showerror("Error", "No keywords loaded for the selected job.")
            return
        # results accumulator
        report_data = []
        # iterate over unique CV basenames (ignoring .pdf/.docx duplication)
        unique_names = set(os.path.splitext(f)[0] for f in files)
        for name in unique_names:
            pdf_path = os.path.join(cvs_dir, name + ".pdf")
            docx_path = os.path.join(cvs_dir, name + ".docx")
            # pick one to read (pdf preferred)
            text = None
            if os.path.exists(pdf_path):
                text = extract_text_from_pdf(pdf_path)
            elif os.path.exists(docx_path):
                text = extract_text_from_docx(docx_path)
            if not text:
                continue
            
            text_to_search = text if self.case_sensitive_var.get() else text.lower()
            entry = {"cv_name": name, "results": []}
            # run all algorithms
            for algo_name, algo_func in self.ALGORITHMS.items():
                total_comparisons = 0
                start = time.perf_counter()
                for kw in keywords:
                    kw_find = kw if self.case_sensitive_var.get() else kw.lower()
                    _, comps = algo_func(text_to_search, kw_find)
                    total_comparisons += comps
                end = time.perf_counter()
                exec_time = (end - start) * 1000
                entry["results"].append({
                    "algorithm": algo_name,
                    "time_ms": exec_time,
                    "comparisons": total_comparisons
                })
            report_data.append(entry)
        # write report to JSON
        output_path = os.path.join("data", "cv_runtime_report.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=4)
        messagebox.showinfo("Batch Analysis Complete", f"Report saved to:\n{output_path}")


    # --- GUI Widget Builders ---
    # These methods create and place the widgets for each part of the UI.
    
    def create_input_widgets(self):
        """Populates the left-hand input frame with all controls."""
        self.input_frame.grid_propagate(False) # Keep frame size

        # --- 1. Job Selection ---
        ttk.Label(self.input_frame, text="1. Select Job Position:").grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.job_options = [
            "Senior AI/ML Engineer (Agentic AI)",
            "Computer Vision Engineer",
            "Data Scientist"
        ]
        self.selected_job = tk.StringVar()
        self.job_dropdown = ttk.Combobox(
            self.input_frame, 
            textvariable=self.selected_job, 
            values=self.job_options, 
            state="readonly"
        )
        self.job_dropdown.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        # Bind the '<<ComboboxSelected>>' event to the load_job_keywords method
        self.job_dropdown.bind("<<ComboboxSelected>>", self.load_job_keywords)

        # --- 2. Keywords Display ---
        ttk.Label(self.input_frame, text="2. Job Keywords (auto-loaded):").grid(
            row=2, column=0, padx=10, pady=(10, 5), sticky="w")
        self.keywords_text = tk.Text(self.input_frame, height=10, width=35, state=tk.DISABLED, wrap=tk.WORD)
        self.keywords_text.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")

        # --- 3. Upload CV ---
        ttk.Label(self.input_frame, text="3. Upload CV:").grid(
            row=4, column=0, padx=10, pady=(10, 5), sticky="w")
        self.load_cv_button = ttk.Button(self.input_frame, text="Load CV File", command=self.load_cv)
        self.load_cv_button.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        self.cv_filename_label = ttk.Label(self.input_frame, text="No file loaded.", wraplength=280)
        self.cv_filename_label.grid(row=6, column=0, padx=10, pady=5, sticky="w")

        # --- 4. Options ---
        ttk.Label(self.input_frame, text="4. Options:").grid(
            row=7, column=0, padx=10, pady=(10, 5), sticky="w")
        self.case_sensitive_var = tk.BooleanVar(value=False)
        self.case_sensitive_check = ttk.Checkbutton(
            self.input_frame, 
            text="Case Sensitive Search", 
            variable=self.case_sensitive_var
        )
        self.case_sensitive_check.grid(row=8, column=0, padx=10, pady=5, sticky="w")

        # --- 5. Analyze Button ---
        self.analyze_button = ttk.Button(
            self.input_frame, 
            text="Analyze CV", 
            command=self.run_analysis, 
            style="Accent.TButton" # Special style for emphasis
        )
        self.analyze_button.grid(row=9, column=0, padx=10, pady=20, sticky="ew")

        # --- Batch Analysis ---
        self.batch_button = ttk.Button(
            self.input_frame,
            text="Run Batch Analysis (data/cvs)",
            command=self.run_batch_analysis
        )
        self.batch_button.grid(row=10, column=0, padx=10, pady=5, sticky="ew")

        
        # Define the custom "Accent" button style
        style = ttk.Style()
        style.configure("Accent.TButton", font=('TkDefaultFont', 12, 'bold'))

    def create_results_tab_widgets(self):
        """Populates the 'Keyword Results' tab."""
        # Frame for the main metric (Relevance Score)
        metrics_frame = ttk.Frame(self.tab_results)
        metrics_frame.pack(fill="x", padx=10, pady=10)
        
        self.score_label = ttk.Label(
            metrics_frame, 
            text="Relevance Score: --%", 
            font=('TkDefaultFont', 14, 'bold')
        )
        self.score_label.pack(side=tk.LEFT, padx=10)

        # Frame to hold the two keyword lists (Matched vs. Missing)
        lists_frame = ttk.Frame(self.tab_results)
        lists_frame.pack(fill="both", expand=True, padx=10, pady=10)
        # Configure columns to have equal weight (so they resize together)
        lists_frame.grid_columnconfigure(0, weight=1)
        lists_frame.grid_columnconfigure(1, weight=1)
        lists_frame.grid_rowconfigure(1, weight=1) # Row 1 (Listboxes) will expand
        
        # Matched Keywords
        ttk.Label(lists_frame, text="✅ Matched Keywords", font=('TkDefaultFont', 12, 'bold')).grid(
            row=0, column=0, pady=5)
        self.matched_list = tk.Listbox(lists_frame, background="#e0ffe0", foreground="#006400")
        self.matched_list.grid(row=1, column=0, sticky="nsew", padx=5)
        
        # Missing Keywords
        ttk.Label(lists_frame, text="❌ Missing Keywords", font=('TkDefaultFont', 12, 'bold')).grid(
            row=0, column=1, pady=5)
        self.missing_list = tk.Listbox(lists_frame, background="#ffe0e0", foreground="#a00000")
        self.missing_list.grid(row=1, column=1, sticky="nsew", padx=5)

    def create_performance_table_tab_widgets(self):
        """Populates the 'Performance Table' tab with a Treeview."""
        # A Treeview widget can be configured to look like a table
        self.perf_table = ttk.Treeview(
            self.tab_performance_table, 
            columns=("Algorithm", "Time", "Comparisons"), 
            show="headings" # Hide the default first column
        )
        # Define column headings
        self.perf_table.heading("Algorithm", text="Algorithm")
        self.perf_table.heading("Time", text="Execution Time (ms)")
        self.perf_table.heading("Comparisons", text="Total Comparisons")
        
        # Define column properties
        self.perf_table.column("Algorithm", width=200)
        self.perf_table.column("Time", width=150, anchor=tk.E) # 'E' = East (right-aligned)
        self.perf_table.column("Comparisons", width=150, anchor=tk.E)
        
        self.perf_table.pack(fill="both", expand=True, padx=10, pady=10)

    def create_performance_chart_tab_widgets(self):
        """Populates the 'Performance Chart' tab with a Matplotlib canvas."""
        # This frame will contain the chart canvas
        self.chart_frame = ttk.Frame(self.tab_performance_chart)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create the initial empty Matplotlib Figure and Axes
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax1 = self.fig.add_subplot(111) # Primary Y-axis
        
        # Create the Tkinter-compatible canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Set initial chart properties
        self.ax1.set_title("Performance Comparison")
        self.ax1.set_ylabel("Execution Time (ms)")
        self.fig.tight_layout()

    def create_cv_text_tab_widgets(self):
        """Populates the 'Extracted CV Text' tab with a scrollable Text widget."""
        self.cv_text_widget = tk.Text(self.tab_cv_text, wrap=tk.WORD, state=tk.DISABLED)
        self.cv_text_scrollbar = ttk.Scrollbar(
            self.tab_cv_text, 
            orient=tk.VERTICAL, 
            command=self.cv_text_widget.yview
        )
        self.cv_text_widget.configure(yscrollcommand=self.cv_text_scrollbar.set)
        
        # Pack the scrollbar and text widget
        self.cv_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cv_text_widget.pack(fill="both", expand=True, padx=5, pady=5)

    # --- Core Logic & Event Handlers ---
    # These methods are called in response to user actions.
    
    def load_job_keywords(self, event=None):
        """
        Event handler for the Job Position combobox.
        Loads keywords from a corresponding JSON file.
        """
        selected_job_title = self.selected_job.get()
        if not selected_job_title:
            return

        # Map the user-friendly title to a filename
        filename_map = {
            "Senior AI/ML Engineer (Agentic AI)": "agentic_ai_engineer.json",
            "Computer Vision Engineer": "computer_vision_engineer.json",
            "Data Scientist": "data_scientist.json"
        }
        
        if selected_job_title not in filename_map:
            messagebox.showerror("Error", "Invalid job selection.")
            return

        # Assume JSONs are in a 'data/job_descriptions' subfolder
        file_path = os.path.join("data", "job_descriptions", filename_map[selected_job_title])

        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"Job description file not found:\n{file_path}")
            return

        try:
            # Read and parse the JSON file
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Combine keywords from different sections of the JSON
            all_keywords = []
            for key in ["required_skills", "preferred_skills", "tools_and_frameworks"]:
                if key in data and isinstance(data[key], list):
                    all_keywords.extend(data[key])

            if not all_keywords:
                messagebox.showwarning("Warning", f"No keywords found in '{file_path}'.")
                return

            # Update the (disabled) keywords text box
            self.keywords_text.config(state=tk.NORMAL) # Must be enabled to modify
            self.keywords_text.delete("1.0", tk.END)
            # Use sorted(set(...)) to get unique, alphabetized keywords
            for kw in sorted(set(all_keywords)):
                self.keywords_text.insert(tk.END, kw + "\n")
            self.keywords_text.config(state=tk.DISABLED) # Disable again

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load job description from JSON:\n{e}")

    def load_cv(self):
        """
        Event handler for the 'Load CV File' button.
        Opens a file dialog and extracts text from the selected file.
        """
        filepath = filedialog.askopenfilename(
            title="Select CV File",
            filetypes=(("PDF Files", "*.pdf"), 
                       ("Word Documents", "*.docx"), 
                       ("All Files", "*.*"))
        )
        if not filepath:
            return # User cancelled

        self.cv_filepath = filepath
        filename = os.path.basename(filepath)
        self.cv_filename_label.config(text=f"Loaded: {filename}")
        
        # --- Extract Text Immediately ---
        self.cv_text_content = ""
        if filepath.endswith(".pdf"):
            self.cv_text_content = extract_text_from_pdf(filepath)
        elif filepath.endswith(".docx"):
            self.cv_text_content = extract_text_from_docx(filepath)
        else:
            messagebox.showwarning("Warning", "Unknown file type. Only .pdf and .docx are supported for text extraction.")
            return
        
        if self.cv_text_content:
            # Update the 'Extracted CV Text' tab
            self.cv_text_widget.config(state=tk.NORMAL) # Enable to modify
            self.cv_text_widget.delete("1.0", tk.END)
            self.cv_text_widget.insert("1.0", self.cv_text_content)
            self.cv_text_widget.config(state=tk.DISABLED) # Disable to make read-only
        else:
            self.cv_filename_label.config(text="Failed to read text from file.")

    def run_analysis(self):
        """
        Event handler for the 'Analyze CV' button.
        This is the main function that runs all algorithms and updates the UI.
        """
        
        # --- 1. Get Inputs and Validate ---
        if not self.selected_job.get():
            messagebox.showerror("Error", "Please select a job position first.")
            return

        # Read keywords from the (disabled) text box
        self.keywords_text.config(state=tk.NORMAL)
        keywords_raw = self.keywords_text.get("1.0", tk.END)
        self.keywords_text.config(state=tk.DISABLED)
        keywords = [k.strip() for k in keywords_raw.split("\n") if k.strip()]
        
        if not self.cv_filepath:
            messagebox.showerror("Error", "Please load a CV file first.")
            return
            
        if not keywords:
            messagebox.showerror("Error", "No keywords found for the selected job.")
            return

        if not self.cv_text_content:
            messagebox.showerror("Error", "Could not read text from CV. Please try re-loading.")
            return

        # --- 2. Run All Algorithms for Comparison ---
        self.performance_data.clear() # Clear data from previous runs
        
        is_case_sensitive = self.case_sensitive_var.get()
        
        # Prepare text once based on case sensitivity
        cv_text_to_search = self.cv_text_content if is_case_sensitive else self.cv_text_content.lower()

        # Loop through all registered algorithms
        for algo_name, algo_func in self.ALGORITHMS.items():
            
            matched_for_this_algo = []
            missing_for_this_algo = []
            total_comparisons = 0
            
            start_time = time.perf_counter() # Use high-precision timer
            
            # Run the search for each keyword
            for keyword in keywords:
                keyword_to_find = keyword if is_case_sensitive else keyword.lower()
                
                found, comparisons = algo_func(cv_text_to_search, keyword_to_find)
                
                total_comparisons += comparisons
                if found:
                    matched_for_this_algo.append(keyword)
                else:
                    missing_for_this_algo.append(keyword)
            
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000 # Convert to ms
            
            # Calculate score
            score = (len(matched_for_this_algo) / len(keywords)) * 100 if keywords else 0
                
            # Store all results in our instance variable
            self.performance_data.append({
                "name": algo_name,
                "time": execution_time_ms,
                "comparisons": total_comparisons,
                "score": score,
                "matched": matched_for_this_algo,
                "missing": missing_for_this_algo
            })

        # --- 3. Update GUI Tabs with New Data ---
        if not self.performance_data:
            messagebox.showinfo("Info", "Analysis complete, but no data was generated.")
            return

        # Update Results Tab
        # (We assume all algorithms *should* give the same match results if correct)
        # So, we just use the results from the first algorithm for the summary.
        first_result = self.performance_data[0]
        self.score_label.config(text=f"Relevance Score: {first_result['score']:.2f}%")
        
        self.matched_list.delete(0, tk.END) # Clear old list
        for item in first_result['matched']:
            self.matched_list.insert(tk.END, item)
            
        self.missing_list.delete(0, tk.END) # Clear old list
        for item in first_result['missing']:
            self.missing_list.insert(tk.END, item)

        # Update Performance Table Tab
        self.update_performance_table()
        
        # Update Performance Chart Tab
        self.update_performance_chart()
        
        # Automatically switch to the results tab
        self.notebook.select(self.tab_results)
        
    def update_performance_table(self):
        """Refreshes the 'Performance Table' tab with new data."""
        # Clear old data
        for item in self.perf_table.get_children():
            self.perf_table.delete(item)
            
        # Insert new data
        for result in self.performance_data:
            self.perf_table.insert("", tk.END, values=(
                result['name'],
                f"{result['time']:.4f}",       # Format time to 4 decimal places
                f"{result['comparisons']:,}" # Format comparisons with commas
            ))

    def update_performance_chart(self):
        """Refreshes the 'Performance Chart' tab with new data."""
        # Clear previous chart
        self.ax1.clear()
        
        if not self.performance_data:
            self.ax1.set_title("No Performance Data to Display")
            self.canvas.draw()
            return
            
        # Extract data for plotting
        algo_names = [r['name'] for r in self.performance_data]
        times = [r['time'] for r in self.performance_data]
        comparisons = [r['comparisons'] for r in self.performance_data]
        
        # --- Plot 1: Bar chart for Time (Primary Y-axis) ---
        self.ax1.bar(algo_names, times, color='skyblue', label='Time (ms)')
        self.ax1.set_ylabel('Execution Time (ms)', color='skyblue')
        self.ax1.tick_params(axis='y', labelcolor='skyblue')
        self.ax1.set_title("Algorithm Performance Comparison")
        
        # --- Plot 2: Line chart for Comparisons (Secondary Y-axis) ---
        # Create a second Y-axis that shares the same X-axis
        ax2 = self.ax1.twinx() 
        ax2.plot(algo_names, comparisons, color='red', marker='o', linestyle='--', label='Comparisons')
        ax2.set_ylabel('Total Comparisons', color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        
        # Format Y-axis ticks with commas for large numbers
        # 
        # !!! THIS IS THE FIX !!!
        # Changed 'tk.matplotlib.ticker.FuncFormatter' to 'mticker.FuncFormatter'
        #
        ax2.get_yaxis().set_major_formatter(
            mticker.FuncFormatter(lambda x, p: format(int(x), ','))
        )
        
        self.fig.tight_layout() # Adjust plot to prevent labels from overlapping
        self.canvas.draw()      # Redraw the canvas with the new plots

# === APPLICATION ENTRY POINT ===
# This code only runs when the script is executed directly.

if __name__ == "__main__":
    root = tk.Tk()  # Create the main window
    app = CVAnalyzerApp(root) # Instantiate our application class
    root.mainloop() # Start the Tkinter event loop