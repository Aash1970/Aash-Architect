import tkinter as tk
from tkinter import ttk, messagebox

# --- DATA: LINKEDIN "AASH SAUCE" (UK 2026 STANDARD) ---
LI_ABOUT = {
    "Bereavement": "Strategic professional with a background in [Field], returning to the workforce after a period dedicated to complex estate management and crisis leadership. Demonstrated high-stakes decision-making and project governance during a critical transition period.",
    "Health Recovery": "Resilient [Field] specialist returning to work with a renewed focus on personal optimization and healthcare navigation. Proven ability to manage long-term recovery projects with discipline, discipline, and strategic adaptability.",
    "Sandwich Care": "Expert in multi-generational logistics and resource allocation. Balanced full-scale domestic operations with complex care-compliance, demonstrating extreme multitasking and emotional intelligence in a high-pressure environment."
}

def apply_li_sauce():
    scenario = scenario_var.get()
    text = LI_ABOUT.get(scenario, "Select a scenario.")
    li_output.delete('1.0', tk.END)
    li_output.insert(tk.END, text)

# --- UI SETUP ---
root = tk.Tk()
root.title("Aash's Career Architect v2.4.0")
root.geometry("700x600")

# TABS
notebook = ttk.Notebook(root)
tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)
notebook.add(tab1, text="Resilience ROI")
notebook.add(tab2, text="LinkedIn Sauce")
notebook.pack(expand=1, fill="both")

# TAB 2: LINKEDIN
ttk.Label(tab2, text="LinkedIn 'About' Generator", font=('Helvetica', 14, 'bold')).pack(pady=10)
scenario_var = tk.StringVar()
scenario_menu = ttk.OptionMenu(tab2, scenario_var, "Select Scenario", *LI_ABOUT.keys())
scenario_menu.pack(pady=10)
ttk.Button(tab2, text="Generate Aash Sauce", command=apply_li_sauce).pack(pady=10)
li_output = tk.Text(tab2, height=12, width=70, font=('Helvetica', 11), wrap='word')
li_output.pack(pady=10)

root.mainloop()
