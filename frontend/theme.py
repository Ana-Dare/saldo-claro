from pathlib import Path


def load_css() -> str:
    return (Path(__file__).parent / "styles.css").read_text(encoding="utf-8")
