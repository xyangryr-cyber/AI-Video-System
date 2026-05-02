"""Media storage -- file-system side of the SPEC-B-002 write path.

Two-step contract for committing a media artifact:

1. ``MediaStorage.write_bytes`` writes the file to disk.
2. The caller commits an ``artifact_ref`` (e.g. ``phases.artifact_path``)
   to SQLite via a repository.

If step 2 fails the caller MUST invoke ``MediaStorage.delete`` on the
returned path to remove the orphan file. ``ArtifactManager`` implements
that protocol; direct ``MediaStorage`` users are expected to do the
same.
"""

from __future__ import annotations

from pathlib import Path


class MediaStorage:
    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def write_bytes(self, relative_path: str, data: bytes) -> Path:
        target = self._root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    def delete(self, path: Path) -> None:
        """Idempotent delete -- missing file is not an error."""
        try:
            Path(path).unlink()
        except FileNotFoundError:
            pass
