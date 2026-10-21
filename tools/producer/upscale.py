from __future__ import annotations

import argparse
import datetime as dt
import tomllib
from pathlib import Path

from .providers import ComfyUIProvider


def main() -> None:
    ap = argparse.ArgumentParser(description="vapor-studio image upscaler (ComfyUI)")
    ap.add_argument("image", help="path to the approved PNG to upscale")
    ap.add_argument("--config", default="tools/producer/config.toml")
    ap.add_argument("--out", default=None, help="output dir (default pipeline/05-packaged/<today>)")
    args = ap.parse_args()

    cfg = tomllib.loads(Path(args.config).read_text())["comfyui"]
    provider = ComfyUIProvider(base_url=cfg["base_url"], checkpoint=cfg.get("checkpoint", ""))
    model = cfg.get("upscale_model", "RealESRGAN_x4plus.pth")

    src = Path(args.image)
    out_dir = (
        Path(args.out) if args.out else Path("pipeline/05-packaged") / dt.date.today().isoformat()
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    data = provider.upscale(src.read_bytes(), slug=src.stem, model=model)
    out = out_dir / f"{src.stem}-4x.png"
    out.write_bytes(data)
    print(out)


if __name__ == "__main__":
    main()
