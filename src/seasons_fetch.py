from __future__ import annotations
import os, sys, json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, TypedDict

# repo root: farm-pipeline
ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

# sibling repo: farm-schema/sample/seasons.uk.json
SCHEMA_SAMPLE = ROOT.parents[0] / "farm-schema" / "sample" / "seasons.uk.json"

class SeasonItem(TypedDict, total=False):
    month: int
    inSeason: List[str]
    notes: str
    source: str
    sourceName: str
    updatedAt: str

def load_local() -> List[SeasonItem]:
    if not SCHEMA_SAMPLE.exists():
        print(f"❌ Sample file missing: {SCHEMA_SAMPLE}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(SCHEMA_SAMPLE.read_text("utf-8"))
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
