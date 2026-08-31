# GLEE NeurIPS 2026 competition paper

This folder is a self-contained Overleaf project containing both the
submission-safe competition paper and the longer working report.

## Overleaf settings

- Main document for submission: `main.tex`
- Compiler: pdfLaTeX
- TeX Live version: 2026, or the newest version available
- Shell escape: not required

Compiling `main.tex` produces exactly four main pages, followed by references
and the NeurIPS checklist. It is the safe default for submission. Compiling
`full_report.tex` additionally includes the technical appendix. The shared
manuscript source is `paper.tex`, and all quantitative figures are included as
vector PDFs in `figures/`.

## Before submission

Replace the `Author Name`, `Affiliation`, and `email@example.com` placeholders
in `paper.tex`. Keep the current single-blind workshop style unless the
organizers give different instructions for the camera-ready version. The
human-opponent data-use and ethics determination also remains an external
submission item.

The project intentionally excludes build logs, private review notes,
competition data, operational source code, and live-agent configuration.
