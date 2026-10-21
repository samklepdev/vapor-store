import io
import urllib.error
import urllib.request

import pytest

from tools.producer.providers import ComfyUIProvider, GenRequest, Provider


def _provider() -> ComfyUIProvider:
    return ComfyUIProvider(
        "http://127.0.0.1:8188/", "sd_xl_base_1.0.safetensors", poll_interval=0.0
    )


def test_satisfies_provider_protocol():
    assert isinstance(_provider(), Provider)
    assert _provider().name == "comfyui-sdxl"


def test_build_workflow_maps_request_fields():
    p = _provider()
    req = GenRequest(prompt="chrome grid sunset", width=1152, height=896, n=3, slug="bs")
    g = p._build_workflow(req, seed=42)

    assert g["4"]["inputs"]["ckpt_name"] == "sd_xl_base_1.0.safetensors"
    assert g["6"]["inputs"]["text"] == "chrome grid sunset"      # positive prompt
    assert g["6"]["inputs"]["clip"] == ["4", 1]
    assert g["7"]["inputs"]["text"] == ""                        # negative (default)
    assert g["5"]["inputs"] == {"width": 1152, "height": 896, "batch_size": 3}
    assert g["3"]["inputs"]["seed"] == 42
    assert g["3"]["inputs"]["steps"] == 30
    assert g["3"]["inputs"]["model"] == ["4", 0]
    assert g["3"]["inputs"]["latent_image"] == ["5", 0]
    assert g["8"]["inputs"]["samples"] == ["3", 0]
    assert g["9"]["inputs"]["filename_prefix"] == "bs"


def test_generate_submits_awaits_and_downloads_in_order(monkeypatch):
    p = _provider()
    sent = {}
    history = {
        "pid": {
            "status": {"status_str": "success", "completed": True},
            "outputs": {
                "9": {
                    "images": [
                        {"filename": "a.png", "subfolder": "", "type": "output"},
                        {"filename": "b.png", "subfolder": "sub", "type": "output"},
                    ]
                }
            },
        }
    }
    monkeypatch.setattr(
        p,
        "_post_json",
        lambda path, payload: sent.update(path=path, payload=payload)
        or {"prompt_id": "pid"},
    )
    monkeypatch.setattr(p, "_get_json", lambda path: history)
    monkeypatch.setattr(p, "_get_bytes", lambda path: b"BYTES:" + path.encode())

    out = p.generate(GenRequest(prompt="x", n=2, slug="s"))

    assert sent["path"] == "/prompt"
    assert "prompt" in sent["payload"] and "client_id" in sent["payload"]
    assert out == [
        b"BYTES:/view?filename=a.png&subfolder=&type=output",
        b"BYTES:/view?filename=b.png&subfolder=sub&type=output",
    ]


def test_generate_raises_when_prompt_rejected(monkeypatch):
    p = _provider()
    monkeypatch.setattr(p, "_post_json", lambda path, payload: {"error": "bad node"})
    with pytest.raises(RuntimeError, match="rejected"):
        p.generate(GenRequest(prompt="x", n=1, slug="s"))


def test_generate_raises_when_no_images(monkeypatch):
    p = _provider()
    history = {"pid": {"status": {"status_str": "success", "completed": True}, "outputs": {}}}
    monkeypatch.setattr(p, "_post_json", lambda path, payload: {"prompt_id": "pid"})
    monkeypatch.setattr(p, "_get_json", lambda path: history)
    with pytest.raises(RuntimeError, match="no images"):
        p.generate(GenRequest(prompt="x", n=1, slug="s"))


def test_timeout_surfaces_as_runtime_error(monkeypatch):
    p = _provider()

    def _boom(*args, **kwargs):
        raise TimeoutError("slow server")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    with pytest.raises(RuntimeError, match="unresponsive"):
        p._get_json("/history/x")


def test_http_error_surfaces_comfyui_body(monkeypatch):
    p = _provider()

    def _raise_http_error(*args, **kwargs):
        raise urllib.error.HTTPError(
            url="http://127.0.0.1:8188/prompt",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=io.BytesIO(b'{"node_errors": {"4": "checkpoint not found"}}'),
        )

    monkeypatch.setattr(urllib.request, "urlopen", _raise_http_error)
    with pytest.raises(RuntimeError, match="rejected") as excinfo:
        p._get_json("/prompt")
    assert "checkpoint not found" in str(excinfo.value)
