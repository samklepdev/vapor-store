from __future__ import annotations

import argparse
import datetime as dt
import tomllib
from pathlib import Path

from .providers import FluxFalProvider, GenRequest, Provider


def dated_output_dir(base: Path, today: dt.date | None = None) -> Path:
    return base / (today or dt.date.today()).isoformat()


def save_batch(images: list[bytes], out_dir: Path, slug: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i, data in enumerate(images, start=1):
        p = out_dir / f"{slug}-{i:03d}.png"
        p.write_bytes(data)
        paths.append(p)
    return paths


def run(
    provider: Provider,
    req: GenRequest,
    raw_base: Path,
    today: dt.date | None = None,
) -> list[Path]:
    images = provider.generate(req)
    return save_batch(images, dated_output_dir(raw_base, today), req.slug)


def _load_fal(config_path: Path) -> FluxFalProvider:
    cfg = tomllib.loads(config_path.read_text())["fal"]
    return FluxFalProvider(api_key=cfg["api_key"], model=cfg.get("model", "fal-ai/flux/dev"))


def main() -> None:
    ap = argparse.ArgumentParser(description="vapor-studio image producer")
    ap.add_argument("--niche", required=True, help="slug, e.g. battlestation")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--config", default="tools/producer/config.toml")
    ap.add_argument("--raw-base", default="pipeline/02-raw")
    args = ap.parse_args()

    provider = _load_fal(Path(args.config))
    req = GenRequest(
        prompt=args.prompt, width=args.width, height=args.height, n=args.n, slug=args.niche
    )
    paths = run(provider, req, raw_base=Path(args.raw_base))
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
