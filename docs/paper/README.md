# Paper build

The repository contains a reproducible paper-style technical report.

## Generated artifact

`chatgpt-recovery-dynamics-paper.pdf`

## Source of numbers

The builder reads only published derived reference JSON:

- data/summary.json
- data/transition_biopsy_reference.json
- data/deep_validation_reference.json
- data/server_congestion_reference.json

No raw HAR or private data is used.

## Build

~~~bash
python -m pip install reportlab pypdf
python scripts/build_paper_pdf.py
~~~

The GitHub Actions workflow validates the PDF with pypdf, renders every page with
Poppler, and uploads the PDF plus rendered preview pages as a reviewable Actions
artifact. It does **not** push generated PDF bytes to `main` automatically.

After review, a selected PDF candidate can be committed on a separate branch and
merged deliberately.

The Markdown companion is PAPER.md.
