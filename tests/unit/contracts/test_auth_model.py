"""Tests for [SPEC-A-009] V1 Authentication Model (Single-User)."""

import json
import re
import subprocess
from pathlib import Path


class TestAC1DefaultUserIdValue:
    """AC-1: `DEFAULT_USER_ID` constant equals "default" in both Python and TypeScript"""

    def test_default_user_id_value(self):
        from src.shared.constants.auth import DEFAULT_USER_ID

        assert DEFAULT_USER_ID == "default"

    def test_default_user_id_value_typescript(self):
        ts_path = Path("src/shared/constants/auth.ts")
        assert ts_path.exists(), "src/shared/constants/auth.ts must exist"
        content = ts_path.read_text()
        assert "DEFAULT_USER_ID" in content
        assert '"default"' in content or "'default'" in content


class TestAC2NoHardcodedDefaultUserId:
    """AC-2: No hardcoded string "default" for user_id anywhere outside the constant definition"""

    def test_no_hardcoded_default_user_id(self):
        result = subprocess.run(
            ["rg", '"default"', "src/", "--type", "py"], capture_output=True, text=True
        )
        lines = result.stdout.splitlines()
        violations = [
            line
            for line in lines
            if re.search(r"user", line, re.IGNORECASE)
            and "DEFAULT_USER_ID" not in line
            and "auth.py" not in line
        ]
        assert violations == [], "Hardcoded 'default' user_id found:\n" + "\n".join(
            violations
        )


class TestAC3EnsureUserDirCreatesDirectory:
    """AC-3: Startup function creates `data/users/default/` if it does not exist"""

    def test_ensure_user_dir_creates_directory(self, tmp_path):
        from src.backend.startup.ensure_user_dir import ensure_user_dir

        ensure_user_dir(base=tmp_path)
        expected = tmp_path / "data" / "users" / "default"
        assert expected.is_dir(), f"Expected {expected} to be a directory"


class TestAC4EnsureUserDirCreatesBrandKitTemplate:
    """AC-4: Startup function creates `data/users/default/brand_kit.json` template if missing"""

    def test_ensure_user_dir_creates_brand_kit_template(self, tmp_path):
        from src.backend.startup.ensure_user_dir import ensure_user_dir

        ensure_user_dir(base=tmp_path)
        brand_kit = tmp_path / "data" / "users" / "default" / "brand_kit.json"
        assert brand_kit.is_file(), f"Expected {brand_kit} to exist"
        data = json.loads(brand_kit.read_text())
        assert isinstance(data, dict), "brand_kit.json must be a JSON object"

    def test_ensure_user_dir_does_not_overwrite_existing_brand_kit(self, tmp_path):
        from src.backend.startup.ensure_user_dir import ensure_user_dir

        ensure_user_dir(base=tmp_path)
        brand_kit = tmp_path / "data" / "users" / "default" / "brand_kit.json"
        original = {"custom": "value"}
        brand_kit.write_text(json.dumps(original))

        ensure_user_dir(base=tmp_path)
        data = json.loads(brand_kit.read_text())
        assert data == original, (
            "ensure_user_dir must not overwrite existing brand_kit.json"
        )


class TestAC5No401403ErrorCodes:
    """AC-5: No 401 or 403 HTTP status codes defined in error code constants"""

    def test_no_401_403_error_codes(self):
        result = subprocess.run(
            ["rg", r"401|403|UNAUTHORIZED|FORBIDDEN", "src/shared/", "--type", "py"],
            capture_output=True,
            text=True,
        )
        lines = result.stdout.strip()
        assert lines == "", (
            f"Found 401/403/UNAUTHORIZED/FORBIDDEN in shared constants:\n{lines}"
        )


class TestAC6V15UpgradePathDocumented:
    """AC-6: Code comments document V1.5 upgrade path: users table + session token + middleware"""

    def test_v15_upgrade_path_documented(self):
        auth_path = Path("src/shared/constants/auth.py")
        assert auth_path.exists(), "src/shared/constants/auth.py must exist"
        content = auth_path.read_text()
        keywords = ["V1.5", "session token", "middleware"]
        for kw in keywords:
            assert kw.lower() in content.lower(), (
                f"V1.5 upgrade comment must mention '{kw}'"
            )
