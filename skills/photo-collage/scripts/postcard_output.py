"""Deterministic card captions, lossless stacking, and small display previews.

Requires an existing Python + Pillow runtime. Never calls a model or reads GPS.
"""
import argparse
import hashlib
import json
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError as error:
    raise SystemExit("Missing Pillow in this Python runtime; use an existing Pillow runtime or another verified deterministic compositor.") from error


def load(path):
    with Image.open(path) as image:
        # Normalize display orientation only; do not infer captions from EXIF.
        return ImageOps.exif_transpose(image).convert("RGBA")


def destination(output, inputs):
    output = Path(output)
    if output.resolve() in {Path(p).resolve() for p in inputs if p is not None}:
        raise ValueError("Output must differ from all inputs; original files are preserved.")
    if output.exists():
        raise ValueError("Output exists; choose a new output filename.")
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def add_caption(card, labels, font_path):
    lines = [" ".join(value for value in [labels["date"], labels["time"]] if value), labels["location"]]
    lines = [line for line in lines if line]
    if not lines:
        return []
    if not font_path:
        raise ValueError("Supplied captions require an existing font covering those characters; provide --font.")
    width, height = card.size
    x, y = round(width * 0.12), round(height * 0.83)
    max_width, max_height = round(width * 0.76), round(height * 0.13)
    draw = ImageDraw.Draw(card)
    for size in range(max(8, round(width * 0.025)), 5, -1):
        font = ImageFont.truetype(str(font_path), size=size)
        wrapped = []
        for value in lines:
            for paragraph in value.split("\n"):
                line = ""
                for char in paragraph:
                    if line and draw.textlength(line + char, font=font) > max_width:
                        wrapped.append(line)
                        line = ""
                    line += char
                wrapped.append(line)
        step = round(size * 1.6)
        if len(wrapped) * step <= max_height:
            break
    else:
        raise ValueError("Caption does not fit without becoming unreadable; shorten it or choose a larger card.")
    missing = font.getmask(chr(0x10FFFF))
    for char in set("".join(lines)):
        glyph = font.getmask(char)
        if not char.isspace() and glyph.size == missing.size and bytes(glyph) == bytes(missing):
            raise ValueError("Font lacks a supplied character; select a font with matching language coverage.")
    boxes = []
    for index, line in enumerate(wrapped):
        position = (x, y + index * step)
        draw.text(position, line, font=font, fill=(174, 126, 99, 255), anchor="lt")
        boxes.append(list(draw.textbbox(position, line, font=font, anchor="lt")))
    return boxes


def compose(postcard, output, *, output_mode="postcard_only", original=None,
            location="", date="", time="", font_path=None):
    if output_mode not in {"postcard_only", "stacked_original"}:
        raise ValueError("Unknown output mode.")
    if output_mode == "stacked_original" and original is None:
        raise ValueError("stacked_original requires the authorized original image.")
    output = destination(output, [postcard, original])
    if output.suffix.lower() != ".png":
        raise ValueError("Use PNG for the lossless master; create a separate preview afterward.")
    card = load(postcard)
    source = load(original) if output_mode == "stacked_original" else None
    if source and card.width != source.width:
        card = card.resize((source.width, round(card.height * source.width / card.width)), Image.Resampling.LANCZOS)
    labels = {"date": date, "time": time, "location": location}
    bounds = add_caption(card, labels, font_path)
    if source:
        master = Image.new("RGBA", (source.width, source.height + card.height))
        master.paste(source, (0, 0))
        master.paste(card, (0, source.height))
    else:
        master = card
    master.save(output, format="PNG", compress_level=9)
    report = {"output_mode": output_mode, "size": list(master.size), "labels": labels,
              "caption_bounds": bounds, "bytes": output.stat().st_size}
    if source:
        with Image.open(output) as saved:
            top = saved.crop((0, 0, source.width, source.height)).convert("RGBA")
        report.update(original_size=list(source.size),
                      original_rgba_sha256=hashlib.sha256(source.tobytes()).hexdigest(),
                      original_panel_rgba_sha256=hashlib.sha256(top.tobytes()).hexdigest(),
                      original_panel_pixels_equal=source.tobytes() == top.tobytes())
        if not report["original_panel_pixels_equal"]:
            raise RuntimeError("Saved original panel failed lossless pixel verification.")
    return report


def preview(input_path, output, *, width=560, quality=86):
    if width < 1 or not 1 <= quality <= 100:
        raise ValueError("Width must be positive and quality must be 1–100.")
    output = destination(output, [input_path])
    if output.suffix.lower() not in {".webp", ".jpg", ".jpeg"}:
        raise ValueError("Preview must use WebP or JPEG; keep the PNG master separately.")
    image = load(input_path)
    if image.width > width:
        image = image.resize((width, round(image.height * width / image.width)), Image.Resampling.LANCZOS)
    if output.suffix.lower() == ".webp":
        image.save(output, format="WEBP", quality=quality, method=6)
    else:
        image.convert("RGB").save(output, format="JPEG", quality=quality, optimize=True, progressive=True)
    return {"size": list(image.size), "bytes": output.stat().st_size, "quality": quality}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    card = commands.add_parser("compose")
    card.add_argument("--postcard", required=True)
    card.add_argument("--original")
    card.add_argument("--output-mode", choices=["postcard_only", "stacked_original"], default="postcard_only")
    for label in ["location", "date", "time"]:
        card.add_argument("--" + label, default="")
    card.add_argument("--font", dest="font_path")
    small = commands.add_parser("preview")
    small.add_argument("--input", dest="input_path", required=True)
    small.add_argument("--width", type=int, default=560)
    small.add_argument("--quality", type=int, default=86)
    for command in [card, small]:
        command.add_argument("--output", required=True)
        command.add_argument("--report")
    args = vars(parser.parse_args())
    report_path = args.pop("report")
    action = args.pop("command")
    try:
        if report_path:
            destination(report_path, [args.get("postcard"), args.get("original"), args.get("input_path"), args["output"]])
        result = compose(**args) if action == "compose" else preview(**args)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if report_path:
        Path(report_path).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
