"""Tests for [SPEC-B-001] Docker Compose Three-Service Topology.

These tests validate the *configuration topology* B-001 is responsible for:
docker-compose.yml, .env.example, .gitignore, Dockerfiles, init-data-dirs.sh.

Runtime verification (actually starting containers, curling the frontend,
inspecting container env) is out of scope here -- those land in
`tests/integration/infra/` once backend API (B-003) and worker (B-004) are
implemented enough to boot. See AGENTS.md "Business-Complete Delivery Gate":
B-001 delivers the scaffold; B-003/B-004 deliver runtime bring-up.

No pyyaml dependency: docker-compose structure is simple enough for regex-
based checks, and adding a dep is outside B-001's allowed_files.
"""

from __future__ import annotations

import re
import stat
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
GITIGNORE = REPO_ROOT / ".gitignore"
INIT_SCRIPT = REPO_ROOT / "scripts" / "init-data-dirs.sh"
BACKEND_DOCKERFILE = REPO_ROOT / "src" / "backend" / "Dockerfile"
FRONTEND_DOCKERFILE = REPO_ROOT / "src" / "frontend" / "Dockerfile"

EXPECTED_SERVICES = ("web", "api", "worker")
EXPECTED_DATA_SUBDIRS = ("config", "users", "projects", "logs", "db")


# ---- Helpers ---------------------------------------------------------------


def _compose_text() -> str:
    assert COMPOSE_FILE.is_file(), f"missing: {COMPOSE_FILE}"
    return COMPOSE_FILE.read_text(encoding="utf-8")


def _service_block(compose_text: str, name: str) -> str:
    """Return the YAML block for a given service (everything up to the next
    top-level service key or end-of-file). Regex-based because we chose not
    to add a yaml dep for this single consumer.
    """
    pattern = rf"^  {re.escape(name)}:\n(?P<body>(?:    .*\n|\n)+?)(?=^  \S|^\S|\Z)"
    m = re.search(pattern, compose_text, re.MULTILINE)
    assert m is not None, f"service '{name}' block not found in docker-compose.yml"
    return m.group("body")


# ---- AC-1: three services defined in compose ------------------------------


class TestAC1ThreeServicesRunning:
    """AC-1: `docker compose up -d` 后三个服务状态为 Running

    Config-level assertion: the compose file declares web/api/worker with
    a buildable context or image reference. Actual runtime bring-up is a
    B-003/B-004 concern (integration test).
    """

    def test_compose_file_exists(self):
        assert COMPOSE_FILE.is_file(), "docker-compose.yml is missing"

    def test_three_services_defined(self):
        text = _compose_text()
        for svc in EXPECTED_SERVICES:
            assert re.search(rf"^  {svc}:", text, re.MULTILINE), (
                f"service '{svc}' must be declared at top-level of services:"
            )

    def test_each_service_has_build_or_image(self):
        text = _compose_text()
        for svc in EXPECTED_SERVICES:
            body = _service_block(text, svc)
            assert ("build:" in body) or ("image:" in body), (
                f"service '{svc}' must declare either build: or image:"
            )

    def test_api_and_worker_share_backend_dockerfile(self):
        """api and worker are Python services sharing src/backend/ build."""
        text = _compose_text()
        for svc in ("api", "worker"):
            body = _service_block(text, svc)
            # Accept: build:, context:, or dockerfile: pointing at src/backend
            assert re.search(
                r"(build|context|dockerfile):\s*(\./)?src/backend",
                body,
            ), f"service '{svc}' must build from src/backend/"


# ---- AC-2: frontend reachable on :3000 ------------------------------------


class TestAC2FrontendAccessible:
    """AC-2: 前端 http://localhost:3000 返回 200 OK

    Config-level: web service publishes host port 3000.
    """

    def test_web_service_publishes_port_3000(self):
        text = _compose_text()
        body = _service_block(text, "web")
        # Accept "3000:3000", "3000:<inner>", or list item form
        assert re.search(r"3000\s*:\s*\d+", body) or re.search(
            r"- \s*['\"]?3000:", body
        ), "web service must publish host port 3000"

    def test_web_service_builds_frontend_dockerfile(self):
        text = _compose_text()
        body = _service_block(text, "web")
        assert re.search(
            r"(build|context|dockerfile):\s*(\./)?src/frontend",
            body,
        ), "web service must build from src/frontend/"


# ---- AC-3: .env ignored by git --------------------------------------------


