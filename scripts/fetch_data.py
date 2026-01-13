#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

# -----------------------------
# Utilities
# -----------------------------

def _sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _sha256_file(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _atomic_write_bytes(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    with tmp.open('wb') as f:
        f.write(data)
    tmp.replace(target)


def _write_metadata(sidecar: Path, metadata: Dict) -> None:
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    with sidecar.open('w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


# -----------------------------
# Source configuration
# -----------------------------

@dataclass
class SourceSpec:
    key: str
    description: str
    env_url: str
    default_filename: str
    env_token: Optional[str] = None  # e.g., METOFFICE_API_KEY


SOURCES: Dict[str, SourceSpec] = {
    "ons": SourceSpec(
        key="ons",
        description="ONS tourism spend by region (CSV/Excel)",
        env_url="ONS_TOURISM_URL",
        default_filename="ons_tourism_spend_by_region.csv",
    ),
    "visitbritain": SourceSpec(
        key="visitbritain",
        description="VisitBritain international visitors monthly (CSV)",
        env_url="VISITBRITAIN_URL",
        default_filename="visitbritain_international_visitors_monthly.csv",
    ),
    "opengeo": SourceSpec(
        key="opengeo",
        description="ONS Open Geography LAD boundaries (GeoJSON/Shapefile)",
        env_url="OPEN_GEO_LAD_URL",
        default_filename="open_geography_lad.geojson",
    ),
    "metoffice": SourceSpec(
        key="metoffice",
        description="Met Office regional weather summaries (JSON/CSV)",
        env_url="METOFFICE_URL",
        env_token="METOFFICE_API_KEY",
        default_filename="metoffice_regional_weather.json",
    ),
}


# -----------------------------
# Fetch logic (HTTP)
# -----------------------------

def http_fetch_bytes(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    timeout: int = 60,
) -> Tuple[bytes, Dict[str, str]]:
    """Fetch bytes via stdlib urllib; returns (content, response_headers)."""
    if params:
        sep = '&' if ('?' in url) else '?'
        url = f"{url}{sep}{urlencode(params)}"

    req = Request(url, headers=headers or {})
    with urlopen(req, timeout=timeout) as resp:
        content = resp.read()
        headers_out = {k.lower(): v for k, v in resp.headers.items()}
    return content, headers_out


# -----------------------------
# Orchestration
# -----------------------------

def resolve_output_path(url: str, out_dir: Path, fallback_filename: str) -> Path:
    """Derive a filename from the URL path; fall back if missing."""
    parsed = urlparse(url)
    name = Path(parsed.path).name
    if not name:
        name = fallback_filename
    return out_dir / name


def ingest_one(
    spec: SourceSpec,
    url: str,
    out_dir: Path,
    token: Optional[str] = None,
    params: Optional[Dict[str, str]] = None,
    force: bool = False,
) -> Dict:
    """Download a single source, write bytes atomically if changed, and create metadata sidecar.

    Returns a summary dict.
    """
    headers = {}
    if token:
        # Common patterns; adjust for specific APIs as needed.
        headers["Authorization"] = f"Bearer {token}"

    out_path = resolve_output_path(url, out_dir, spec.default_filename)

    # Fetch
    content, resp_headers = http_fetch_bytes(url, headers=headers, params=params)
    new_hash = _sha256_bytes(content)

    # Idempotency check
    old_hash = _sha256_file(out_path)
    changed = (old_hash != new_hash) or force or (old_hash is None)

    # Write if needed
    if changed:
        _atomic_write_bytes(out_path, content)

    # Sidecar metadata
    sidecar = out_path.with_suffix(out_path.suffix + ".metadata.json")
    metadata = {
        "source": spec.key,
        "description": spec.description,
        "url": url,
        "downloaded_at": dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat(),
        "sha256": new_hash,
        "size_bytes": len(content),
        "content_type": resp_headers.get("content-type"),
        "params": params or {},
        "token_env": spec.env_token,
        "force": force,
    }
    _write_metadata(sidecar, metadata)

    return {
        "source": spec.key,
        "file": str(out_path),
        "changed": changed,
        "size_bytes": len(content),
        "sha256": new_hash,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch raw datasets for UK Tourism Analytics and store them in data/raw/ with metadata sidecars.\n"
            "Provide source URLs via CLI flags or environment variables."
        )
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=sorted(SOURCES.keys()) + ["all"],
        default=["all"],
        help="Which sources to fetch (default: all)",
    )
    parser.add_argument(
        "--out-dir",
        default="data/raw",
        help="Output directory for raw files (default: data/raw)",
    )
    # Optional per-source URL overrides
    for key, spec in SOURCES.items():
        parser.add_argument(
            f"--{key}-url",
            default=None,
            help=(
                f"Override URL for {key}. If not provided, reads from env {spec.env_url}."
            ),
        )
    parser.add_argument(
        "--since",
        default=None,
        help=(
            "Optional date filter (YYYY-MM or YYYY-MM-DD) passed as a param where supported."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite even if content hash is unchanged.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help=(
            "Create small placeholder files instead of downloading (for first-run testing only)."
        ),
    )
    # In notebook/CI contexts, unknown args may be passed; ignore them.
    args, _unknown = parser.parse_known_args()
    return args


def _demo_write_placeholder(out_dir: Path, spec: SourceSpec) -> Dict:
    """Create a tiny placeholder CSV/GeoJSON to validate the pipeline wiring.
    Only used when --demo is passed.
    """
    if spec.key == "opengeo":
        data = (
            '{"type":"FeatureCollection","features":[]}\n'.encode("utf-8")
        )
        out_path = out_dir / spec.default_filename
    else:
        # Minimal CSV header only
        header = "date,region_code,value\n".encode("utf-8")
        data = header
        out_path = out_dir / spec.default_filename

    new_hash = _sha256_bytes(data)
    _atomic_write_bytes(out_path, data)
    sidecar = out_path.with_suffix(out_path.suffix + ".metadata.json")
    _write_metadata(
        sidecar,
        {
            "source": spec.key,
            "description": spec.description,
            "url": "demo://placeholder",
            "downloaded_at": dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat(),
            "sha256": new_hash,
            "size_bytes": len(data),
            "content_type": "text/csv" if spec.key != "opengeo" else "application/geo+json",
            "params": {},
            "token_env": spec.env_token,
            "force": True,
            "demo": True,
        },
    )
    return {
        "source": spec.key,
        "file": str(out_path),
        "changed": True,
        "size_bytes": len(data),
        "sha256": new_hash,
        "demo": True,
    }


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = list(SOURCES.keys()) if "all" in args.sources else args.sources

    # Common date param (best-effort; different APIs may require different naming)
    date_param = None
    if args.since:
        date_param = {"since": args.since}

    summaries = []

    for key in selected:
        spec = SOURCES[key]

        # Resolve URL (CLI flag > ENV var)
        cli_val = getattr(args, f"{key}_url")
        url = cli_val or os.getenv(spec.env_url)

        if args.demo:
            # Create placeholder and continue
            summaries.append(_demo_write_placeholder(out_dir, spec))
            continue

        if not url:
            print(
                f"[skip] {key}: no URL provided. Set --{key}-url or env {spec.env_url}."
            )
            continue

        token = os.getenv(spec.env_token) if spec.env_token else None

        try:
            summary = ingest_one(
                spec=spec,
                url=url,
                out_dir=out_dir,
                token=token,
                params=date_param,
                force=args.force,
            )
            status = "downloaded" if summary["changed"] else "up-to-date"
            size_kb = summary["size_bytes"] / 1024
            print(f"[ok] {key}: {status} → {summary['file']} ({size_kb:.1f} KB)")
            summaries.append(summary)
        except Exception as e:
            print(f"[error] {key}: {e}")

    # Print a short JSON summary for logs/CI
    print("\n=== fetch summary ===")
    print(json.dumps(summaries, indent=2))

    # DVC hint (printed only; actual DVC ops are done outside this script)
    print(
        "\nHint: run `dvc add data/raw` and `dvc push` to version raw datasets after fetching."
    )


if __name__ == "__main__":
    main()
