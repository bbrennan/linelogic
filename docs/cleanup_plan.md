# Repo Cleanup Plan — “File Swamp” Removal

Goal: make the repository root look like a professional Python library + Streamlit app repo.

## Guardrails (non‑negotiable)
- Preserve package import paths (`src/linelogic/...`).
- Prefer `git mv` to preserve history.
- Do not delete files unless clearly redundant/obsolete; otherwise move to `docs/archive/`.

---

## Root allowlist (keep in root)
- `README.md` (front door)
- `pyproject.toml`
- `LICENSE`
- `Makefile`
- `.gitignore`, `.env.example`, `.pre-commit-config.yaml`
- `CONTRIBUTING.md`, `SECURITY.md`, `CODEOWNERS`
- `.github/` (CI)
- `src/`, `tests/`, `scripts/`, `notebooks/`, `feature_store/`

Everything else currently in root should move.

---

## Inventory + Classification Checklist

### Streamlit app
- [x] MOVE: `streamlit_app.py` → `app/app.py`
- [x] MOVE: `streamlit_app_enhanced.py` → `app/app_enhanced.py` (or `app/pages/...` if we later adopt multipage)
- [x] UPDATE: README/docs instructions to run `streamlit run app/app.py`

### Assets
- [ ] MOVE: `linelogic_logo.png` → `assets/linelogic_logo.png`
- [ ] MOVE: `LOGO_DESIGN_BRIEF.md` → `docs/specs/ui/LOGO_DESIGN_BRIEF.md`

### Roadmap / planning
- [ ] MOVE: `future-work.md` → `docs/specs/roadmap/future-work.md`

### Deployment / operations (POC package)
Move into `docs/specs/deployment/` (keep separate unless confirmed redundant):
- [ ] MOVE: `POC_DEPLOYMENT_PACKAGE.md` → `docs/specs/deployment/POC_DEPLOYMENT_PACKAGE.md`
- [ ] MOVE: `DEPLOYMENT_INDEX.md` → `docs/specs/deployment/DEPLOYMENT_INDEX.md`
- [ ] MOVE: `DEPLOYMENT_SUMMARY.md` → `docs/specs/deployment/DEPLOYMENT_SUMMARY.md`
- [ ] MOVE: `DEPLOYMENT_READY.md` → `docs/specs/deployment/DEPLOYMENT_READY.md`
- [ ] MOVE: `DEPLOYMENT_CHECKLIST.md` → `docs/specs/deployment/DEPLOYMENT_CHECKLIST.md`
- [ ] MOVE: `FINAL_LAUNCH_CHECKLIST.md` → `docs/specs/deployment/FINAL_LAUNCH_CHECKLIST.md`
- [ ] MOVE: `OPERATIONS_RUNBOOK.md` → `docs/specs/deployment/OPERATIONS_RUNBOOK.md`
- [ ] MOVE: `VALIDATION_FRAMEWORK.md` → `docs/specs/deployment/VALIDATION_FRAMEWORK.md`
- [ ] MOVE: `TRAIN_QUICK_START.md` → `docs/specs/training/TRAIN_QUICK_START.md`
- [ ] MOVE: `TRAINING_READY.md` → `docs/specs/training/TRAINING_READY.md`
- [ ] MOVE: `MODEL_TRAINING_COMPLETE.md` → `docs/status/MODEL_TRAINING_COMPLETE.md`
- [ ] MOVE: `TRAINING_COMPLETE_SUMMARY.md` → `docs/status/TRAINING_COMPLETE_SUMMARY.md`
- [ ] MOVE: `AUTOMATED_SETUP.md` → `docs/specs/setup/AUTOMATED_SETUP.md`

### MLOps / tracking
- [ ] MOVE: `MLOPS_IMPLEMENTATION.md` → `docs/specs/mlops/MLOPS_IMPLEMENTATION.md`
- [ ] MOVE: `MLOPS_QUICK_REFERENCE.md` → `docs/specs/mlops/MLOPS_QUICK_REFERENCE.md`

