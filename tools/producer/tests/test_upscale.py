import json

from tools.producer.providers import ComfyUIProvider


def _provider() -> ComfyUIProvider:
    return ComfyUIProvider("http://127.0.0.1:8188", "sd_xl_base_1.0.safetensors", poll_interval=0.0)


def test_build_upscale_workflow_wiring():
    p = _provider()
    g = p._build_upscale_workflow("input.png", "RealESRGAN_x4plus.pth", "bs-night-neon-001")
    assert g["10"]["class_type"] == "LoadImage"
    assert g["10"]["inputs"]["image"] == "input.png"
    assert g["11"]["class_type"] == "UpscaleModelLoader"
    assert g["11"]["inputs"]["model_name"] == "RealESRGAN_x4plus.pth"
    assert g["12"]["class_type"] == "ImageUpscaleWithModel"
    assert g["12"]["inputs"]["upscale_model"] == ["11", 0]
    assert g["12"]["inputs"]["image"] == ["10", 0]
    assert g["13"]["class_type"] == "SaveImage"
    assert g["13"]["inputs"]["images"] == ["12", 0]
    assert g["13"]["inputs"]["filename_prefix"] == "bs-night-neon-001"


def test_upscale_uploads_submits_and_downloads(monkeypatch):
    p = _provider()
    seen = {}

    def fake_upload(data, filename):
        seen["uploaded"] = (data, filename)
        return "input.png"

    def fake_post(path, payload):
        seen["submit_path"] = path
        seen["graph"] = payload["prompt"]
        return {"prompt_id": "pid"}

    history = {
        "pid": {
            "status": {"status_str": "success", "completed": True},
            "outputs": {
                "13": {"images": [{"filename": "up.png", "subfolder": "", "type": "output"}]}
            },
        }
    }
    monkeypatch.setattr(p, "_upload_image", fake_upload)
    monkeypatch.setattr(p, "_post_json", fake_post)
    monkeypatch.setattr(p, "_get_json", lambda path: history)
    monkeypatch.setattr(p, "_get_bytes", lambda path: b"UP:" + path.encode())

    out = p.upscale(b"rawbytes", slug="bs", model="RealESRGAN_x4plus.pth")

    assert seen["uploaded"] == (b"rawbytes", "bs.png")
    assert seen["submit_path"] == "/prompt"
    assert seen["graph"]["11"]["inputs"]["model_name"] == "RealESRGAN_x4plus.pth"
    assert out == b"UP:/view?filename=up.png&subfolder=&type=output"


def test_upload_image_builds_multipart(monkeypatch):
    p = _provider()
    captured = {}

    def fake_open(request):
        captured["url"] = request.full_url
        captured["ctype"] = request.headers.get("Content-type")
        captured["body"] = request.data
        return json.dumps({"name": "input.png", "subfolder": "", "type": "input"}).encode()

    monkeypatch.setattr(p, "_open", fake_open)
    name = p._upload_image(b"PNGDATA", "bs.png")

    assert name == "input.png"
    assert captured["url"].endswith("/upload/image")
    assert "multipart/form-data; boundary=" in captured["ctype"]
    assert b'name="image"; filename="bs.png"' in captured["body"]
    assert b"PNGDATA" in captured["body"]
