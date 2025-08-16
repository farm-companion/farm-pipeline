from __future__ import annotations
import os, sys, json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, TypedDict

# repo root: farm-pipeline
ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

# Candidate locations for the sample (CI vs local)
SCHEMA_SAMPLE_CANDIDATES = [
    ROOT / "farm-schema" / "sample" / "seasons.uk.json",        # CI: extra checkout into subfolder
    ROOT.parents[0] / "farm-schema" / "sample" / "seasons.uk.json",  # Local: sibling repo
]

class SeasonItem(TypedDict, total=False):
    month: int
    inSeason: List[str]
    notes: str
    source: str
    sourceName: str
    updatedAt: str

def find_sample() -> Path | None:
    for p in SCHEMA_SAMPLE_CANDIDATES:
        if p.exists():
            return p
    return None

def load_local() -> List[SeasonItem]:
    sample = find_sample()
    if not sample:
        print("❌ Sample file missing; looked in:", file=sys.stderr)
        for p in SCHEMA_SAMPLE_CANDIDATES:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(sample.read_text("utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    for d in data:
        d.setdefault("source", "https://example.org/sample")
        d.setdefault("sourceName", "Local sample (dev)")
        d["updatedAt"] = now
    return data

def main():
    provider = os.getenv("SEASON_PROVIDER", "local").lower()
    if provider == "local":
        items = load_local()
    elif provider == "eufic":
        # Implemented next step
        print("EUFIC provider not yet implemented. Use SEASON_PROVIDER=local for now.", file=sys.stderr)
        sys.exit(2)
    else:
        print(f"Unknown provider: {provider}", file=sys.stderr)
        sys.exit(2)

    DIST.mkdir(parents=True, exist_ok=True)
    out = DIST / "seasons.uk.json"
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2))
    print(f"✅ Wrote {len(items)} seasonal items → {out}")

if __name__ == "__main__":
    main()
