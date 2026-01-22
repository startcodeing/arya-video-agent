"""Script to run all tests."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Run all tests."""
    import pytest

    # Run pytest with arguments
    sys.exit(pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "--strict-markers",
    ]))


if __name__ == "__main__":
    main()
