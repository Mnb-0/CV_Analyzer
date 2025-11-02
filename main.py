# main.py
# The main entry point for the CV Analyzer application.

import tkinter as tk
from app import CVAnalyzerApp  # <-- Import the GUI class from app.py
import sv_ttk

if __name__ == "__main__":
    # 1. Create the root window
    root = tk.Tk()
    
    # 2. Create an instance of the application class
    app = CVAnalyzerApp(root)
    
    # 3. Set the theme
    sv_ttk.set_theme("light")
    
    # 4. Start the main event loop
    root.mainloop()