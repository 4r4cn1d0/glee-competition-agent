# Anonymous review artifact

This is a local, nonoperational review bundle for the competition paper. It
contains aggregate tables, a pure reference implementation of selected policy
rules, synthetic test vectors, and safe figure generators. The operational
repository remains private. Nothing in this directory connects to a service,
reads process state, or changes a live agent.

## One-command verification

Use Python 3.9 or later. Install the two pinned plotting dependencies in an isolated
environment, then run the verifier from this directory:

```sh
python3 -m venv ../review-artifact-venv
../review-artifact-venv/bin/python -m pip install -r requirements.lock
../review-artifact-venv/bin/python verify_all.py
```

The final command performs all of the following:

1. Enforces a closed file allowlist and rejects symbolic links.
2. Verifies every file against `MANIFEST.sha256`.
3. Scans text for credentials, remote addresses, absolute machine paths,
   wall-clock records, source-only namespaces, and common identifier forms.
4. Runs the mathematical and synthetic-policy checks.
5. Recomputes aggregate tables, including the 91-row randomized checkpoint,
   official final display values, and the complete two-window final-policy
   census.
6. Regenerates all four figures in a temporary directory and checks their
   dimensions against the included visual references.

Expected final line:

```text
verify_all: PASS
```

## Package map

- `policy/` contains a declarative policy excerpt, pure reference functions,
  and synthetic test vectors.
- `analysis/` contains standard-library arithmetic and table checks.
- `data/` contains deidentified or aggregate-only inputs.
- `figures/` contains safe generators and expected visual outputs.
- `tables/` contains deterministic rendered-table outputs.

The package intentionally excludes production source, fitted production
models, operational configuration, raw messages, full trajectories, external
review notes, and manuscript build products. See
`REPRODUCIBILITY_BOUNDARY.md` for the precise claim boundary and `LICENSES.md`
for unresolved release conditions.

The four strict semantic-parser warnings are released only for the audited
pre-close persuasion subcohort. They are not represented as a parser audit of
the complete final-policy census.

A container recipe is not included in this review bundle. The executable
artifact is pure Python except for plotting, and the two direct plotting
dependencies are pinned. A public release should add a frozen transitive
environment only after its licensing and redistribution terms are settled.
