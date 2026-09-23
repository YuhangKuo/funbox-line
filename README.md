# Funbox 抽陀螺

整理 Funbox／來玩聚抽陀螺的指定商品、門市、抽選時間與 LINE 連結。

## 資料流程

目前採用「**先鏡像來源，再更新 INDEX**」：

```text
UXUX11/funbox-line（來源 Repo）
        ↓
data/source/latest.html
        ↓
RULES.md 驗證／商品與門市正規化
        ↓
INDEX（index.html）
        ↓
GitHub Pages
```

來源 Repo 的 Git 歷史本身就是來源快照的版本紀錄；本專案另外保存目前使用的來源快照與上游 commit 資訊。

### 來源同步

GitHub Actions 會定期從來源 Repo 的 `main/index.html` 建立：

- `data/source/latest.html`：目前來源原始 HTML 快照
- `data/source/latest.json`：來源 Repo、上游 commit、抓取時間等 metadata

因此日後更新 INDEX 時，不直接依賴來源 GitHub Pages 是否能即時開啟，而是先使用已同步到本 Repo 的來源快照。

## 主要操作

### 新增追蹤商品

> **「新增追蹤商品 XXX」**

依 RULES.md 確認商品後加入追蹤清單，並同步核對 INDEX。

### 更新 INDEX

> **「更新 INDEX」**

按照 RULES.md：

1. 先確認來源 Repo 的最新快照。
2. 再建立固定 5 地區完整門市母集合。
3. 核對 Tracked Products 與 Active Products。
4. 最後更新 INDEX 並 commit。

## 目前商品清單

目前 RULES.md 指定追蹤的商品如下：

- BX-00 — BX-00 蒼龍神劍
- BX-09 — BX-09 戰鬥通行證
- BX-10 — BX-10 極限衝擊戰鬥盤
- BX-35 — BX-35 隨機強化組Vol.04
- BX-48 — BX-48 隨機強化組Vol.09
- BX-50 — BX-50 天堂日輪
- UX-03 — UX-03 魔導神杖
- UX-15 — UX-15 鮫鯊狂鱗改造組
- UX-16 — UX-16 時鐘幻象 隨機強化組
- UX-19 — UX-19 子彈獅鷲
- UX-20 — UX-20 榮耀武神
- UX-21 — UX-21 惡魔冥界改造組
- CX-00 — CX-00 新世紀福音戰士陀螺套組
- CX-00 — CX-00 迪卡狂怒
- CX-07 — CX-07 天馬爆擊
- CX-11 — CX-11 帝王威能
- CX-19 — CX-19 鱷魚裂甲
- CX-16 — CX-16 極限衝擊對戰組C

> UX-19 子彈獅鷲H 與 UX-19 子彈獅鷲視為同一個追蹤商品，INDEX 統一顯示 UX-19 子彈獅鷲。
>
> CX-00 迪卡狂怒 FT3-60T 統一視為 CX-00 迪卡狂怒。

## 核心規則

- 只追蹤 RULES.md 指定商品。
- 來源出現其他商品，不自動加入 INDEX。
- RULES.md 是追蹤清單，不代表所有商品都必須出現在 INDEX 的商品選單。
- 更新 INDEX 時，只有最新來源在固定 5 地區有可確認資料的商品才顯示在 INDEX。
- 固定地區：台北市、新北市、桃園市、新竹市、新竹縣。
- 相同型號、不同商品名稱分開處理。
- 不確定的資料不猜、不改。
- 以最新來源為準，採最小必要修改。

## 資料來源

- 來源 Repo：https://github.com/UXUX11/funbox-line
- 來源 GitHub Pages：https://uxux11.github.io/funbox-line/
- 本專案 GitHub：https://github.com/YuhangKuo/funbox-line
- 本專案網站：https://yuhangkuo.github.io/funbox-line/
