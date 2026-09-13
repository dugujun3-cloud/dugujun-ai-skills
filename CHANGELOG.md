# Changelog

All notable public-repository changes are recorded here. Skill behavior changes must also identify the affected Skill.

## [Unreleased]

### Added

- Machine-readable `skills-manifest.json` with maturity and public-source status.
- Dependency-free repository validator and regression tests.
- GitHub Actions validation for pull requests and main.
- Security, contribution, Issue and Pull Request guidance.
- `user-operations-playbook` lifecycle and conversion adaptation reference with upstream MIT attribution.
- `dugujun-deep-research` and `claim-evidence-auditor`, published verbatim from their canonical sources. They are released as a linked pair: each references the other, so publishing either alone would leave a dangling reference. Their `references/source-map.md` files record the originating prompts and the original design decisions added on top.

### Changed

- Reframed the README as a public product catalog and trusted installation entrypoint.
- Shortened the `user-operations-playbook` discovery description, preserved implicit invocation, and marked its public source current after release validation.
- Marked `dugujun-account-analysis` public source current after backporting its sanitized environment-variable boundary to the local canonical source and adding a refusal regression test.

### Not changed

- No Skill runtime behavior, public method, license, Tag or Release was changed in this foundation update.
