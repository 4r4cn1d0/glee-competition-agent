# Camera-ready artifact release plan

Decision: use the narrow aggregate-first verification bundle at review time and
target a sanitized production-equivalent source release at camera ready. The
second step remains conditional on licensing, privacy, and data-use permission;
it is not claimed as completed evidence in the submission.

Target: publish a frozen, sanitized artifact with the camera-ready paper, due
November 20, 2026 if accepted. The operational development repository remains
private until this release is prepared and verified.

## Separate anonymous review artifact

The submission-time review bundle is not a copy of this camera-ready package.
It is aggregate-first and contains a standalone executable specification of
effective behavior, synthetic fixtures, deidentified released tables,
mathematical checks, and figure and table generators. It excludes raw
production source, the 81-key private overlay, fleet controls, dormant arms,
private manifests, logs, transcripts, messages, game and profile identifiers,
timestamps, process metadata, internal paths, and repository history. Reviewers
can reproduce released arithmetic, figures, tables, mathematical identities,
and synthetic policy behavior. They cannot independently reclassify withheld
messages, re-audit private joins or game-hash assignment, observe
counterfactual opponent responses, or prove equivalence to the withheld
production source.

This boundary prevents a review artifact from becoming an operational
competition deployment. The current OpenReview form exposes no separate
artifact field. Publish or transmit this archive only through an
organizer-approved review channel, without repository metadata; otherwise keep
it local and do not imply that reviewers received it.

## Release contents

- Final deterministic policy source used by the submitted agent.
- A non-operational snapshot of the effective bank configuration.
- The frozen `submitted_agent_bank_manifest.csv` receipt, with its source
  commit, configuration hashes, era boundaries, 81 recorded overlay flags, and
  behavior-affecting defaults absent from the overlay.
- The ordered `submitted_policy_asset_manifest.csv` receipt with 23 policy and
  fitted-model paths and their individual SHA-256 values.
- A documented public alias for internal profile-specific flag names, including
  every profile-specific private key, while retaining a private
  checksum-preserving map for independent verification.
- Python and system dependency locks sufficient to rebuild the paper and run
  the released checks.
- Theory-to-code verifier, reachability checks, and deidentified analysis
  scripts.
- Artifact-manifest verifier for the policy, fitted models, overlay, and
  behavior-affecting defaults.
- Figure and table generators with their released input tables.
- The deidentified persuasion-parser coverage table and read-only analyzer;
  raw messages remain withheld, so the public table verifies reported
  arithmetic but not independent semantic relabeling.
- Deidentified clone checkpoint, rating checkpoints, a public experiment
  registry, and derived non-identifying aggregates.
- The theory, code, and evidence audit in
  `paper/review/theory_code_audit.md`.
- Build instructions, license, data-access statement, and a frozen release tag.

## Material withheld

- API keys, tokens, `.env`, and credentials.
- Operational fleet controls, rollout files, host details, and process records.
- Raw logs and competition transcripts.
- Game IDs, opponent names or public IDs, timestamps that permit linkage, and
  other direct or quasi-identifiers.
- Private research ledgers when their free text could expose withheld material.
  Their relevant evidence will appear as derived tables with documented
  transformations.
- Internal review scaffolds and peer-review notes. Do not copy
  `paper/review/` wholesale into the release.

## Reproducibility boundary

The artifact must reproduce the reported calculations, paper figures, table
counts, and deterministic policy checks. It cannot replay the private live
field, reconstruct unobserved counterfactual responses, or re-audit server
receipt for games whose joined records are withheld. The paper must retain this
boundary explicitly.

## Pre-release checks

- Replace the author placeholder and provide the public agent ID in the
  submission form. The manuscript need not expose internal fleet labels.
- Freeze the exact release commit and record its checksum.
- Confirm licenses for code, data, template assets, and generated figures.
- Scan the complete artifact for secrets and identifiers.
- Generate a public registry table that replaces private `.ai` paths with
  stable release source IDs and checksums of sanitized evidence excerpts or
  derived records. Do not ship the private working-tree crosswalk.
- Release only `paper/review/theory_code_audit.md` from the working review
  directory, after the same identifier and secret scan.
- Verify that the effective configuration snapshot cannot control a live fleet.
- Run the theory verifier, analysis scripts, figure generators, LaTeX build, and
  test suite from a clean environment.
- Confirm that released aggregates reproduce every number claimed as
  reproducible in the paper.
- Obtain the required organizer or institutional determination for interactions
  with possible human opponents.
