# GLEE competition paper

This directory contains the working NeurIPS 2026 submission draft for the First
Workshop on Interpreting Agent Behavior.

## Build

From this directory, run:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The manuscript uses the official `sglblindworkshop` option from the NeurIPS 2026
author kit. A pristine copy of that kit is retained in `official_template/`;
`neurips_2026.sty` at the directory root is the exact style file used to build
the paper.

## Submission state

- Main paper: four pages.
- References: begin on page five and do not count toward the four-page limit.
- NeurIPS paper checklist: included after the references.
- Performance numbers: protected, dated Agent 5 snapshot from August 26, 2026;
  they are described as observational and non-final.
- Remaining placeholder: author name, affiliation, and email in `main.tex`.

Before submission, replace the author placeholder and decide whether to retain
the dated snapshot or update it with the final losslessly banked competition
result. Any updated number should be rechecked against the same frozen evidence
and limitations stated in the manuscript.