class TestAC3EnvInGitignore:
    """AC-3: `.env` 在 `.gitignore` 中，不被 git 追踪"""

    def test_env_in_gitignore(self):
        text = GITIGNORE.read_text(encoding="utf-8")
        # Either ".env" on its own line or ".env*" pattern; NOT commented
        patterns = [r"^\.env$", r"^\.env\*$", r"^\.env\.\*$"]
        assert any(re.search(p, text, re.MULTILINE) for p in patterns), (
            ".env (or .env* / .env.*) must be listed in .gitignore"
        )

    def test_env_example_allowlisted(self):
        """Ensure .env.example stays tracked even though .env is ignored."""
        text = GITIGNORE.read_text(encoding="utf-8")
        assert re.search(r"^!\.env\.example$", text, re.MULTILINE), (
            "!.env.example negation must be present so template stays tracked"
        )

    def test_env_example_file_exists(self):
        assert ENV_EXAMPLE.is_file(), ".env.example template missing"


# ---- AC-4: init-data-dirs.sh sets .env permission to 600 ------------------


class TestAC4EnvFilePermission600:
    """AC-4: `.env` 文件权限为 600 (scripts/init-data-dirs.sh 中设置)"""

    def test_init_script_exists(self):
        assert INIT_SCRIPT.is_file(), "scripts/init-data-dirs.sh missing"

    def test_init_script_is_executable(self):
        mode = INIT_SCRIPT.stat().st_mode
        assert mode & stat.S_IXUSR, (
            "scripts/init-data-dirs.sh must be executable (chmod +x)"
        )

    def test_init_script_chmods_env_to_600(self):
        text = INIT_SCRIPT.read_text(encoding="utf-8")
        assert re.search(r"chmod\s+600\s+.*\.env\b", text), (
            "init-data-dirs.sh must chmod 600 on .env to protect secrets"
        )


# ---- AC-5: API_KEY injection via env_file ---------------------------------


class TestAC5ApiKeyInjected:
    """AC-5: 容器内 `env | grep _API_KEY` 可见注入值

    Config-level: .env.example lists at least one _API_KEY variable;
    api and worker services reference env_file.
    """

    def test_env_example_declares_api_key_vars(self):
        text = ENV_EXAMPLE.read_text(encoding="utf-8")
        assert re.search(r"^\w*_API_KEY\s*=", text, re.MULTILINE), (
            ".env.example must declare at least one *_API_KEY template variable"
        )

    def test_api_service_uses_env_file(self):
        text = _compose_text()
        body = _service_block(text, "api")
        assert "env_file:" in body, "api service must declare env_file:"
        assert ".env" in body, "api service env_file must reference .env"

    def test_worker_service_uses_env_file(self):
        text = _compose_text()
        body = _service_block(text, "worker")
        assert "env_file:" in body, "worker service must declare env_file:"
        assert ".env" in body, "worker service env_file must reference .env"


# ---- AC-6: sqlite DB mount path ------------------------------------------


class TestAC6SqliteDbExists:
    """AC-6: `ls data/db/app.sqlite3` 存在 (Volume 挂载正确)

    Config-level: api (and/or worker) service mounts ./data (which contains
    db/) into the container, and init-data-dirs.sh creates data/db/. The
    sqlite file itself is created by the app at first write; we only assert
    the mount plumbing is in place.
    """

    def test_api_mounts_data_volume(self):
        text = _compose_text()
        body = _service_block(text, "api")
        assert re.search(r"(\./)?data(:|/db)", body), (
            "api service must mount ./data (or ./data/db) volume"
        )

    def test_init_script_creates_data_db_dir(self):
        text = INIT_SCRIPT.read_text(encoding="utf-8")
        assert re.search(r"(mkdir[^\n]*data/db)|(data/db)", text), (
            "init-data-dirs.sh must ensure data/db/ directory exists"
        )


# ---- AC-7: data/ directory structure -------------------------------------


class TestAC7DataDirectoryStructure:
    """AC-7: `./data/{config,users,projects,logs,db}` 目录结构完整"""

    def test_init_script_creates_all_five_subdirs(self):
        text = INIT_SCRIPT.read_text(encoding="utf-8")
        for sub in EXPECTED_DATA_SUBDIRS:
            assert re.search(rf"data/{sub}\b", text), (
                f"init-data-dirs.sh must create data/{sub}/"
            )

    def test_init_script_uses_mkdir_p(self):
        """-p flag makes the script idempotent; required for re-runs."""
        text = INIT_SCRIPT.read_text(encoding="utf-8")
        assert "mkdir -p" in text, (
            "init-data-dirs.sh should use `mkdir -p` for idempotence"
        )