### UI/UX & dashboard docs
- [ ] MOVE: `UI_UX_DESIGN_SYSTEM.md` → `docs/specs/ui/UI_UX_DESIGN_SYSTEM.md`
- [ ] MOVE: `UI_UX_REDESIGN_SUMMARY.md` → `docs/specs/ui/UI_UX_REDESIGN_SUMMARY.md`
- [ ] MOVE: `DASHBOARD_BEFORE_AFTER.md` → `docs/specs/ui/DASHBOARD_BEFORE_AFTER.md`
- [ ] MOVE: `DASHBOARD_CLEANUP.md` → `docs/status/DASHBOARD_CLEANUP.md`
- [ ] MOVE: `DASHBOARD_BEFORE_AFTER.md` (already above)
- [ ] ARCHIVE: `STREAMLIT_REFRESH_INSTRUCTIONS.md` → `docs/archive/STREAMLIT_REFRESH_INSTRUCTIONS.md` (overlaps `DASHBOARD_CLEANUP.md`; keep archived for history)
- [ ] MOVE: `TABLE_DESIGN_DETAILS.md` → `docs/specs/storage/TABLE_DESIGN_DETAILS.md`

### Compliance / legal
- [ ] MOVE: `LEGAL_COMPLIANCE.md` → `docs/specs/compliance/LEGAL_COMPLIANCE.md`

### Summaries / status logs (dated)
- [ ] MOVE: `README_AUTOMATED.md` → `docs/status/2026-01-10/README_AUTOMATED.md` (sanitize personal email to placeholder)
- [ ] MOVE: `JAN_10_TEST_RESULTS.md` → `docs/status/2026-01-10/JAN_10_TEST_RESULTS.md`
- [ ] MOVE: `TEST_LOG_JAN_10.md` → `docs/status/2026-01-10/TEST_LOG_JAN_10.md`
- [ ] MOVE: `EMAIL_SETUP_COMPLETE.md` → `docs/status/EMAIL_SETUP_COMPLETE.md`
- [ ] MOVE: `ENHANCED_MODEL_SUMMARY.md` → `docs/specs/model/ENHANCED_MODEL_SUMMARY.md`
- [ ] MOVE: `QUICK_REFERENCE.md` → `docs/specs/deployment/QUICK_REFERENCE.md`

### Data / generated artifacts currently in root
These should not live in root. Move under `docs/status/2026-01-10/` for now.
- [ ] MOVE: `predictions_log.csv` → `docs/status/predictions_log.csv`
- [ ] MOVE: `predictions_test_2026_01_10.csv` → `docs/status/2026-01-10/predictions_test_2026_01_10.csv`
- [ ] MOVE: `test_live.csv` → `docs/status/2026-01-10/test_live.csv`
- [ ] MOVE: `test_predictions.csv` → `docs/status/2026-01-10/test_predictions.csv`
- [ ] MOVE: `test_predictions_fixed.csv` → `docs/status/2026-01-10/test_predictions_fixed.csv`
- [ ] MOVE: `test_predictions_final.csv` → `docs/status/2026-01-10/test_predictions_final.csv`

### ADRs
- [ ] MOVE: `adr/0001_architecture.md` → `docs/decisions/0001_architecture.md`
- [ ] MOVE: `adr/0003_provider_injection.md` → `docs/decisions/0003_provider_injection.md`
- [ ] CREATE: `docs/decisions/ADR_TEMPLATE.md`

---

## Repo structure to ensure
- `app/` (Streamlit)
- `assets/`
- `examples/`
- `docs/README.md` + subfolder READMEs
- `docs/specs/`, `docs/decisions/`, `docs/research/`, `docs/status/`, `docs/archive/`

---

## Link update plan
After moves, update:
- `README.md` repo structure section and any doc links
- Any intra-doc links pointing at old root paths
- Any scripts/docs that refer to `streamlit_app.py`

---

## Guardrail plan
- Add a check (pre-commit + CI) that fails if root contains `*.md` outside an allowlist (`README.md`, `CONTRIBUTING.md`, `SECURITY.md`).
- Add a short policy section to `CONTRIBUTING.md`.
