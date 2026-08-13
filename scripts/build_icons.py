"""Build the Joycon2VRC icon family from the generated master artwork."""

from pathlib import Path

from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SMALL_MASTER = ASSETS / "icon-small-master.png"
DETAILED_MASTER = ASSETS / "icon-full-bleed-master.png"

WINDOWS_SIZES = (16, 24, 32, 48, 64, 96, 128, 256)
FAVICON_SIZES = (16, 32, 48)


def resized(source: Image.Image, size: int) -> Image.Image:
    image = source.resize((size, size), Image.Resampling.LANCZOS, reducing_gap=3.0)
    if size <= 48:
        image = image.filter(ImageFilter.UnsharpMask(radius=0.55, percent=115, threshold=2))
    return image


def main() -> None:
    small = Image.open(SMALL_MASTER).convert("RGBA")
    detailed = Image.open(DETAILED_MASTER).convert("RGBA")

    resized(small, 512).save(ASSETS / "icon.png", optimize=True)
    detailed_1024 = resized(detailed, 1024)
    detailed_1024.save(ASSETS / "icon-detailed.png", optimize=True)
    detailed_1024.save(ASSETS / "icon-1024.png", optimize=True)

    windows_dir = ASSETS / "windows"
    windows_dir.mkdir(exist_ok=True)
    for size in WINDOWS_SIZES:
        resized(small, size).save(windows_dir / f"icon-{size}.png", optimize=True)

    # Pillow embeds each requested resolution into one Windows ICO container.
    small.save(ASSETS / "icon.ico", sizes=[(size, size) for size in WINDOWS_SIZES])

    for size in FAVICON_SIZES:
        resized(small, size).save(ASSETS / f"favicon-{size}.png", optimize=True)
    resized(small, 32).save(ASSETS / "favicon.png", optimize=True)
    small.save(ASSETS / "favicon.ico", sizes=[(size, size) for size in FAVICON_SIZES])


if __name__ == "__main__":
    main()
