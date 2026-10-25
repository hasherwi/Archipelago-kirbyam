# Kirby publication trust boundary

**Do not enable or use #993 standalone as safe publication.** Its legacy prune,
delete and clobber behavior is removed by #994. The safe publisher requires the
combined stack plus owner-verified tag/environment protections and immutable-release
enforcement. Tests must remain offline; a skipped publisher job is not evidence of
successful signing, immutable staging or publication.

Partial #982 coverage. Build outputs do not authorize publication. The writer job
requires this repository, a protected `kirbyam-v*` tag push and the `kirbyam-release`
environment. Its checkout selects main, disables persisted credentials, and executes
only main's publisher policy. That policy checks the event/ref again, requires the
tagged commit to be in main history, reads its manifest/changelog as data, and derives
all release metadata independently of build outputs. Tagged manifest versions must
already agree; automatic writer-side version-sync PRs are removed. Build jobs retain
read-only contents access; the publisher has only contents:write, no PR/OIDC rights.

## Owner configuration still required (not performed by this PR)

Protect main and release tags against unauthorized updates/deletion. Configure
kirbyam-release with required reviewers and prevent self-review; allow only approved
protected release tags. Review the exact tagged SHA and build artifact before approval.
An environment name in YAML does not establish these protections. Until these settings
are inspected and approved, end-to-end release authorization acceptance remains open.
Do not weaken the protected-ref condition to make an unconfigured repository publish.
A maintainer with workflow/settings authority remains in the trusted computing base.

The self-hosted smoke job now permits main only, with no persisted checkout credentials.
Its actual host/network isolation, ephemerality, installed runtime and cleanup have NOT
been verified. The owner must establish a dedicated isolated runner with no unrelated
credentials, restrict its runner group to reviewed workflows, and document cleanup
before treating it as safe. A main-only guard does not make arbitrary dependencies safe.
No runner, environment, repository setting, credential or trust setting was changed here.

## Remaining scope

Global full-application release permissions are outside the Kirby-only boundary.
Artifact origin, immutable publication and retry behavior are tracked separately in
#983. This change does not make builder-produced bytes independently trustworthy.
Tests use in-memory contexts and inspect workflow source; they never publish or modify
release state. Hosted tag/environment behavior still requires owner-approved validation.
