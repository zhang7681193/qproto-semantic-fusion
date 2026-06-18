"""Verify the source assets for the Information Fusion workflow figure.

Figure 1 is distributed as an editable PowerPoint source plus the exported
workflow image used by the LaTeX manuscript. The check guards against
accidentally reverting to the older three-panel concept figure.
"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    roots = [Path("manuscript/latex_qproto_hop_IF"), Path("latex_qproto_hop_IF")]
    root = next((candidate for candidate in roots if candidate.exists()), None)
    if root is None:
        raise SystemExit("Missing manuscript LaTeX directory.")

    tex_source = root / "sections" / "01_introduction.tex"
    image_asset = root / "figures" / "fig1_semantic_fusion_redrawn_v45_cropped.png"
    pptx_asset = root / "figures" / "fig1_semantic_fusion_redrawn_v45_source.pptx"

    for required in (tex_source, image_asset, pptx_asset):
        if not required.exists():
            raise SystemExit(f"Missing Figure 1 asset: {required}")

    text = tex_source.read_text(encoding="utf-8")
    marker = "figures/fig1_semantic_fusion_redrawn_v45_cropped.png"
    if marker not in text:
        raise SystemExit("The introduction does not reference the current workflow Figure 1 image.")

    print(f"Figure 1 LaTeX source: {tex_source}")
    print(f"Figure 1 workflow asset: {image_asset}")
    print(f"Figure 1 editable source: {pptx_asset}")


if __name__ == "__main__":
    main()

