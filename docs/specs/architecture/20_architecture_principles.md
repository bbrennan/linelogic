# Architecture Principles: SOLID + KISS

This document captures practical guidelines to ensure our data ingest pipelines and model workflows remain robust, testable, and simple.

## Goals
- Rock-solid data ingest for both training and inference
- Clear boundaries between layers (providers → contracts → validation → features → models → apps)
- Easy to extend without breaking existing behavior

## Layered Structure
- Data Providers: External APIs (balldontlie, odds). Responsibilities: HTTP, rate limiting, caching, normalization.
- Contracts: Pydantic models defining exact shapes (`Team`, `Game`, `TeamSeasonStats`).
- Validation: Utilities to enforce contracts and sanity checks before downstream use.
- Ingest Pipeline: Orchestrated fetch→normalize→validate→persist manifests; idempotent and traceable.
- Features: Pure transformation from validated inputs → feature vectors for training/inference.
- Models: Train, evaluate, and persist artifacts; avoid coupling to providers.
- Apps: CLI, Streamlit, email—consume models/outputs only.

## SOLID
- Single Responsibility: Each module focuses on one concern (e.g., provider vs validator vs feature).
- Open/Closed: Add new providers/endpoints without modifying consumer code by honoring contracts.
- Liskov Substitution: Providers should adhere to common interfaces; swapping is safe.
- Interface Segregation: Define narrow interfaces (e.g., `GamesProvider`, `TeamsProvider`) instead of one giant client.
- Dependency Inversion: High-level modules (feature engineering, inference) depend on contracts/interfaces, not concrete providers.

### Action Items
- Introduce provider interface(s) and inject into `FeatureEngineer` and `DailyInferenceEngine`.
- Enforce input validation at ingest boundaries; reject malformed payloads early.
- Keep feature engineering stateless/pure for inference paths.

## KISS
- Prefer small modules and composable functions.
- Avoid deep inheritance; use composition.
- Make failure modes explicit with clear logs and safe fallbacks.

## Microservices?
- Current repo is a modular monolith. True microservices add operational complexity (deployment, observability, networking).
- Recommendation: Keep modular boundaries and clear interfaces, introduce services only when scale or team size demands.

## Observability & Manifests
- Persist ingest manifests (*.json) with counts and validation errors for auditing.
- Add CI checks to fail on contract violations.

## Testing Guidance
- Unit tests for validators and feature extraction.
- Integration tests for ingest pipeline against free-tier endpoints (teams/games).
- Smoke tests for inference outputs format.
