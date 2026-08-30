# Contributing

Thank you for helping improve the public Agent Skills.

## Before opening a Pull Request

1. Keep one focused change per Pull Request.
2. Update only public, authorized material. Use synthetic examples instead of customer, account or internal data.
3. Preserve the Skill name and invocation boundary unless the change explicitly addresses routing.
4. Add or update tests when scripts, validation rules or behavior contracts change.
5. Run:

```bash
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -v
python3 -m compileall -q skills scripts tests
```

## Public-boundary requirements

- Do not submit names, phone numbers, email addresses, account IDs, customer lists, internal links, cookies, credentials or private cases.
- Do not submit `.DS_Store`, caches, logs, generated ZIP files, local absolute paths or binary work products.
- Do not copy third-party articles, books, screenshots, prompts or datasets without a compatible license and required attribution.
- Separate facts, inferences, hypotheses and synthetic examples.

## Skill structure

Runtime packages belong under `skills/<skill-name>/`. Keep the entrypoint at `SKILL.md`; add `scripts/`, `references/`, `assets/`, `agents/` and per-Skill licenses only when needed.

Add every new Skill to `skills-manifest.json`. A directory/manifest mismatch fails CI.
