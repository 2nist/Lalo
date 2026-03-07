# Machine C: Single-Song Diagnostics

## Mission

Turn YouTube and local-song runs into reproducible diagnostic evidence.

## Lane

`single-song-diagnostics`

## Primary Scope

- one-song analysis review
- candidate log inspection
- audio health checks
- reproducible failure notes

## Must Not Touch

- detector defaults
- benchmark thresholds
- BTC runtime code

## Success Criteria

1. song source and slug are recorded
2. backend and algorithm are recorded
3. output artifacts are named and saved
4. findings become hypotheses for machine B, not direct default changes

## Preferred Outputs

- exact audio path or slug
- backend used
- algorithm used
- notable wrong boundaries
- suspected failure mode
- recommendation for benchmark lane

## Expected Artifacts

- candidate log path
- sections JSON path
- short repro note for handoff
