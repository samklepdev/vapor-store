import datetime as dt
from pathlib import Path

import pytest

from tools.producer.generate import _load_provider, dated_output_dir, run, save_batch
from tools.producer.providers import ComfyUIProvider, FluxFalProvider, GenRequest, Provider


class FakeProvider:
    name = "fake"

    def __init__(self, blobs: list[bytes]) -> None:
        self._blobs = blobs
        self.seen: GenRequest | None = None

    def generate(self, req: GenRequest) -> list[bytes]:
        self.seen = req
        return self._blobs


def test_dated_output_dir_uses_iso_date(tmp_path: Path):
    d = dated_output_dir(tmp_path, today=dt.date(2026, 10, 20))
    assert d == tmp_path / "2026-10-20"


def test_save_batch_writes_padded_png_files(tmp_path: Path):
    paths = save_batch([b"a", b"b"], tmp_path, slug="battlestation")
    assert [p.name for p in paths] == ["battlestation-001.png", "battlestation-002.png"]
    assert (tmp_path / "battlestation-001.png").read_bytes() == b"a"


def test_run_calls_provider_and_writes_to_dated_dir(tmp_path: Path):
    prov: Provider = FakeProvider([b"x", b"y", b"z"])
    req = GenRequest(prompt="chrome grid sunset", n=3, slug="bs")
    paths = run(prov, req, raw_base=tmp_path, today=dt.date(2026, 10, 20))
    assert len(paths) == 3
    assert all(p.parent == tmp_path / "2026-10-20" for p in paths)
    assert prov.seen is req


def test_load_provider_defaults_to_fal():
    cfg = {"fal": {"api_key": "k"}}
    assert isinstance(_load_provider(cfg), FluxFalProvider)


def test_load_provider_comfyui_from_config():
    cfg = {
        "provider": {"kind": "comfyui"},
        "comfyui": {"base_url": "http://127.0.0.1:8188", "checkpoint": "c.safetensors"},
    }
    p = _load_provider(cfg)
    assert isinstance(p, ComfyUIProvider)
    assert p.name == "comfyui-sdxl"


def test_cli_override_beats_config_kind():
    cfg = {
        "provider": {"kind": "flux-fal"},
        "fal": {"api_key": "k"},
        "comfyui": {"base_url": "http://127.0.0.1:8188", "checkpoint": "c.safetensors"},
    }
    assert isinstance(_load_provider(cfg, override="comfyui"), ComfyUIProvider)


def test_unknown_provider_kind_raises():
    with pytest.raises(ValueError, match="unknown provider"):
        _load_provider({"provider": {"kind": "nope"}})
