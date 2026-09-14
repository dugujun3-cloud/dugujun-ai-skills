# Changelog

All notable public-repository changes are recorded here. Skill behavior changes must also identify the affected Skill.

## [Unreleased]

### Added

- `field-before-effort`：普通人决策顺序（场先于功），从公开讨论蒸馏，去掉违法/偏激路径。
- Machine-readable `skills-manifest.json` with maturity and public-source status.
- Dependency-free repository validator and regression tests.
- GitHub Actions validation for pull requests and main.
- Security, contribution, Issue and Pull Request guidance.
- `user-operations-playbook` lifecycle and conversion adaptation reference with upstream MIT attribution.
- `dugujun-deep-research` and `claim-evidence-auditor`, a linked pair (each references the other, so publishing either alone would leave a dangling reference). Published with their internal provenance codes and private-environment references removed before release.
- `pre-publish-polish-review`, `solo-business-review` and `knowledge-product-builder`: three further **distillations** from the same internal corpus. Each was rewritten for public use rather than copied — product names replaced by semantic role slots, private paths removed, and internal tool dependencies dropped so the Skills stand alone.
- `multi-agent-division-playbook`, a **distillation** rather than a mirror: authored from internal operating rules by replacing product names with semantic role slots and private paths with abstract namespaces. No local file corresponds to it one-to-one, so upstream changes require re-distillation rather than a file-level sync — see its `references/provenance.md`.

### Changed

- Reframed the README as a public product catalog and trusted installation entrypoint.
- Shortened the `user-operations-playbook` discovery description, preserved implicit invocation, and marked its public source current after release validation.
- Marked `dugujun-account-analysis` public source current after backporting its sanitized environment-variable boundary to the local canonical source and adding a refusal regression test.

### Not changed

- No Skill runtime behavior, public method, license, Tag or Release was changed in this foundation update.
