from pathlib import Path
import tempfile
import unittest

from scripts.validate_repo import parse_skill_frontmatter_text, validate_repo


class FrontmatterTests(unittest.TestCase):
    def test_block_description(self) -> None:
        metadata = parse_skill_frontmatter_text(
            "---\nname: sample-skill\ndescription: >-\n  A useful public skill.\n---\n"
        )
        self.assertEqual(metadata["name"], "sample-skill")
        self.assertEqual(metadata["description"], "A useful public skill.")

    def test_unquoted_colon_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_skill_frontmatter_text(
                "---\nname: sample-skill\ndescription: Invalid: unquoted value\n---\n"
            )


class RepositoryTests(unittest.TestCase):
    def test_current_repository_passes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(validate_repo(root), [])

    def test_manifest_directory_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ["README.md", "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md"]:
                (root / name).write_text("placeholder\n", encoding="utf-8")
            (root / "skills").mkdir()
            (root / "skills-manifest.json").write_text(
                '{"schema_version":1,"skills":[]}\n', encoding="utf-8"
            )
            (root / "skills" / "unlisted-skill").mkdir()
            (root / "skills" / "unlisted-skill" / "SKILL.md").write_text(
                "---\nname: unlisted-skill\ndescription: test\n---\n", encoding="utf-8"
            )
            errors = validate_repo(root)
            self.assertTrue(any("missing directory entry" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
