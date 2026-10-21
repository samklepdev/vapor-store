from PIL import Image

from tools.producer.mockup import CANVAS, make_mockup, wall


def test_wall_returns_rgb_of_given_size():
    img = wall((400, 300))
    assert img.size == (400, 300)
    assert img.mode == "RGB"


def test_make_mockup_writes_valid_canvas_with_art_composited(tmp_path):
    art = tmp_path / "art.png"
    Image.new("RGB", (512, 512), (255, 0, 255)).save(art)  # magenta
    out = make_mockup(art, tmp_path / "m.png")

    assert out.exists()
    img = Image.open(out).convert("RGB")
    assert img.size == CANVAS
    # canvas center falls inside the art region -> should be the magenta art, not wall
    r, g, b = img.getpixel((CANVAS[0] // 2, CANVAS[1] // 2))
    assert r > 150 and b > 150 and g < 120
