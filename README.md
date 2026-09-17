# Funbox 抽陀螺資料整理

本專案用於整理 Funbox／來玩聚抽陀螺相關資料。

## 作業規則

專案的詳細資料核對與修改規則請先閱讀 [`RULES.md`](RULES.md)。

## 下指令的方法

之後要我協助更新專案時，可以直接使用以下指令。

### 1. 更新商品型號紀錄

> 先更新 RULES.md 的商品型號紀錄。

用途：先查最新資料來源，確認 BX／UX／CX 型號，更新 `RULES.md` 的完整型號紀錄；這一步不修改 `index.html`。

### 2. 更新商品型號並同步 INDEX

> 先更新 RULES.md 的商品型號紀錄，再依最新販售狀態同步 INDEX，最後 commit。

處理方式：
- 新確認的型號加入 `RULES.md`。
- `RULES.md` 保留完整的商品型號紀錄，即使目前沒有販售。
- 目前沒有販售的型號，從 `index.html` 移除。
- 目前有販售的型號，依來源資料保留在 `index.html`。
- 不因完整商品名稱不同而重複建立相同型號代碼。

### 3. 全面核對並更新

> 按照 RULES.md 全面核對 Funbox，更新商品型號、門市、抽選時間、商品與 LINE 連結，有問題就修正並 commit。

這會依 `RULES.md` 的完整流程進行來源核對與最小必要修改。

### 4. 只檢查、不修改

> 按照 RULES.md 核對目前資料，有問題先告訴我，不要修改也不要 commit。

適合在正式更新前先查看差異。

### 5. 只更新型號、不動其他資料

> 只更新商品型號，按照 RULES.md 核對來源，更新 MD 和 INDEX，其他資料不要動。

只處理型號相關資料，不重新整理門市、時間或其他 UI／功能。

## 資料來源

- 資料來源：<https://uxux11.github.io/funbox-line/>
- GitHub：<https://github.com/YuhangKuo/funbox-line>
- 網站：<https://yuhangkuo.github.io/funbox-line/>
