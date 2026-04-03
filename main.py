from __future__ import annotations

import argparse
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional

import utils


def unified_diff(old_text: str, new_text: str, *, from_name: str, to_name: str) -> str:
    """
    Create a readable diff between two normalized text blobs.
    """
    old_lines = (old_text or "").splitlines()
    new_lines = (new_text or "").splitlines()
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=from_name,
        tofile=to_name,
        lineterm="",
    )
    return "\n".join(diff)


def compare_slide_models(old_model: Dict[str, Any], new_model: Dict[str, Any]) -> Dict[str, Any]:
    old_slides: List[Dict[str, Any]] = old_model.get("slides", [])
    new_slides: List[Dict[str, Any]] = new_model.get("slides", [])

    max_len = max(len(old_slides), len(new_slides))
    results: List[Dict[str, Any]] = []

    for i in range(max_len):
        if i >= len(old_slides):
            results.append(
                {
                    "index": i,
                    "status": "added",
                    "old": None,
                    "new": new_slides[i],
                }
            )
            continue

        if i >= len(new_slides):
            results.append(
                {
                    "index": i,
                    "status": "removed",
                    "old": old_slides[i],
                    "new": None,
                }
            )
            continue

        old_slide = old_slides[i]
        new_slide = new_slides[i]

        old_text = old_slide.get("text", "") or ""
        new_text = new_slide.get("text", "") or ""

        if old_text == new_text:
            results.append(
                {
                    "index": i,
                    "status": "same",
                    "old": {"text": old_text},
                    "new": {"text": new_text},
                }
            )
        else:
            diff = unified_diff(
                old_text,
                new_text,
                from_name=f"old_slide_{i}",
                to_name=f"new_slide_{i}",
            )
            results.append(
                {
                    "index": i,
                    "status": "changed",
                    "old": {"text": old_text},
                    "new": {"text": new_text},
                    "diff": diff,
                }
            )

    return {
        "old_slide_count": len(old_slides),
        "new_slide_count": len(new_slides),
        "slides": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two PPTX files and output diff_report.json."
    )
    # Preferred UX: pass two positional .pptx paths:
    #   python main.py old.pptx new.pptx
    parser.add_argument(
        "pptx_files",
        nargs="*",
        help="Two PPTX paths: old then new (e.g. old.pptx new.pptx).",
    )
    # Backward compatible flags (in case you already use these).
    parser.add_argument("--old", help="Path to the old pptx file.")
    parser.add_argument("--new", help="Path to the new pptx file.")
    parser.add_argument(
        "--out",
        default="diff_report.json",
        help="Output diff report JSON path (default: diff_report.json).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.old and args.new:
        old_path = Path(args.old)
        new_path = Path(args.new)
    elif len(args.pptx_files) == 2:
        old_path = Path(args.pptx_files[0])
        new_path = Path(args.pptx_files[1])
    else:
        raise SystemExit(
            "Usage: python main.py old.pptx new.pptx  OR  python main.py --old old.pptx --new new.pptx"
        )
    out_path = Path(args.out)

    if not old_path.exists():
        raise FileNotFoundError(f"Old file not found: {old_path}")
    if not new_path.exists():
        raise FileNotFoundError(f"New file not found: {new_path}")
    if old_path.suffix.lower() != ".pptx":
        raise ValueError(f"Old file must be a .pptx: {old_path}")
    if new_path.suffix.lower() != ".pptx":
        raise ValueError(f"New file must be a .pptx: {new_path}")

    old_prs = utils.load_presentation(str(old_path))
    new_prs = utils.load_presentation(str(new_path))

    old_model = utils.extract_presentation_model(old_prs)
    new_model = utils.extract_presentation_model(new_prs)

    diff_report = compare_slide_models(old_model, new_model)

    report = {
        "old": str(old_path),
        "new": str(new_path),
        "diff": diff_report,
    }

    utils.write_diff_report(report, str(out_path))
    print(f"Report saved: {out_path}")


if __name__ == "__main__":
    main()

