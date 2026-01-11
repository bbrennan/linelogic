# Architecture Refactor: Provider Injection

## Summary
Added provider protocol/interface to support dependency injection and improve testability while maintaining SOLID principles.

## Changes Made
1. **Provider Protocol** (`src/linelogic/data/provider_protocol.py`)
   - Defined `GamesProvider` and `TeamsProvider` protocols
   - Enables dependency injection and mocking for tests
   - `BalldontlieProvider` already implements these methods naturally (structural typing)

2. **Data Contracts** (`src/linelogic/data/contracts.py`)
   - Pydantic models for `Team`, `Game`, `TeamSeasonStats`
   - Strict validation with field constraints
   - Prevents invalid data from entering pipelines

3. **Validators** (`src/linelogic/data/validators.py`)
   - Functions to validate raw API responses against contracts
   - Sanity checks (team count, duplicate checks, score validation)
   - Returns both validated objects and error messages

4. **Ingest Pipeline** (`src/linelogic/ingest/pipeline.py`)
   - Orchestrates fetch→normalize→validate→persist flow
   - Generates idempotent manifests with content hashes
   - Traceable for auditing and debugging

5. **Unit Tests** (`tests/test_contracts.py`)
   - Contract validation tests
   - Validator function tests
   - Sanity check tests
   - 9 passing tests covering core validation logic

6. **CI Workflow** (`.github/workflows/ci.yml`)
   - Ingest validation job (teams + games)
   - Unit test job with pytest
   - Runs on PRs to `main` and `develop`

## Future Work
- Inject provider protocol into `FeatureEngineer` and `DailyInferenceEngine` constructors
- Add integration tests with mock providers
- Expand test coverage to feature engineering logic

## Testing
```bash
# Run unit tests
.venv/bin/pytest tests/test_contracts.py -v

# Test ingest pipeline
.venv/bin/python -c "from linelogic.ingest.pipeline import IngestPipeline; p=IngestPipeline(); print(p.ingest_current_teams())"
```

## Notes
- Provider injection can be added without breaking existing code due to structural typing
- Current implementation maintains backward compatibility
- Manifests stored in `.linelogic/manifests/` for audit trails
