"""Observable output invariants; run with unittest and an installed Pillow."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

from PIL import Image


MODULE = Path(__file__).parents[1] / "skills/photo-collage/scripts/postcard_output.py"
spec = importlib.util.spec_from_file_location("postcard_output", MODULE)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class PostcardOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.original = self.root / "original.png"
        self.card = self.root / "card.png"
        Image.new("RGB", (80, 60), (15, 92, 173)).save(self.original)
        Image.new("RGB", (40, 50), (244, 240, 228)).save(self.card)
        self.original_bytes = self.original.read_bytes()

    def tearDown(self):
        self.temp.cleanup()

    def test_postcard_only_has_no_original_panel_or_invented_labels(self):
        out = self.root / "only.png"
        report = helper.compose(self.card, out)
        with Image.open(out) as result, Image.open(self.card) as card:
            self.assertEqual(result.size, card.size)
            self.assertEqual(result.convert("RGBA").tobytes(), card.convert("RGBA").tobytes())
        self.assertEqual(report["labels"], {"date": "", "time": "", "location": ""})

    def test_stacked_original_is_untouched_even_if_card_width_differs(self):
        out = self.root / "stack.png"
        report = helper.compose(self.card, out, output_mode="stacked_original", original=self.original)
        with Image.open(out) as result, Image.open(self.original) as original:
            self.assertEqual(result.size, (80, 160))
            top = result.crop((0, 0, 80, 60)).convert("RGBA")
            self.assertEqual(top.tobytes(), original.convert("RGBA").tobytes())
        self.assertTrue(report["original_panel_pixels_equal"])
        self.assertEqual(self.original_bytes, self.original.read_bytes())

    def test_missing_original_and_input_overwrite_fail(self):
        with self.assertRaises(ValueError):
            helper.compose(self.card, self.root / "bad.png", output_mode="stacked_original")
        with self.assertRaises(ValueError):
            helper.compose(self.card, self.card)
        self.assertEqual(self.original_bytes, self.original.read_bytes())

    def test_preview_is_smaller_and_does_not_change_source(self):
        out = self.root / "preview.webp"
        helper.preview(self.original, out, width=40, quality=86)
        with Image.open(out) as result:
            self.assertEqual(result.size, (40, 30))
            self.assertEqual(result.format, "WEBP")
        self.assertEqual(self.original_bytes, self.original.read_bytes())

    def test_supplied_labels_change_only_card_and_preserve_literals(self):
        # Bigger card gives real caption space; compare top pixels after text rendering.
        Image.new("RGB", (400, 500), (244, 240, 228)).save(self.card)
        Image.new("RGB", (400, 300), (15, 92, 173)).save(self.original)
        labels = {"date": "2026.10.03", "time": "17:30", "location": "合成山湖"}
        out = self.root / "captioned-stack.png"
        report = helper.compose(self.card, out, output_mode="stacked_original", original=self.original,
                                font_path=os.environ.get("PHOTO_COLLAGE_TEST_FONT", helper.DEFAULT_CAPTION_FONT), **labels)
        self.assertEqual(report["labels"], labels)
        with Image.open(out) as result, Image.open(self.original) as original:
            self.assertEqual(result.crop((0, 0, 400, 300)).convert("RGBA").tobytes(),
                             original.convert("RGBA").tobytes())
        self.assertTrue(report["caption_bounds"])

    def test_default_handwritten_font_keeps_color_and_long_mixed_labels(self):
        Image.new("RGB", (1122, 1402), (244, 240, 228)).save(self.card)
        labels = {"date": "2026.10.03", "time": "17:30", "location": "福建省厦门市思明区环岛南路曾厝垵文创村海边观景步道 · Xiamen Seaside Walk"}
        out = self.root / "handwritten.png"
        report = helper.compose(self.card, out, **labels)
        self.assertEqual(report["labels"], labels)
        self.assertEqual(report["caption_color_rgba"], [174, 126, 99, 255])
        self.assertEqual(report["caption_font"], "LXGWWenKai-Regular.ttf")
        self.assertGreaterEqual(len(report["caption_bounds"]), 3)
        with Image.open(out) as result:
            self.assertGreater(result.tobytes().count(bytes([174, 126, 99, 255])), 0)
        for left, top, right, bottom in report["caption_bounds"]:
            self.assertGreaterEqual(left, 0)
            self.assertLessEqual(right, 1122)
            self.assertLessEqual(bottom, 1402)

    def test_missing_glyph_and_unreadably_long_text_fail(self):
        Image.new("RGB", (1122, 1402), (244, 240, 228)).save(self.card)
        out = self.root / "invalid-glyph.png"
        with self.assertRaises(ValueError):
            helper.compose(self.card, out, location=chr(0x10FFFF))
        self.assertFalse(out.exists())
        out = self.root / "too-long.png"
        with self.assertRaises(ValueError):
            helper.compose(self.card, out, location="厦门\n" * 30)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
