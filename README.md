# PPT Compare (JSON)

This is an MVP project that compares two `.pptx` files by extracting slide text and outputting a JSON report.

## Development Plan

See [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md) for the current development plan.

## Prerequisites

1. Install WinPython (already done on your side).
2. Use the WinPython command prompt (or any prompt where the WinPython `python.exe` is the one being used).

## Setup

From the project folder:

```bash
pip install -r requirements.txt
```

## Run

Two positional `.pptx` paths (old, then new). Default output is `diff_report.json` in the current directory:

```bash
python main.py "path/to/old.pptx" "path/to/new.pptx"
```

Optional flags (same behavior):

```bash
python main.py --old "path/to/old.pptx" --new "path/to/new.pptx" --out "diff_report.json"
```

If your `python` command is not available in your current shell, use the WinPython Python executable directly (example):

```bash
"D:\path\to\python.exe" main.py "path\to\old.pptx" "path\to\new.pptx"
```

## Output format (high level)

The generated `diff_report.json` includes:

1. `old`, `new`: input file paths
2. `diff`: slide-by-slide comparison
3. For each slide index:
   - `same`: text matches
   - `changed`: text differs + a unified diff of lines
   - `added` / `removed`: slide count mismatch

