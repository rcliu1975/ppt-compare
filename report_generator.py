import base64
import os
import shutil
from pathlib import Path
from typing import Any, Dict

from jinja2 import Template


def image_to_base64(img_path: str) -> str:
    """Convert an image file to a base64 data URI string."""
    if not img_path or not os.path.exists(img_path):
        return ""
    with open(img_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        ext = os.path.splitext(img_path)[1][1:]
        if ext.lower() == 'jpg':
            ext = 'jpeg'
        return f"data:image/{ext};base64,{encoded_string}"


def generate_html_report(report_data: Dict[str, Any], output_path: str) -> None:
    """
    Generate a standalone HTML report with embedded base64 images.
    """
    # Embed images into the report_data
    if "diff" in report_data and "slides" in report_data["diff"]:
        for slide in report_data["diff"]["slides"]:
            if "diff_image_path" in slide and slide["diff_image_path"]:
                slide["diff_image_b64"] = image_to_base64(slide["diff_image_path"])
            if "new_image_path" in slide and slide["new_image_path"]:
                slide["new_image_b64"] = image_to_base64(slide["new_image_path"])
            if "old_image_path" in slide and slide["old_image_path"]:
                slide["old_image_b64"] = image_to_base64(slide["old_image_path"])

    template_str = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>PPT Compare Report</title>
        <style>
            body { font-family: sans-serif; margin: 2rem; background: #f9f9f9; color: #333; }
            h1 { color: #222; }
            .slide-card { background: white; padding: 1.5rem; margin-bottom: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            .status-same { border-left: 6px solid #4caf50; }
            .status-changed { border-left: 6px solid #ff9800; }
            .status-added { border-left: 6px solid #2196f3; }
            .status-removed { border-left: 6px solid #f44336; }
            .diff-img { max-width: 100%; height: auto; border: 1px solid #ddd; margin-top: 1rem; border-radius: 4px; }
            .text-diff { background: #f4f4f4; padding: 1rem; white-space: pre-wrap; font-family: monospace; border-radius: 4px; overflow-x: auto; }
            .header-info { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 2rem; }
        </style>
    </head>
    <body>
        <h1>Presentation Comparison Report</h1>
        <div class="header-info">
            <p><strong>Old File:</strong> {{ report.old }}</p>
            <p><strong>New File:</strong> {{ report.new }}</p>
            <p><strong>Total Slides (Old):</strong> {{ report.diff.old_slide_count }}</p>
            <p><strong>Total Slides (New):</strong> {{ report.diff.new_slide_count }}</p>
        </div>
        
        <h2>Slide Details</h2>
        {% for slide in report.diff.slides %}
            <div class="slide-card status-{{ slide.status }}">
                <h3>
                    {% if slide.index is not none %}New Slide {{ slide.index }}{% else %}N/A{% endif %}
                    {% if slide.old_index is not none %}(Old Slide {{ slide.old_index }}){% endif %}
                    - <span style="text-transform: uppercase;">{{ slide.status }}</span>
                </h3>
                <p><strong>Similarity Score:</strong> {{ slide.similarity_score }}</p>
                
                {% if slide.diff %}
                    <h4>Text Differences:</h4>
                    <div class="text-diff">{{ slide.diff }}</div>
                {% endif %}
                
                {% if slide.diff_image_b64 %}
                    <h4>Visual Differences (Old | New | Diff Mask):</h4>
                    <img class="diff-img" src="{{ slide.diff_image_b64 }}" alt="Visual Diff">
                {% elif slide.new_image_b64 %}
                    <h4>New Slide Image:</h4>
                    <img class="diff-img" src="{{ slide.new_image_b64 }}" alt="New Slide">
                {% elif slide.old_image_b64 %}
                    <h4>Old Slide Image:</h4>
                    <img class="diff-img" src="{{ slide.old_image_b64 }}" alt="Old Slide">
                {% endif %}
            </div>
        {% endfor %}
    </body>
    </html>
    """

    from jinja2 import Environment, select_autoescape
    env = Environment(autoescape=select_autoescape(['html', 'xml']))
    template = env.from_string(template_str)
    html_content = template.render(report=report_data)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def cleanup_temp_images(temp_dir: str) -> None:
    """Delete the temporary directory."""
    path = Path(temp_dir)
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
