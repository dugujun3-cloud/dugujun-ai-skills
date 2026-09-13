# Changelog

All notable public-repository changes are recorded here. Skill behavior changes must also identify the affected Skill.

## [Unreleased]

### Added

- Machine-readable `skills-manifest.json` with maturity and public-source status.
- Dependency-free repository validator and regression tests.
- GitHub Actions validation for pull requests and main.
- Security, contribution, Issue and Pull Request guidance.
- `user-operations-playbook` lifecycle and conversion adaptation reference with upstream MIT attribution.
- `multi-agent-division-playbook`, a **distillation** rather than a mirror: authored from internal operating rules by replacing product names with semantic role slots and private paths with abstract namespaces. No local file corresponds to it one-to-one, so upstream changes require re-distillation rather than a file-level sync — see its `references/provenance.md`.

### Changed

- Reframed the README as a public product catalog and trusted installation entrypoint.
- Shortened the `user-operations-playbook` discovery description, preserved implicit invocation, and marked its public source current after release validation.
- Marked `dugujun-account-analysis` public source current after backporting its sanitized environment-variable boundary to the local canonical source and adding a refusal regression test.

### Not changed

- No Skill runtime behavior, public method, license, Tag or Release was changed in this foundation update.
