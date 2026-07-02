# CI CD Failure Cases

## Build Failed

CI build failures usually come from dependency resolution, test failure, missing environment variables, or incompatible runtime versions.

Recommended checks:

- Read the failed job log first.
- Compare package lock or dependency changes.
- Confirm build image and runtime version.
- Re-run only after identifying whether the failure is flaky or deterministic.

## Deployment Job Failed

If the deploy job failed after artifact upload, inspect credentials, target namespace, rollout status, and health check timeout.
