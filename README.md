# Titanic Dataset - Data Cleansing with Python

A step-by-step data cleaning project using **pandas**, **NumPy** and **Matplotlib** on the Titanic passenger dataset from Kaggle.

## What this project does

| Step | Task |
|------|------|
| 1-2 | Load the dataset and explore its structure |
| 3-4 | Detect missing values and visualise them (before cleaning) |
| 5 | Check for duplicate values (**none found**) |
| 6-7 | Handle missing values and verify (after cleaning) |
| 8 | Validate data consistency (range and value checks) |
| 9 | Standardise text, fix data types, derive features |
| 10 | Detect and treat outliers (IQR rule) |
| 11 | Final validation and save the cleaned CSV |

## Results

- Missing values: **866 -> 0** (Age 177, Cabin 687, Embarked 2)
- Duplicate rows: **0** (no duplicate values found)
- Shape: 891 x 12 -> 891 x 17 (new features: HasCabin, Deck, Title, FamilySize, IsAlone, Fare_Capped)

## Dataset

- Kaggle: https://www.kaggle.com/c/titanic/data
- CSV used: https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv

## Project structure

```
titanic-data-cleaning/
├── data/
│   ├── titanic.csv              # original dataset
│   └── titanic_cleaned.csv      # cleaned dataset
├── scripts/
│   ├── data_cleaning.py         # the cleaning code (command line)
│   ├── cleaning_gui.py          # the same cleaning with a GUI window
│   └── make_report_assets.py    # builds code/output snapshots for the report
├── images/                      # before/after figures
├── report/
│   └── Titanic_Data_Cleansing_Report.docx
├── requirements.txt
└── README.md
```

## How to run

```bash
pip install -r requirements.txt
python scripts/data_cleaning.py
```

Run it from the project root folder. The cleaned file is written to `data/titanic_cleaned.csv` and figures to `images/`.

### GUI version (no command-line output needed)

```bash
python scripts/cleaning_gui.py
```

A desktop window opens with one button per cleaning step, a data table (missing rows highlighted), charts (before/after heatmaps, bar chart, box plots), a log tab and a **Save Cleaned CSV** button. Uses Tkinter, which comes with Python on Windows.

## Author

Bushra - BSIT, University of the Punjab, Gujranwala Campus
