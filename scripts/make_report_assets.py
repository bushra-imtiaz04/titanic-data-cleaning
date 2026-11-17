"""
Runs scripts/data_cleaning.py step by step and produces:
  - report/assets/step_XX_code.png    (code snapshot)
  - report/assets/step_XX_output.png  (console-output snapshot)
  - report/assets/step_XX_output.txt  (raw output text)
Run from the project root:  python scripts/make_report_assets.py
"""
import contextlib
import io
import os
import re

from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import PythonLexer

SRC = "scripts/data_cleaning.py"
OUT = "report/assets"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
os.makedirs(OUT, exist_ok=True)

source = open(SRC, encoding="utf-8").read()
parts = re.split(r"(?m)^(?=# %% )", source)
chunks = [p for p in parts if p.startswith("# %% ")]


def code_image(code, path):
    fmt = ImageFormatter(font_name="DejaVu Sans Mono", font_size=17, line_numbers=True,
                         style="friendly", image_pad=16, line_number_pad=10,
                         line_number_bg="#EEF1F5", line_number_fg="#6B7785")
    with open(path, "wb") as fh:
        fh.write(highlight(code.rstrip() + "\n", PythonLexer(), fmt))


def output_image(text, path, title="Console output"):
    font = ImageFont.truetype(MONO, 16)
    bold = ImageFont.truetype(MONO_BOLD, 14)
    lines = text.rstrip().split("\n") or [""]
    char_w = font.getlength("M")
    line_h = 22
    width = int(max(len(l) for l in lines) * char_w) + 40
    width = max(width, 420)
    bar_h = 30
    height = bar_h + line_h * len(lines) + 30
    img = Image.new("RGB", (width, height), "#1E2430")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, bar_h], fill="#2D3646")
    for i, c in enumerate(["#E5574D", "#E5B84D", "#58B368"]):
        d.ellipse([12 + i * 20, 9, 24 + i * 20, 21], fill=c)
    d.text((80, 7), title, font=bold, fill="#C9D1DE")
    y = bar_h + 15
    for line in lines:
        d.text((20, y), line, font=font, fill="#E6EDF3")
        y += line_h
    img.save(path)


ns = {"__name__": "__main__"}
step_no = 0
for chunk in chunks:
    header = chunk.split("\n", 1)[0]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(chunk, SRC, "exec"), ns)
    if "HELPERS" in header:
        continue
    step_no += 1
    tag = f"step_{step_no:02d}"
    code_image(chunk, f"{OUT}/{tag}_code.png")
    output = buf.getvalue()
    open(f"{OUT}/{tag}_output.txt", "w", encoding="utf-8").write(output)
    if output.strip():
        output_image(output, f"{OUT}/{tag}_output.png")
    print(f"{tag}: {header[5:]}  ({len(output.splitlines())} output lines)")
