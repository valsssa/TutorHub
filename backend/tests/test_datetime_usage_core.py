"""Tests to verify datetime usage across entire codebase."""
import os
from pathlib import Path


def test_no_utcnow_in_entire_codebase():
    """Ensure datetime.utcnow() is not used anywhere in codebase."""
    backend_path = Path(__file__).parent.parent
    violations = []

    for root, dirs, files in os.walk(backend_path):
        # Skip test files, migrations, and __pycache__
        if "__pycache__" in root or "migrations" in root:
            continue
        for file in files:
            if file.endswith(".py") and not file.startswith("test_"):
                file_path = Path(root) / file
                try:
                    source = file_path.read_text()
                    if "utcnow()" in source and "datetime_utils" not in str(file_path):
                        violations.append(str(file_path.relative_to(backend_path)))
                except Exception:
                    pass

    assert not violations, (
        f"Found datetime.utcnow() in: {violations}. "
        "Use core.datetime_utils.utc_now() instead."
    )
