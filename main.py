from __future__ import annotations

import argparse
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional

from tqdm import tqdm

import utils
import visualizer
import cv_compare
import report_generator


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

    results: List[Dict[str, Any]] = []
    
    SIMILARITY_THRESHOLD = 0.6

    unmatched_old = list(range(len(old_slides)))
    unmatched_new = list(range(len(new_slides)))

    matches = [] # (old_idx, new_idx, score)

    # 1. Exact matches first (for speed and accuracy)
    for n_idx in unmatched_new[:]:
        n_text = new_slides[n_idx].get("text", "") or ""
        best_o_idx = -1
        for o_idx in unmatched_old:
            o_text = old_slides[o_idx].get("text", "") or ""
            if o_text == n_text:
                best_o_idx = o_idx
                break
        if best_o_idx != -1:
            matches.append((best_o_idx, n_idx, 1.0))
            unmatched_old.remove(best_o_idx)
            unmatched_new.remove(n_idx)

    # 2. Similarity matches
    for n_idx in unmatched_new[:]:
        n_text = new_slides[n_idx].get("text", "") or ""
        best_o_idx = -1
        best_score = 0.0
        
        for o_idx in unmatched_old:
            o_text = old_slides[o_idx].get("text", "") or ""
            score = difflib.SequenceMatcher(None, o_text, n_text).ratio()
            if score > best_score:
                best_score = score
                best_o_idx = o_idx
                
        if best_score >= SIMILARITY_THRESHOLD and best_o_idx != -1:
            matches.append((best_o_idx, n_idx, best_score))
            unmatched_old.remove(best_o_idx)
            unmatched_new.remove(n_idx)

    # Construct the results
    for old_idx, new_idx, score in matches:
        old_text = old_slides[old_idx].get("text", "") or ""
        new_text = new_slides[new_idx].get("text", "") or ""
        
        if score == 1.0:
            results.append({
                "index": new_idx,
                "old_index": old_idx,
                "status": "same",
                "similarity_score": score,
                "old": {"text": old_text},
                "new": {"text": new_text},
            })
        else:
            diff = unified_diff(
                old_text,
                new_text,
                from_name=f"old_slide_{old_idx}",
                to_name=f"new_slide_{new_idx}",
            )
            results.append({
                "index": new_idx,
                "old_index": old_idx,
                "status": "changed",
                "similarity_score": round(score, 4),
                "old": {"text": old_text},
                "new": {"text": new_text},
                "diff": diff,
            })
            
    for n_idx in unmatched_new:
        new_text = new_slides[n_idx].get("text", "") or ""
        results.append({
            "index": n_idx,
            "old_index": None,
            "status": "added",
            "similarity_score": 0.0,
            "old": None,
            "new": {"text": new_text},
        })
        
    for o_idx in unmatched_old:
        old_text = old_slides[o_idx].get("text", "") or ""
        results.append({
            "index": None,
            "old_index": o_idx,
            "status": "removed",
            "similarity_score": 0.0,
            "old": {"text": old_text},
            "new": None,
        })
        
    # Sort results to be user-friendly: main flow by new index, then removed at the end
    def sort_key(r: Dict[str, Any]) -> tuple[int, int]:
        idx = r.get("index")
        if idx is not None:
            return (0, idx)
        else:
            return (1, r.get("old_index", 0))
            
    results.sort(key=sort_key)

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

    print("Rendering old PPTX to images...")
    old_images = visualizer.render_pptx_slides(str(old_path), "temp_images/old")
    print("Rendering new PPTX to images...")
    new_images = visualizer.render_pptx_slides(str(new_path), "temp_images/new")

    print("Extracting text models...")
    old_prs = utils.load_presentation(str(old_path))
    new_prs = utils.load_presentation(str(new_path))

    old_model = utils.extract_presentation_model(old_prs)
    new_model = utils.extract_presentation_model(new_prs)

    print("Comparing texts...")
    diff_report = compare_slide_models(old_model, new_model)
    
    Path("temp_images/diffs").mkdir(parents=True, exist_ok=True)
    
    print("Comparing images...")
    for slide in tqdm(diff_report["slides"], desc="Comparing Slides"):
        o_idx = slide.get("old_index")
        n_idx = slide.get("index")
        
        old_img_path = old_images[o_idx] if o_idx is not None and o_idx < len(old_images) else None
        new_img_path = new_images[n_idx] if n_idx is not None and n_idx < len(new_images) else None
        
        slide["old_image_path"] = old_img_path
        slide["new_image_path"] = new_img_path
        
        if slide["status"] in ["same", "changed"] and old_img_path and new_img_path:
            diff_img_out = f"temp_images/diffs/diff_{o_idx}_{n_idx}.png"
            images_are_same = cv_compare.compare_images(old_img_path, new_img_path, diff_img_out)
            if not images_are_same:
                slide["diff_image_path"] = diff_img_out

    report = {
        "old": str(old_path),
        "new": str(new_path),
        "diff": diff_report,
    }

    utils.write_diff_report(report, str(out_path))
    print(f"JSON Report saved: {out_path}")
    
    html_out = out_path.with_suffix('.html')
    report_generator.generate_html_report(report, str(html_out))
    print(f"HTML Report saved: {html_out}")
    
    print("Cleaning up temporary images...")
    report_generator.cleanup_temp_images("temp_images")


if __name__ == "__main__":
    main()

