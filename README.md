# PPT Compare（JSON 版）

這是一個 MVP 專案，用來比對兩個 `.pptx` 檔案的投影片文字內容，並輸出 `JSON` 報告。

目前功能重點： test

1. 讀取兩個 `.pptx` 檔案
2. 抽取每頁投影片的文字
3. 逐頁比對文字差異
4. 輸出 `diff_report.json`

## 目前限制

- 只支援 `.pptx`
- 不支援舊版 `.ppt`
- 目前是「依投影片索引逐頁比對」，還沒有做相似投影片重新配對
- 目前只比對文字，不比對圖片、版面或像素差異

## 開發規畫

目前的功能規畫請參考 [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md)。

## Git 工作流程

建議的單人開發流程請參考 [GIT_WORKFLOW.md](./GIT_WORKFLOW.md)。

## 環境需求

- Python 3.10 以上
- `python-pptx`

## 安裝

在專案目錄內執行：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

如果你已經有自己的 Python 環境，也可以直接安裝：

```bash
python3 -m pip install -r requirements.txt
```

## 執行方式

### 直接帶入檔案路徑

預設輸出檔名為目前目錄下的 `diff_report.json`：

```bash
python main.py "path/to/old.pptx" "path/to/new.pptx"
```

也可以明確指定參數名稱：

```bash
python main.py --old "path/to/old.pptx" --new "path/to/new.pptx" --out "diff_report.json"
```

如果你的 shell 沒有把虛擬環境設成預設，可直接用：

```bash
./.venv/bin/python main.py "path/to/old.pptx" "path/to/new.pptx"
```

## `.env` 操作方式

目前程式本身不會自動讀取 `.env`，也沒有內建 `dotenv` 載入邏輯。

`.env` 的用途是讓你在 shell 中集中管理輸入參數，避免每次手動重打一長串路徑。

### 建立 `.env`

你可以在專案根目錄建立一個 `.env`：

```dotenv
OLD_PPTX=../ppt/old_version.pptx
NEW_PPTX=../ppt/new_version.pptx
OUT_JSON=diff_report.json
```

### 在 shell 載入 `.env`

```bash
set -a
source .env
set +a
```

### 使用 `.env` 內的變數執行

```bash
./.venv/bin/python main.py "$OLD_PPTX" "$NEW_PPTX" --out "$OUT_JSON"
```

## 輸出格式

產生的 `diff_report.json` 目前包含：

1. `old`：舊版檔案路徑
2. `new`：新版檔案路徑
3. `diff`：整體比對結果

`diff.slides` 中每一頁會包含：

- `index`：投影片索引
- `status`：比對狀態
- `old` / `new`：該頁擷取出的文字內容
- `diff`：當狀態為 `changed` 時，提供 unified diff 內容

目前 `status` 可能值：

- `same`：文字相同
- `changed`：文字不同
- `added`：新版多出該頁
- `removed`：新版少了該頁
