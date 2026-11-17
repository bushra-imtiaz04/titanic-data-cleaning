"""
CYBER CLEAN - Data Cleansing Console (GUI) - Titanic Dataset
------------------------------------------------------------
A dark "cyber" themed Tkinter desktop app: click a step button, see the
table / chart / log.

Run from anywhere:
    python scripts/cleaning_gui.py
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------------------------------------------------------- theme
BG = "#0A0E17"        # window background
PANEL = "#111827"     # panels
PANEL2 = "#0D1420"    # inactive tabs / chart axes
BORDER = "#1F2A3C"
CYAN = "#00E5FF"
GREEN = "#39FF88"
RED = "#FF3B6B"
AMBER = "#FFB800"
TEXT = "#D6E4F0"
MUTED = "#6B7C93"
HOVER = "#12304A"
UI_FONT = "Consolas"

CYBER_CMAP = LinearSegmentedColormap.from_list("cyber", ["#0B1220", RED])

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CSV = os.path.join(BASE, "data", "titanic.csv")
DEFAULT_OUT = os.path.join(BASE, "data", "titanic_cleaned.csv")


class CleaningApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CYBER CLEAN - Data Cleansing Console")
        self.geometry("1360x800")
        self.minsize(1100, 680)
        self.configure(bg=BG)
        self.raw = None
        self.df = None
        self.csv_path = DEFAULT_CSV
        self.build_ui()
        if os.path.exists(DEFAULT_CSV):
            self.step_load()
        else:
            self.log("Click 'OPEN CSV' and choose titanic.csv to begin.")

    # ------------------------------------------------------------------ UI
    def make_button(self, parent, text, command, kind="step"):
        look = {
            "step": dict(bg=PANEL, fg=TEXT, hover=HOVER, hover_fg=CYAN, border=BORDER, hover_border=CYAN),
            "run": dict(bg=CYAN, fg=BG, hover="#5CF0FF", hover_fg=BG, border=CYAN, hover_border="#5CF0FF"),
            "save": dict(bg=GREEN, fg=BG, hover="#7DFFAD", hover_fg=BG, border=GREEN, hover_border="#7DFFAD"),
            "reset": dict(bg=PANEL, fg=RED, hover="#2A1020", hover_fg=RED, border=RED, hover_border=RED),
            "top": dict(bg=PANEL, fg=CYAN, hover=HOVER, hover_fg=CYAN, border=CYAN, hover_border=CYAN),
        }[kind]
        btn = tk.Button(
            parent, text=text, command=command, bg=look["bg"], fg=look["fg"],
            activebackground=look["hover"], activeforeground=look["hover_fg"],
            relief="flat", bd=0, cursor="hand2", padx=12, pady=8,
            font=(UI_FONT, 10, "bold" if kind != "step" else "normal"),
            anchor="w" if kind == "step" else "center",
            highlightthickness=1, highlightbackground=look["border"], highlightcolor=look["border"])

        def enter(_):
            btn.configure(bg=look["hover"], fg=look["hover_fg"], highlightbackground=look["hover_border"])

        def leave(_):
            btn.configure(bg=look["bg"], fg=look["fg"], highlightbackground=look["border"])

        btn.bind("<Enter>", enter)
        btn.bind("<Leave>", leave)
        return btn

    def build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                        rowheight=24, borderwidth=0, font=(UI_FONT, 9))
        style.configure("Treeview.Heading", background="#1A2438", foreground=CYAN,
                        font=(UI_FONT, 9, "bold"), relief="flat", borderwidth=0)
        style.map("Treeview", background=[("selected", "#0E3A4A")], foreground=[("selected", CYAN)])
        style.map("Treeview.Heading", background=[("active", "#22304A")])
        style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=[0, 4, 0, 0])
        style.configure("TNotebook.Tab", background=PANEL2, foreground=MUTED, padding=[18, 8],
                        font=(UI_FONT, 10, "bold"), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", PANEL)], foreground=[("selected", CYAN)])
        for orient in ("Vertical", "Horizontal"):
            style.configure(f"{orient}.TScrollbar", background="#1F2A3C", troughcolor=BG,
                            bordercolor=BG, arrowcolor=CYAN, lightcolor="#1F2A3C", darkcolor="#1F2A3C")

        # ---- header
        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=16, pady=(12, 0))
        tk.Label(head, text=">_ CYBER CLEAN", bg=BG, fg=CYAN,
                 font=(UI_FONT, 20, "bold")).pack(side="left")
        tk.Label(head, text="  //  Data Cleansing Console  |  pandas pipeline", bg=BG, fg=MUTED,
                 font=(UI_FONT, 11)).pack(side="left", pady=(8, 0))
        self.make_button(head, "OPEN CSV", self.choose_file, "top").pack(side="right")
        self.path_var = tk.StringVar(value=self.csv_path)
        tk.Label(head, textvariable=self.path_var, bg=BG, fg=MUTED,
                 font=(UI_FONT, 9)).pack(side="right", padx=12)
        tk.Frame(self, bg=CYAN, height=2).pack(fill="x", padx=16, pady=(10, 0))

        # ---- status bar (bottom)
        bar = tk.Frame(self, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        bar.pack(side="bottom", fill="x", padx=16, pady=(0, 12))
        self.stat = {}
        for key, title in (("rows", "ROWS"), ("cols", "COLUMNS"), ("missing", "MISSING CELLS"), ("dups", "DUPLICATE ROWS")):
            cell = tk.Frame(bar, bg=PANEL)
            cell.pack(side="left", padx=18, pady=6)
            tk.Label(cell, text=title, bg=PANEL, fg=MUTED, font=(UI_FONT, 8)).pack(anchor="w")
            lbl = tk.Label(cell, text="-", bg=PANEL, fg=CYAN, font=(UI_FONT, 15, "bold"))
            lbl.pack(anchor="w")
            self.stat[key] = lbl

        # ---- main area
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=12)

        side = tk.Frame(main, bg=PANEL, highlightthickness=1, highlightbackground=BORDER, padx=12, pady=12)
        side.pack(side="left", fill="y")
        tk.Label(side, text="// CLEANING PIPELINE", bg=PANEL, fg=GREEN,
                 font=(UI_FONT, 11, "bold")).pack(anchor="w", pady=(0, 8))
        steps = [
            ("[01] Load Dataset", self.step_load),
            ("[02] Detect Missing (Before)", self.step_detect),
            ("[03] Check Duplicates", self.step_duplicates),
            ("[04] Handle Missing Values", self.step_handle),
            ("[05] Verify Missing (After)", self.step_verify),
            ("[06] Validate Consistency", self.step_validate),
            ("[07] Standardise + Types", self.step_standardise),
            ("[08] Outliers (IQR)", self.step_outliers),
        ]
        for text, cmd in steps:
            self.make_button(side, text, cmd, "step").pack(fill="x", pady=3, ipadx=30)
        tk.Frame(side, bg=BORDER, height=1).pack(fill="x", pady=12)
        self.make_button(side, "RUN ALL STEPS", self.run_all, "run").pack(fill="x", pady=3)
        self.make_button(side, "SAVE CLEANED CSV", self.save_csv, "save").pack(fill="x", pady=3)
        self.make_button(side, "RESET", self.step_load, "reset").pack(fill="x", pady=3)

        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(14, 0))
        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill="both", expand=True)

        # Data tab
        data_tab = tk.Frame(self.tabs, bg=PANEL)
        self.tabs.add(data_tab, text="DATA")
        self.table_title = tk.Label(data_tab, text="", anchor="w", bg=PANEL, fg=CYAN,
                                    font=(UI_FONT, 10, "bold"))
        self.table_title.pack(fill="x", padx=10, pady=8)
        holder = tk.Frame(data_tab, bg=PANEL)
        holder.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.tree = ttk.Treeview(holder, show="headings")
        vs = ttk.Scrollbar(holder, orient="vertical", command=self.tree.yview)
        hs = ttk.Scrollbar(holder, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        vs.pack(side="right", fill="y")
        hs.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("na", background="#4A1423", foreground="#FF9DB5")

        # Chart tab
        chart_tab = tk.Frame(self.tabs, bg=PANEL)
        self.tabs.add(chart_tab, text="CHART")
        self.fig = Figure(figsize=(8, 5), dpi=100, facecolor=PANEL)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_tab)
        self.canvas.get_tk_widget().configure(bg=PANEL, highlightthickness=0)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Log tab
        log_tab = tk.Frame(self.tabs, bg=PANEL)
        self.tabs.add(log_tab, text="LOG")
        self.log_box = ScrolledText(log_tab, font=(UI_FONT, 10), state="disabled", bg="#05080F",
                                    fg=GREEN, insertbackground=GREEN, relief="flat", bd=0, padx=12, pady=10)
        self.log_box.pack(fill="both", expand=True)
        self.log_box.tag_config("head", foreground=CYAN, font=(UI_FONT, 10, "bold"))
        self.log_box.tag_config("good", foreground=GREEN)
        self.log_box.tag_config("bad", foreground=RED)
        self.log_box.tag_config("dim", foreground="#2B3A52")

    # ------------------------------------------------------------- helpers
    def log(self, text=""):
        up = text.upper()
        if text.startswith("STEP") or text.startswith("All steps"):
            tag = "head"
        elif "FAIL" in up:
            tag = "bad"
        elif "PASS" in up or "NO MISSING" in up or "NO DUPLICATE" in up:
            tag = "good"
        elif text.startswith("=") or text.startswith("-"):
            tag = "dim"
        else:
            tag = None
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n", (tag,) if tag else ())
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def need_data(self):
        if self.df is None:
            messagebox.showwarning("No data", "Load a CSV first (Step 01).")
            return False
        return True

    def update_status(self):
        d = self.df
        missing = int(d.isnull().sum().sum())
        dups = int(d.duplicated().sum())
        self.stat["rows"].config(text=str(d.shape[0]), fg=CYAN)
        self.stat["cols"].config(text=str(d.shape[1]), fg=CYAN)
        self.stat["missing"].config(text=str(missing), fg=RED if missing else GREEN)
        self.stat["dups"].config(text=str(dups), fg=RED if dups else GREEN)

    def show_table(self, frame, title, max_rows=300):
        shown = min(len(frame), max_rows)
        self.table_title.config(
            text=f">> {title}   [{shown} of {len(frame)} rows | red row = contains missing value]")
        self.tree.delete(*self.tree.get_children())
        cols = list(frame.columns)
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=230 if c == "Name" else 95, anchor="w", stretch=False)
        for _, row in frame.head(max_rows).iterrows():
            vals = ["NaN" if pd.isna(v) else (round(v, 2) if isinstance(v, float) else v) for v in row]
            self.tree.insert("", "end", values=vals, tags=("na",) if row.isnull().any() else ())
        self.tabs.select(0)

    @staticmethod
    def style_ax(ax):
        ax.set_facecolor(PANEL2)
        ax.tick_params(colors=TEXT, labelsize=8)
        ax.title.set_color(CYAN)
        ax.xaxis.label.set_color(TEXT)
        ax.yaxis.label.set_color(TEXT)
        for spine in ax.spines.values():
            spine.set_color(BORDER)
        legend = ax.get_legend()
        if legend:
            legend.get_frame().set_facecolor(PANEL)
            legend.get_frame().set_edgecolor(BORDER)
            for t in legend.get_texts():
                t.set_color(TEXT)

    def show_chart(self, painter):
        self.fig.clf()
        self.fig.patch.set_facecolor(PANEL)
        painter(self.fig)
        for ax in self.fig.axes:
            self.style_ax(ax)
        self.fig.tight_layout(pad=2)
        self.canvas.draw()
        self.tabs.select(1)

    @staticmethod
    def draw_heatmap(ax, frame, title):
        ax.imshow(frame.isnull().values, aspect="auto", cmap=CYBER_CMAP,
                  interpolation="nearest", vmin=0, vmax=1)
        ax.set_xticks(range(frame.shape[1]))
        ax.set_xticklabels(frame.columns, rotation=60, ha="right", fontsize=8)
        ax.set_ylabel("Row index")
        ax.set_title(title, fontsize=11, weight="bold")
        if frame.isnull().sum().sum() == 0:
            ax.text(0.5, 0.5, "NO MISSING VALUES", transform=ax.transAxes, ha="center",
                    va="center", fontsize=16, weight="bold", color=GREEN,
                    bbox=dict(facecolor=BG, edgecolor=GREEN, boxstyle="round,pad=0.6"))

    def sample_ids(self):
        r = self.raw
        ids = []
        if "Embarked" in r.columns:
            ids += list(r.loc[r["Embarked"].isnull(), "PassengerId"])
        if "Age" in r.columns:
            ids += list(r.loc[r["Age"].isnull(), "PassengerId"].head(6))
        return ids

    # --------------------------------------------------------------- steps
    def choose_file(self):
        path = filedialog.askopenfilename(title="Choose a CSV file",
                                          filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.csv_path = path
            self.path_var.set(path)
            self.step_load()

    def step_load(self):
        try:
            df = pd.read_csv(self.csv_path)
        except Exception as exc:
            messagebox.showerror("Could not load file", str(exc))
            return
        self.raw = df.copy()
        self.df = df
        self.path_var.set(self.csv_path)
        self.log("=" * 60)
        self.log("STEP 1: Dataset loaded")
        self.log(f"  File   : {self.csv_path}")
        self.log(f"  Rows   : {df.shape[0]}   Columns: {df.shape[1]}")
        self.show_table(self.df, "Original dataset")
        self.update_status()

    def step_detect(self):
        if not self.need_data():
            return
        miss = self.df.isnull().sum()
        pct = (miss / len(self.df) * 100).round(2)
        self.log("-" * 60)
        self.log("STEP 2: Missing values (BEFORE cleaning)")
        found = miss[miss > 0]
        if found.empty:
            self.log("  No missing values found.")
        for col in found.index:
            self.log(f"  {col:<12s} {int(miss[col]):>5d}   ({pct[col]:.2f} %)")
        self.log(f"  Total missing cells: {int(miss.sum())}")
        ids = self.sample_ids()
        if ids and "PassengerId" in self.raw.columns:
            sample = self.raw[self.raw["PassengerId"].isin(ids)]
            self.show_table(sample, "BEFORE cleaning - sample rows with missing values")
        self.show_chart(lambda f: self.draw_heatmap(f.add_subplot(111), self.df,
                                                    "Missing values map - BEFORE cleaning (red = missing)"))
        self.update_status()

    def step_duplicates(self):
        if not self.need_data():
            return
        dup_rows = int(self.df.duplicated().sum())
        self.log("-" * 60)
        self.log("STEP 3: Duplicate check")
        self.log(f"  Fully duplicated rows: {dup_rows}")
        if "PassengerId" in self.df.columns:
            self.log(f"  Duplicate PassengerId: {int(self.df['PassengerId'].duplicated().sum())}")
        if dup_rows == 0:
            self.log("  No duplicate values found - nothing to remove.")
            messagebox.showinfo("Duplicates", "No duplicate values found.")
        else:
            self.df = self.df.drop_duplicates().reset_index(drop=True)
            self.log(f"  Removed {dup_rows} duplicate rows.")
            self.show_table(self.df, "After removing duplicates")
        self.update_status()

    def step_handle(self):
        if not self.need_data():
            return
        df = self.df
        self.log("-" * 60)
        self.log("STEP 4: Handling missing values")
        if "Embarked" in df.columns and df["Embarked"].isnull().any():
            mode = df["Embarked"].mode()[0]
            df["Embarked"] = df["Embarked"].fillna(mode)
            self.log(f"  Embarked -> filled with mode '{mode}'")
        if "Age" in df.columns and df["Age"].isnull().any():
            if {"Pclass", "Sex"}.issubset(df.columns):
                df["Age"] = df["Age"].fillna(df.groupby(["Pclass", "Sex"])["Age"].transform("median"))
                self.log("  Age      -> filled with median age of same Pclass and Sex")
            else:
                df["Age"] = df["Age"].fillna(df["Age"].median())
                self.log("  Age      -> filled with overall median")
        if "Cabin" in df.columns:
            df["HasCabin"] = df["Cabin"].notnull().astype(int)
            df["Deck"] = df["Cabin"].str[0].fillna("Unknown")
            df.drop(columns=["Cabin"], inplace=True)
            self.log("  Cabin    -> replaced by HasCabin (0/1) and Deck; Cabin dropped")
        for col in list(df.columns[df.isnull().any()]):  # any other columns with gaps
            if df[col].isnull().mean() > 0.6:
                df.drop(columns=[col], inplace=True)
                self.log(f"  {col} -> dropped (more than 60 % missing)")
            elif pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
                self.log(f"  {col} -> filled with median")
            else:
                df[col] = df[col].fillna(df[col].mode()[0])
                self.log(f"  {col} -> filled with mode")
        self.df = df
        self.log(f"  Missing cells now: {int(df.isnull().sum().sum())}")
        self.show_table(self.df, "After handling missing values")
        self.update_status()

    def step_verify(self):
        if not self.need_data():
            return
        before = self.raw.isnull().sum()
        after = self.df.isnull().sum().reindex(self.raw.columns, fill_value=0)
        cols = before[before > 0].index
        self.log("-" * 60)
        self.log("STEP 5: Missing values AFTER cleaning")
        self.log(f"  {'Column':<12s} {'Before':>7s} {'After':>7s}")
        for c in cols:
            self.log(f"  {c:<12s} {int(before[c]):>7d} {int(after[c]):>7d}")
        total = int(self.df.isnull().sum().sum())
        self.log(f"  Total missing cells now: {total}")
        if total == 0:
            self.log("  No missing values remain.")
        ids = self.sample_ids()
        if ids and "PassengerId" in self.df.columns:
            self.show_table(self.df[self.df["PassengerId"].isin(ids)],
                            "AFTER cleaning - the same sample rows")

        def paint(fig):
            ax1 = fig.add_subplot(1, 2, 1)
            x = np.arange(len(cols))
            b1 = ax1.bar(x - 0.2, before[cols], 0.4, label="Before", color=RED)
            b2 = ax1.bar(x + 0.2, after[cols], 0.4, label="After", color=GREEN)
            ax1.bar_label(b1, color=TEXT)
            ax1.bar_label(b2, color=TEXT)
            ax1.set_xticks(x)
            ax1.set_xticklabels(cols)
            ax1.set_title("Missing values: before vs after", weight="bold")
            ax1.legend()
            self.draw_heatmap(fig.add_subplot(1, 2, 2), self.df, "Missing map - AFTER cleaning")

        self.show_chart(paint)
        self.update_status()

    def step_validate(self):
        if not self.need_data():
            return
        d = self.df
        rules = [
            ("Age between 0 and 100", "Age", lambda s: s.between(0, 100).all()),
            ("Fare is not negative", "Fare", lambda s: (s >= 0).all()),
            ("Survived only 0 or 1", "Survived", lambda s: s.isin([0, 1]).all()),
            ("Pclass only 1, 2 or 3", "Pclass", lambda s: s.isin([1, 2, 3]).all()),
            ("Sex only male/female", "Sex", lambda s: s.astype(str).str.lower().isin(["male", "female"]).all()),
            ("PassengerId is unique", "PassengerId", lambda s: s.is_unique),
        ]
        self.log("-" * 60)
        self.log("STEP 6: Consistency checks")
        for name, col, rule in rules:
            if col in d.columns:
                self.log(f"  {name:<26s} -> {'PASS' if bool(rule(d[col])) else 'FAIL'}")
        if "Fare" in d.columns:
            self.log(f"  Passengers with Fare = 0: {int((d['Fare'] == 0).sum())} (kept: crew / staff)")

    def step_standardise(self):
        if not self.need_data():
            return
        df = self.df
        self.log("-" * 60)
        self.log("STEP 7: Standardise text, fix data types, derive features")
        for c in df.columns:
            if pd.api.types.is_string_dtype(df[c]) and not isinstance(df[c].dtype, pd.CategoricalDtype):
                df[c] = df[c].str.strip()
        if "Name" in df.columns:
            df["Name"] = df["Name"].str.replace(r"\s+", " ", regex=True)
            df["Title"] = df["Name"].str.extract(r",\s*([^.]+)\.", expand=False).str.strip()
            df["Title"] = df["Title"].replace({"Mlle": "Miss", "Ms": "Miss", "Mme": "Mrs"})
            df["Title"] = df["Title"].where(df["Title"].isin(["Mr", "Mrs", "Miss", "Master"]), "Other")
            self.log("  Title extracted from Name (Mr, Mrs, Miss, Master, Other)")
        if "Sex" in df.columns:
            df["Sex"] = df["Sex"].astype(str).str.strip().str.title()
            self.log("  Sex written in title case")
        if "Embarked" in df.columns:
            df["Embarked"] = df["Embarked"].astype(str).replace(
                {"C": "Cherbourg", "Q": "Queenstown", "S": "Southampton"})
            self.log("  Embarked codes replaced by port names")
        if {"SibSp", "Parch"}.issubset(df.columns):
            df["FamilySize"] = df["SibSp"] + df["Parch"] + 1
            df["IsAlone"] = (df["FamilySize"] == 1).astype(int)
            self.log("  FamilySize and IsAlone created")
        for c in ["Sex", "Embarked", "Deck", "Title"]:
            if c in df.columns:
                df[c] = df[c].astype("category")
        for c in ["Survived", "Pclass", "SibSp", "Parch", "HasCabin", "FamilySize", "IsAlone"]:
            if c in df.columns:
                df[c] = df[c].astype("int8")
        self.log("  Data types corrected (category / int8)")
        self.df = df
        self.show_table(self.df, "After standardising text and data types")
        self.update_status()

    def step_outliers(self):
        if not self.need_data():
            return
        df = self.df
        self.log("-" * 60)
        self.log("STEP 8: Outliers (IQR method)")
        for col in ["Age", "Fare"]:
            if col in df.columns:
                q1, q3 = df[col].quantile([0.25, 0.75])
                iqr = q3 - q1
                low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                n = int(((df[col] < low) | (df[col] > high)).sum())
                self.log(f"  {col:<5s}: valid range [{low:.2f}, {high:.2f}] -> {n} outliers")
        if "Fare" not in df.columns:
            return
        q1, q3 = df["Fare"].quantile([0.25, 0.75])
        high = q3 + 1.5 * (q3 - q1)
        df["Fare_Capped"] = df["Fare"].clip(lower=0, upper=high)
        self.log(f"  Fare_Capped created: max {df['Fare'].max():.2f} -> {df['Fare_Capped'].max():.2f}")
        self.log("  (Age outliers are real ages, so they are kept.)")

        def boxplot(ax, data, color):
            ax.boxplot(data, patch_artist=True,
                       boxprops=dict(facecolor=color, edgecolor=color, alpha=0.55),
                       medianprops=dict(color=AMBER, linewidth=2),
                       whiskerprops=dict(color=TEXT), capprops=dict(color=TEXT),
                       flierprops=dict(markerfacecolor=color, markeredgecolor=color, markersize=4))

        def paint(fig):
            a1 = fig.add_subplot(1, 2, 1)
            boxplot(a1, df["Fare"], RED)
            a1.set_title("Fare - BEFORE capping", weight="bold")
            a2 = fig.add_subplot(1, 2, 2, sharey=a1)
            boxplot(a2, df["Fare_Capped"], GREEN)
            a2.set_title("Fare_Capped - AFTER capping", weight="bold")

        self.show_chart(paint)
        self.update_status()

    # ------------------------------------------------------------- actions
    def run_all(self):
        self.step_load()
        if self.df is None:
            return
        for step in (self.step_detect, self.step_duplicates, self.step_handle, self.step_verify,
                     self.step_validate, self.step_standardise, self.step_outliers):
            step()
            self.update_idletasks()
        self.log("-" * 60)
        self.log("All steps finished. Use 'SAVE CLEANED CSV' to export the result.")
        self.tabs.select(2)

    def save_csv(self):
        if not self.need_data():
            return
        out_dir = os.path.dirname(DEFAULT_OUT)
        path = filedialog.asksaveasfilename(
            title="Save cleaned dataset", defaultextension=".csv",
            initialdir=out_dir if os.path.isdir(out_dir) else BASE,
            initialfile="titanic_cleaned.csv", filetypes=[("CSV files", "*.csv")])
        if path:
            self.df.to_csv(path, index=False)
            self.log(f"Saved cleaned dataset -> {path}")
            messagebox.showinfo("Saved", f"Cleaned dataset saved:\n{path}")


if __name__ == "__main__":
    CleaningApp().mainloop()
