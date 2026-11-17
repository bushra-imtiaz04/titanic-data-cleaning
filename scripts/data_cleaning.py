"""
Data Cleaning Project - Titanic Passenger Dataset
-------------------------------------------------
Cleans the Kaggle / Data Science Dojo Titanic dataset step by step:
missing values, duplicates, consistency checks, text standardisation,
data types and outliers.

Run from the project root:
    python scripts/data_cleaning.py
"""

# %% HELPERS (plotting utilities, not part of the cleaning logic)
import os
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BEFORE_COLOR = "#C0392B"
AFTER_COLOR = "#1E8449"
HEADER_COLOR = "#1F3A5F"


def save_table_image(frame, path, title):
    """Render a small DataFrame as a picture; empty (NaN) cells are shaded red."""
    text = frame.astype(object).where(frame.notnull(), "NaN").astype(str).values
    colors = np.where(frame.isnull().values, "#F5B7B1", "white").tolist()
    fig, ax = plt.subplots(figsize=(1.6 * frame.shape[1], 0.5 * (len(frame) + 1.5)))
    ax.axis("off")
    tbl = ax.table(cellText=text, colLabels=list(frame.columns), cellColours=colors,
                   loc="upper center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.5)
    for (row, _), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_facecolor(HEADER_COLOR)
            cell.set_text_props(color="white", weight="bold")
    ax.set_title(title, fontsize=12, weight="bold", pad=10)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_missing_heatmap(frame, path, title):
    """Draw every cell of the dataset: red = missing, white = present."""
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.imshow(frame.isnull().values, aspect="auto", cmap="Reds",
              interpolation="nearest", vmin=0, vmax=1)
    ax.set_xticks(range(frame.shape[1]))
    ax.set_xticklabels(frame.columns, rotation=45, ha="right")
    ax.set_ylabel("Row index")
    ax.set_title(title, fontsize=12, weight="bold")
    if frame.isnull().sum().sum() == 0:
        ax.text(0.5, 0.5, "No missing values", transform=ax.transAxes, ha="center",
                va="center", fontsize=18, weight="bold", color=AFTER_COLOR,
                bbox=dict(facecolor="white", edgecolor=AFTER_COLOR, boxstyle="round,pad=0.6"))
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


# %% STEP 1: Import libraries and load the dataset
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 100)
pd.set_option("display.max_colwidth", 12)

DATA_PATH = "data/titanic.csv"
CLEAN_PATH = "data/titanic_cleaned.csv"
IMG_DIR = "images"
os.makedirs(IMG_DIR, exist_ok=True)

df = pd.read_csv(DATA_PATH)
raw = df.copy()  # untouched copy, used later for before/after comparison

print("Dataset loaded successfully")
print("Rows:", df.shape[0], "| Columns:", df.shape[1])


# %% STEP 2: Initial data exploration
print(df.head())
print()
df.info()
print()
print(df.describe().round(2))


# %% STEP 3: Detect missing values (BEFORE cleaning)
missing_before = df.isnull().sum()
missing_pct = (missing_before / len(df) * 100).round(2)

report = pd.DataFrame({"Missing Values": missing_before,
                       "Percentage (%)": missing_pct})
print(report[report["Missing Values"] > 0])
print("\nTotal missing cells:", int(missing_before.sum()))


# %% STEP 4: Visualise the missing values (BEFORE cleaning)
# Same passengers are shown before and after cleaning (2 missing Embarked + 6 missing Age)
sample_ids = (list(df.loc[df["Embarked"].isnull(), "PassengerId"])
              + list(df.loc[df["Age"].isnull(), "PassengerId"].head(6)))

before_cols = ["PassengerId", "Pclass", "Sex", "Age", "Cabin", "Embarked"]
sample_before = df.loc[df["PassengerId"].isin(sample_ids), before_cols]

save_table_image(sample_before, f"{IMG_DIR}/table_before.png",
                 "BEFORE cleaning - rows with missing values (red = NaN)")
save_missing_heatmap(df, f"{IMG_DIR}/heatmap_before.png",
                     "Missing values map - BEFORE cleaning")
print(sample_before.to_string(index=False))


# %% STEP 5: Check for duplicate values
dup_rows = int(df.duplicated().sum())
dup_ids = int(df["PassengerId"].duplicated().sum())
shared_tickets = int(df["Ticket"].duplicated().sum())

print("Fully duplicated rows  :", dup_rows)
print("Duplicate PassengerId  :", dup_ids)
print("Repeated ticket numbers:", shared_tickets, "(group bookings, not errors)")

if dup_rows == 0:
    print("\nNo duplicate values found - nothing to remove.")
else:
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"\nRemoved {dup_rows} duplicate rows.")


# %% STEP 6: Handle the missing values
# Embarked: only 2 missing -> fill with the most frequent port (mode)
embarked_mode = df["Embarked"].mode()[0]
df["Embarked"] = df["Embarked"].fillna(embarked_mode)

# Age: fill with the median age of passengers in the same class and sex
df["Age"] = df["Age"].fillna(df.groupby(["Pclass", "Sex"])["Age"].transform("median"))

# Cabin: ~77% missing -> too sparse to fill, so keep the information as two features
df["HasCabin"] = df["Cabin"].notnull().astype(int)
df["Deck"] = df["Cabin"].str[0].fillna("Unknown")
df = df.drop(columns=["Cabin"])

print("Embarked filled with:", embarked_mode)
print("Median age used per group:")
print(raw.groupby(["Pclass", "Sex"])["Age"].median())


# %% STEP 7: Verify - missing values (AFTER cleaning)
after_cols = ["PassengerId", "Pclass", "Sex", "Age", "HasCabin", "Deck", "Embarked"]
sample_after = df.loc[df["PassengerId"].isin(sample_ids), after_cols]

