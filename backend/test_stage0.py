"""Test Stage 0 — image to text via MiniCPM."""

from pathlib import Path

from model_manager import manager
from pipelines.stage0_minicpm import run_stage0


# Use the same test image you used in PowerShell.
IMAGE_PATH = Path(r"C:\Users\prath\projects\Summerizer\content-summarizer\test image.png")


def main() -> None:
    print(f"Reading: {IMAGE_PATH}")
    image_bytes = IMAGE_PATH.read_bytes()
    print(f"Loaded {len(image_bytes)} bytes.")

    print("\nEnsuring MiniCPM-V is loaded...")
    manager.ensure_model("minicpm")

    print("\nRunning Stage 0 (image → text)...")
    description = run_stage0(image_bytes, IMAGE_PATH.name)

    print("\n=== DESCRIPTION ===")
    print(description)

    print("\nShutting down...")
    manager.shutdown()


if __name__ == "__main__":
    main()
    