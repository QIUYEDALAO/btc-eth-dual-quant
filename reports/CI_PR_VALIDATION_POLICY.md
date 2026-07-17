# Pull Request CI Validation Policy

- Status: selective_pr_gate_pending_merge
- Scope: repository CI routing only; no research, policy, production, data, strategy, trading, or authorization change

## Decision

Exactly one workflow handles `pull_request`: `.github/workflows/pr-selective-validate.yml`.
It cancels obsolete heads, always runs the repository project Gate, compile and
secret/diff checks, and adds any stage validator changed by the pull request or
referenced by a changed workflow.

One consolidated regression workflow handles changes landing on `main` with the
same project Gate and changed-stage selection. The 60 historical stage workflows
remain available through `workflow_dispatch` for targeted diagnosis, but no
longer fan out automatically on either feature branches or `main`.

## Acceptance

- Pull-request workflows: 1.
- Automatic main-push workflows: 1.
- Historical workflows with automatic triggers: 0.
- Obsolete pull-request heads: cancelled through concurrency.
- Repository regression: retained through the consolidated `main` Gate.
- Historical stage entry points: retained through manual dispatch.
- Policy guard: `scripts/ci_pr_trigger_policy_check.py` plus unit tests.

This governance change does not alter ADR-0015 or authorize any downstream work.