save_table_image(sample_after, f"{IMG_DIR}/table_after.png",
                 "AFTER cleaning - same rows, no missing values")
save_missing_heatmap(df, f"{IMG_DIR}/heatmap_after.png",
                     "Missing values map - AFTER cleaning")

comparison = pd.DataFrame({
    "Before": raw.isnull().sum(),
    "After": df.isnull().sum().reindex(raw.columns, fill_value=0),  # Cabin replaced by Deck/HasCabin
})
print(comparison[comparison["Before"] > 0])
print("\nTotal missing cells now:", int(df.isnull().sum().sum()))

# grouped bar chart: before vs after
cols = comparison.index[comparison["Before"] > 0]
x = np.arange(len(cols))
fig, ax = plt.subplots(figsize=(7, 4.5))
b1 = ax.bar(x - 0.2, comparison.loc[cols, "Before"], 0.4, label="Before", color=BEFORE_COLOR)
b2 = ax.bar(x + 0.2, comparison.loc[cols, "After"], 0.4, label="After", color=AFTER_COLOR)
ax.bar_label(b1)
ax.bar_label(b2)
ax.set_xticks(x)
ax.set_xticklabels(cols)
ax.set_ylabel("Missing values")
ax.set_title("Missing values per column: before vs after", weight="bold")
ax.legend()
fig.tight_layout()
fig.savefig(f"{IMG_DIR}/missing_counts_before_after.png", dpi=200)
plt.close(fig)


# %% STEP 8: Validate data consistency
checks = {
    "Age between 0 and 100": df["Age"].between(0, 100).all(),
    "Fare is not negative": (df["Fare"] >= 0).all(),
    "Survived only 0 or 1": df["Survived"].isin([0, 1]).all(),
    "Pclass only 1, 2 or 3": df["Pclass"].isin([1, 2, 3]).all(),
    "Sex only male/female": df["Sex"].str.lower().isin(["male", "female"]).all(),
    "Embarked only C, Q or S": df["Embarked"].isin(["C", "Q", "S"]).all(),
    "PassengerId is unique": df["PassengerId"].is_unique,
}
for name, passed in checks.items():
    print(f"{name:26s} -> {'PASS' if bool(passed) else 'FAIL'}")

print("\nPassengers with Fare = 0:", int((df["Fare"] == 0).sum()), "(kept: crew / staff tickets)")


# %% STEP 9: Standardise text, fix data types and derive features
for col in ["Name", "Sex", "Ticket", "Embarked", "Deck"]:
    df[col] = df[col].str.strip()

df["Name"] = df["Name"].str.replace(r"\s+", " ", regex=True)
df["Sex"] = df["Sex"].str.title()
df["Embarked"] = df["Embarked"].map({"C": "Cherbourg", "Q": "Queenstown", "S": "Southampton"})

# Title from the name (Mr, Mrs, Miss, Master, Other)
df["Title"] = df["Name"].str.extract(r",\s*([^.]+)\.", expand=False).str.strip()
df["Title"] = df["Title"].replace({"Mlle": "Miss", "Ms": "Miss", "Mme": "Mrs"})
df["Title"] = df["Title"].where(df["Title"].isin(["Mr", "Mrs", "Miss", "Master"]), "Other")

# Family features
df["FamilySize"] = df["SibSp"] + df["Parch"] + 1
df["IsAlone"] = (df["FamilySize"] == 1).astype(int)

# Correct data types
for col in ["Sex", "Embarked", "Deck", "Title"]:
    df[col] = df[col].astype("category")
for col in ["Survived", "Pclass", "SibSp", "Parch", "HasCabin", "FamilySize", "IsAlone"]:
    df[col] = df[col].astype("int8")

print(df[["Name", "Sex", "Embarked", "Title", "FamilySize", "IsAlone"]].head())
print()
print(df.dtypes)


# %% STEP 10: Detect and treat outliers (IQR method)
def iqr_bounds(series):
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


for col in ["Age", "Fare"]:
    low, high = iqr_bounds(df[col])
    n_out = int(((df[col] < low) | (df[col] > high)).sum())
    print(f"{col:5s}: valid range [{low:.2f}, {high:.2f}] -> {n_out} outliers")

# Age outliers are real ages (up to 80) -> kept.
# Fare is heavily skewed -> cap at the upper bound in a NEW column, original kept.
low, high = iqr_bounds(df["Fare"])
df["Fare_Capped"] = df["Fare"].clip(lower=max(low, 0), upper=high)
print(f"\nMax Fare before: {df['Fare'].max():.2f} | after capping: {df['Fare_Capped'].max():.2f}")

fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
axes[0].boxplot(df["Fare"], patch_artist=True, boxprops=dict(facecolor="#F5B7B1"))
axes[0].set_title("Fare - BEFORE capping")
axes[1].boxplot(df["Fare_Capped"], patch_artist=True, boxprops=dict(facecolor="#ABEBC6"))
axes[1].set_title("Fare_Capped - AFTER capping")
axes[0].set_ylabel("Fare")
fig.tight_layout()
fig.savefig(f"{IMG_DIR}/fare_boxplot_before_after.png", dpi=200)
plt.close(fig)


# %% STEP 11: Final validation and save the cleaned dataset
import textwrap

print("Final shape            :", df.shape)
print("Missing values         :", int(df.isnull().sum().sum()))
print("Duplicate rows         :", int(df.duplicated().sum()))
print("Columns                :")
print(textwrap.fill(", ".join(df.columns), width=70))

df.to_csv(CLEAN_PATH, index=False)
print("\nCleaned dataset saved ->", CLEAN_PATH)
