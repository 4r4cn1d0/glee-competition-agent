# Evidence dossier receipt

Status: private internal receipt, not manuscript text

Captured: 2026-08-31T11:34:35Z

Repository `HEAD`: `ead108352449089a32c0f6805479940052c99be1`

The working tree contained 90 modified, deleted, or untracked entries at the
capture time. These hashes identify exact file contents. They are not a clean
commit receipt and do not imply that every file was tracked by Git.

## Dossier files

| File | SHA-256 |
|---|---|
| `paper/evidence_dossier/GLEE_PROJECT_EVIDENCE_DOSSIER.md` | `1e5fe1bf44bf69da9963055341f95d6715f20f07b470912575ea2505e17e117c` |
| `paper/evidence_dossier/AGENT5_ONLY_PAPER_SCOPE.md` | `86bcec65f988aee31169d365354126b3e1033d310cf537c2d37fbe5439ddb739` |
| `paper/evidence_dossier/OFFICIAL_FINAL_WINDOW_EXPORT.md` | `73bc10036a0df695ae4781d653dd6d1af382c4042234a6c1b924cf9eb7a011e7` |
| `paper/evidence_dossier/source_notes/conversation_history.md` | `2cf0e21113404f270f053620eb80a873f1ef3c606b0e60d15bdd03914637c3db` |
| `paper/evidence_dossier/source_notes/data_logs_and_conformance.md` | `dc876a7e85096434199b583538536aab7bfe909c3010a3494e6773eee6347c4e` |
| `paper/evidence_dossier/source_notes/timeline_and_decisions.md` | `47b12a4d10c63d9b1930cca401f2ff376b8b7be2574e42033d180646b8f8b551` |

The receipt does not hash itself. If any dossier file changes, regenerate this
table before calling the package frozen.

## Operational ledgers at capture

| File | SHA-256 |
|---|---|
| `.ai/CURRENT_STATE.md` | `c0e96a905ff8b9b354cac405e1af001846295023f910126b59e2c3bb08ad40b1` |
| `.ai/FINDINGS.md` | `93cdf2b07a6ddc1c1970db98e9d80d2d4878a5f4b1a72e5c5ffe7803e97d98fa` |
| `.ai/EXPERIMENTS.md` | `ef34830fb18ccd319b0e41e4eb473f694623ad9c3b10f903b7ac6258c555169e` |
| `.ai/HANDOFF.md` | `06b9b08fd1e0645aff792622445b44770be44e607656271b25347401af991f27` |

These hashes provide a stable target for the source-note line locators. Future
citations should name the hash plus a dated event key, because line numbers in a
later ledger revision can drift.

## Manuscript and frozen paper data at capture

| File | SHA-256 |
|---|---|
| `paper/main.tex` | `8be72d8248f287cd0a47cc4c25d10ee80697f23f0582b674c3c751f788d4f894` |
| `paper/appendix.tex` | `3fef27c5d54d89983e442fc5994acf81bae3bc1c55da81d4bf0cb3bdf3216b6c` |
| `paper/data/submitted_agent_leaderboard_snapshot.csv` | `fb02ed03b0ea57c7a456a2c940afe9c9f910cfc55bb579921dd561a2eede1dcc` |
| `paper/data/final_policy_era_census.csv` | `d5cebc8f7b827c470faf43746048351d2448d0487865546a568eb9b65e5b290c` |
| `paper/data/final_policy_two_window_census.csv` | `13bde10d17f6ec2bae73019da744a514b28a8b087be0700fe49c965936205e5a` |
| `paper/data/submitted_agent_bank_manifest.csv` | `5ac02a61fc75844693e5a7e2f70cc91aed5c55698df4c563abdfcc2fa4754bd5` |
| `paper/data/log_archive_coverage.csv` | `6726bcddc1a771c902b251ad6217d995808a7afc5e97b13622d3edd0975a3b48` |
| `paper/data/final_window_outcome_summary.csv` | `3f638cc40bc45c2996929685cbc18dbf2f6fa7c3951e676696015f699c00f190` |
| `paper/data/final_window_official_export_manifest.csv` | `8548dcafc9a90a80216afd2c341580b0cd7daedc2207e63483005183bc639817` |
| `paper/analysis/analyze_final_window_outcomes.py` | `1cb900d4d3a15b0340fb1f0bbfd423715820d932207fc895aec91755bf6d4edf` |

The `log_archive_coverage.csv` hash preserves a stale evidence object, not an
endorsed result. Its 99.44 percent interpretation mixes local terminal
assignments with official rated games and is invalid. The corrected conditional
comparison is documented in the data source note.

The manuscript files were revised after the original dossier pass to include
the authenticated final-window replay receipt and official displayed rating
changes. The raw replay JSON is intentionally absent from this repository.
Its private source hash is recorded in
`paper/data/final_window_official_export_manifest.csv` and
`OFFICIAL_FINAL_WINDOW_EXPORT.md`.

## Controlling review snapshot

| File | SHA-256 |
|---|---|
| `paper/review/harsh_review_2026-08-30/editorial_decision.md` | `3827565facc095e79c4b1ecf1d8b4f72da9dfef038a63bc324b48e0c345e273f` |
| `paper/review/harsh_review_2026-08-30/revision_roadmap.md` | `3a1103034fe165f522eec886b25d08edfbe0762e66bbcf18373133ed4c80977e` |

The review predates the corrected lifetime denominator audit. Any review claim
using 248 missing records, 263 missing terminals, or 99.44 percent coverage is
superseded by this dossier.

## Count receipt

The exact read-only command is recorded under "Focal canonical statuses" in
`source_notes/data_logs_and_conformance.md`. At capture it returned:

```text
  15 active null
22999 completed agreement
15306 completed completed
 5597 completed no_deal
 2177 completed walked_away
    1 no_deal invalid_moves_exceeded
  221 no_deal timeout
```

The completed rows sum to 46,079. All local rows sum to 46,316. The public
rated-game total is 46,564. A 485-count rated gap and 98.96 percent local rated
coverage follow only if each completed local row maps one-to-one to a public
rated increment.

## Coverage limitation

The current Paper task was available as active conversation context but was not
exported as an immutable turn archive. Its editorial requirements are summarized
in the private conversation source note, but they do not yet have a separate
content-addressed task receipt.

The conversation and timeline notes contain private absolute paths, opaque task
or message identifiers, short directives, and competitor handles. Keep the
entire `paper/evidence_dossier/` directory out of public, reviewer, Overleaf, and
shared Git bundles until it has been deliberately redacted.
