#!/usr/bin/env python3
"""Funbox INDEX 測試版資料檢查器。

用途：
- 只檢查，不修改任何檔案。
- 不抓網路、不 commit、不改 index.html。
- 檢查 RULES.md、來源 latest.html 與 index.html 的一致性。

執行：
    python tools/check_index.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "RULES.md"
INDEX = ROOT / "index.html"
SOURCE = ROOT / "data" / "source" / "latest.html"

ALLOWED_REGIONS = {"台北市", "新北市", "桃園市", "新竹市", "新竹縣"}


def fail(message: str) -> None:
    print(f"ERROR: {message}")


def extract_rules_products(text: str) -> list[tuple[str, str]]:
    section = text.split("### 3.1 Tracked Products", 1)
    if len(section) != 2:
        raise ValueError("找不到 RULES.md 的 Tracked Products 區段")

    table = section[1].split("### 3.2 Active Products", 1)[0]
    products = []
    for line in table.splitlines():
        match = re.match(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$", line)
        if not match:
            continue
        code, name = match.groups()
        if code in {"型號代碼", "---"}:
            continue
        products.append((code, name))
    return products


def extract_js_products(text: str) -> dict[str, str]:
    match = re.search(r"const products=\{(.*?)\};", text, re.S)
    if not match:
        raise ValueError("找不到 index.html 的 products 定義")

    result = {}
    for key, value in re.findall(r'(\w+):"([^"]*)"', match.group(1)):
        if key in result:
            raise ValueError(f"INDEX products 出現重複 key：{key}")
        result[key] = value
    return result


def extract_shop_objects(text: str) -> list[str]:
    match = re.search(r"const shops=\[\n(.*?)\n\]\nconst regions=", text, re.S)
    if not match:
        raise ValueError("找不到 index.html 的 shops 定義")
    return re.findall(r'\{region:".*?\}', match.group(1), re.S)


def extract_shop_fields(shop: str) -> dict[str, str]:
    fields = {}
    for key, value in re.findall(r'(\w+):"([^"]*)"', shop):
        fields[key] = value
    return fields


def normalize_date_time(text: str) -> str:
    """將來源的完整日期時間轉成 INDEX 使用的顯示格式。"""
    text = re.sub(r"抽選/購買時間：", "", text).strip()

    def repl(match: re.Match[str]) -> str:
        return f"{int(match.group(2))}/{int(match.group(3))}"

    text = re.sub(r"(\d{4})/(\d{1,2})/(\d{1,2})", repl, text)
    return re.sub(r"\s+", "", text)


def normalize_model(product_name: str, product_keys: set[str]) -> str | None:
    """從來源商品名稱找出 INDEX 對應 key。"""
    match = re.search(r"\b(BXG|BGX|BX|UX|CX)\s*-\s*(\d{2})\b", product_name.upper())
    if not match:
        return None

    model = f"{match.group(1).replace('BGX', 'BXG')}-{match.group(2)}".lower()
    if model == "cx-00":
        if "新世紀福音戰士" in product_name:
            return "cx00eva" if "cx00eva" in product_keys else None
        if "迪卡狂怒" in product_name:
            return "cx00db" if "cx00db" in product_keys else None
        return None

    key = model.replace("-", "")
    return key if key in product_keys else None


def extract_source_records(text: str, product_keys: set[str]) -> list[dict[str, str]]:
    """解析來源 draw-store，回傳固定五地區內可對應到 INDEX 的商品資料。"""
    records = []
    starts = [m.start() for m in re.finditer(r'<div class="draw-store"[^>]*>', text)]

    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(text)
        block = text[start:end]

        city = re.search(r'data-draw-city="([^"]+)"', block)
        name = re.search(r'<div class="draw-store-name">([^<]+)</div>', block)
        draw_time = re.search(r'<div class="draw-start">([^<]+)</div>', block)
        if not city or not name or not draw_time:
            continue
        if city.group(1) not in ALLOWED_REGIONS:
            continue

        time = normalize_date_time(draw_time.group(1))
        for item in re.finditer(
            r'<div class="draw-item[^>]*data-draw-href="([^"]+)"[^>]*>.*?'
            r'<div class="draw-product">([^<]+)</div>',
            block,
            re.S,
        ):
            url, product_name = item.groups()
            key = normalize_model(product_name, product_keys)
            if key is None:
                continue
            records.append(
                {
                    "region": city.group(1),
                    "name": name.group(1).strip(),
                    "time": time,
                    "key": key,
                    "url": url.strip(),
                }
            )

    return records


def main() -> int:
    errors = 0
    print("Funbox INDEX 測試版檢查器")
    print("=" * 32)

    for path in (RULES, INDEX, SOURCE):
        if not path.exists():
            fail(f"找不到檔案：{path}")
            errors += 1

    if errors:
        return 1

    rules_text = RULES.read_text(encoding="utf-8")
    index_text = INDEX.read_text(encoding="utf-8")
    source_text = SOURCE.read_text(encoding="utf-8")

    try:
        rules_products = extract_rules_products(rules_text)
        js_products = extract_js_products(index_text)
        shop_texts = extract_shop_objects(index_text)
        shops = [extract_shop_fields(x) for x in shop_texts]
    except ValueError as exc:
        fail(str(exc))
        return 1

    print(f"RULES 追蹤商品：{len(rules_products)}")
    print(f"INDEX 商品定義：{len(js_products)}")
    print(f"INDEX 門市：{len(shops)}")

    # 0. 來源 ↔ INDEX：商品/門市/時間/LINE URL 必須一致。
    source_records = extract_source_records(source_text, set(js_products))
    print(f"來源固定 5 地區商品資料：{len(source_records)}")
    if not source_records:
        fail("來源 latest.html 沒有解析到固定 5 地區的商品資料")
        errors += 1
    else:
        print("PASS: 已解析來源固定 5 地區商品資料")

    product_keys = set(js_products)

    index_records = []
    for shop in shops:
        for key in product_keys:
            if key in shop:
                index_records.append({
                    "region": shop.get("region", ""),
                    "name": shop.get("name", ""),
                    "time": normalize_date_time(shop.get("time", "")),
                    "key": key,
                    "url": shop[key],
                })

    source_set = {(r["region"], r["name"], r["time"], r["key"], r["url"]) for r in source_records}
    index_set = {(r["region"], r["name"], r["time"], r["key"], r["url"]) for r in index_records}

    missing_from_index = sorted(source_set - index_set)
    missing_from_source = sorted(index_set - source_set)

    if missing_from_index:
        for region, name, time, key, url in missing_from_index:
            fail(f"來源有、INDEX 缺少：{region} / {name} / {js_products[key]} / {time} / {url}")
            errors += 1
    else:
        print("PASS: 來源商品資料都有對應 INDEX")

    if missing_from_source:
        for region, name, time, key, url in missing_from_source:
            fail(f"INDEX 有、來源沒有或資料不一致：{region} / {name} / {js_products[key]} / {time} / {url}")
            errors += 1
    else:
        print("PASS: INDEX 沒有來源以外的商品資料")

    # 1. RULES 商品名稱是否存在於 INDEX products。
    rule_names = {name for _, name in rules_products}
    index_names = set(js_products.values())

    # RULES 商品名稱是否存在於 INDEX products。\n    rule_names = {name for _, name in rules_products}\n    index_names = set(js_products.values())\n\n    # 已知正規化：RULES 的 UX-19 用「／子彈獅鷲H」，INDEX 統一顯示「子彈獅鷲」。\n    rule_names_normalized = {\n        name.replace("UX-19 子彈獅鷲／子彈獅鷲H", "UX-19 子彈獅鷲")\n        for name in rule_names\n    }\n\n    missing_names = sorted(rule_names_normalized - index_names)\n    extra_names = sorted(index_names - rule_names_normalized)\n\n    if missing_names:\n        for name in missing_names:\n            fail(f"RULES 商品不在 INDEX：{name}")\n            errors += 1\n    else:\n        print("PASS: RULES 商品都有對應 INDEX 商品")\n\n    if extra_names:
        for name in extra_names:
            fail(f"INDEX 出現未追蹤商品：{name}")
            errors += 1
    else:
        print("PASS: INDEX 沒有未追蹤商品")

    # 2. 商品 key 必須唯一。
    # extract_js_products 已在解析階段檢查重複 key。
    print("PASS: 商品 key 無重複")

    # 3. 門市地區。
    invalid_regions = sorted(
        {
            shop.get("region", "")
            for shop in shops
            if shop.get("region") not in ALLOWED_REGIONS
        }
    )
    if invalid_regions:
        for region in invalid_regions:
            fail(f"出現不允許的地區：{region!r}")
            errors += 1
    else:
        print("PASS: 所有門市都在固定 5 地區")

    # 4. 門市名稱 + 地區不得重複。
    seen_shops = set()
    for shop in shops:
        key = (shop.get("region"), shop.get("name"))
        if key in seen_shops:
            fail(f"門市重複：{key[0]} / {key[1]}")
            errors += 1
        seen_shops.add(key)

    if len(seen_shops) == len(shops):
        print("PASS: 門市名稱/地區無重複")

    # 5. 每筆商品 URL 都必須是 https://lin.ee/...。
    product_keys = set(js_products)
    url_errors = 0
    for shop in shops:
        for key, url in shop.items():
            if key not in product_keys:
                continue
            parsed = urlparse(url)
            if (
                parsed.scheme != "https"
                or parsed.netloc != "lin.ee"
                or not parsed.path.strip("/")
            ):
                fail(f"LINE URL 格式異常：{shop.get('name')} / {key} / {url}")
                errors += 1
                url_errors += 1

    if not url_errors:
        print("PASS: 所有 INDEX 商品 LINE URL 格式正常")

    # 6. 每個商品的資料筆數，並判斷 Active Products。
    counts = {key: 0 for key in js_products}
    duplicate_pairs = set()
    for shop in shops:
        for key in product_keys:
            if key not in shop:
                continue
            counts[key] += 1
            pair = (shop.get("region"), shop.get("name"), key)
            if pair in duplicate_pairs:
                fail(f"同一門市/商品重複資料：{pair}")
                errors += 1
            duplicate_pairs.add(pair)

    active = {key for key, count in counts.items() if count}
    inactive = sorted(key for key, count in counts.items() if not count)

    print(f"Active Products：{len(active)}")
    if inactive:
        print("未出現在任何門市的 RULES/INDEX 商品（不視為錯誤）：")
        for key in inactive:
            print(f"  - {js_products[key]}")

    # 7. 同型號不同名稱的 CX-00 必須分開。
    cx00 = [name for name in js_products.values() if name.startswith("CX-00 ")]
    expected = {"CX-00 新世紀福音戰士陀螺套組", "CX-00 迪卡狂怒"}
    if expected.issubset(cx00):
        print("PASS: CX-00 不同商品有分開處理")
    else:
        fail("CX-00 不同商品未完整分開處理")
        errors += 1

    print("=" * 32)
    if errors:
        print(f"FAIL: 共 {errors} 個問題")
        return 1

    print("PASS: 測試版檢查完成，未發現問題")
    return 0


if __name__ == "__main__":
    sys.exit(main())
