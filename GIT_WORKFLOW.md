# Git Workflow for Solo Development

這份文件整理 `ppt-compare` 在單人開發時建議採用的 Git 工作流程。

## 核心原則

- `main` 盡量保持在可執行、可交付的狀態
- 小改動可以直接在 `main` 進行
- 較大的功能或實驗性改動，建議使用功能分支
- 每次改完一小段就 commit，不要把很多不同目的的修改混成一個 commit
- 只要有進度就可以 push，把 GitHub 當作備份點

## 什麼時候直接用 `main`

適合這些情況：

- 修改 `README.md`
- 修小 bug
- 調整小段邏輯
- 更新設定或文件

建議流程：

```bash
git pull origin main
git status

# 修改程式

git add .
git commit -m "Fix slide text extraction"
git push origin main
```

這種做法最簡單，適合變更範圍小、風險低的工作。

## 什麼時候開功能分支

適合這些情況：

- 新增完整功能
- 重構程式結構
- 嘗試還不確定是否要保留的做法
- 可能需要幾天才完成的工作

例如：

- 加入 HTML 報告輸出
- 加入圖片差異比對
- 調整 CLI 參數設計

建議流程：

```bash
git checkout main
git pull origin main
git checkout -b codex/add-html-report

# 修改程式

git add .
git commit -m "Add HTML report generation"
git push -u origin codex/add-html-report
```

功能確認完成後，再合併回 `main`：

```bash
git checkout main
git pull origin main
git merge codex/add-html-report
git push origin main
```

最後清理分支：

```bash
git branch -d codex/add-html-report
git push origin --delete codex/add-html-report
```

## 為什麼 `main` 雖然能回退，還是建議有時開分支

直接在 `main` 開發不是不行，因為 Git 本來就能回退。

但分支的價值在於先把風險隔離，而不是等出錯後再補救：

- `main` 可以一直維持穩定版本
- 分支上可以放心嘗試和修改
- 如果某個功能做一半想放棄，直接刪分支就好
- 功能完成後再合併，歷史會更清楚

簡單說：

- 回退是事後補救
- 分支是事前隔離

## 推薦給這個專案的實際做法

`ppt-compare` 目前規模不大，建議用下面這個判斷方式：

- 文件更新、小修正：直接在 `main`
- 新功能、重構、實驗：開 `codex/...` 分支

## 常用指令

查看狀態：

```bash
git status
```

查看差異：

```bash
git diff
```

查看提交紀錄：

```bash
git log --oneline --decorate --graph -10
```

回退單一 commit 的影響，保留歷史：

```bash
git revert <commit_sha>
```

把目前工作先暫存：

```bash
git stash
git stash pop
```

## 建議的 commit 習慣

- 一個 commit 只做一件主要事情
- commit 訊息用動詞開頭
- 優先寫清楚「做了什麼」

例如：

- `Add HTML report generation`
- `Fix slide comparison ordering`
- `Update development plan`
- `Refactor JSON diff output`

## 簡短結論

單人專案不一定要走很重的 Git 流程，但建議保留基本紀律：

- 小改動直接進 `main`
- 大改動先開分支
- 常 commit
- 常 push

這樣流程不會太麻煩，又能保留足夠的安全性。
