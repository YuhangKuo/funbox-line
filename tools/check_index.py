#!/usr/bin/env python3
"""Funbox INDEX 測試版資料檢查器。

用途：
- 只檢查，不修改任何檔案。
- 不抓網路、不 commit、不改 index.html。
- 目前針對 RULES.md 與 index.html 做基本一致性檢查。

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


def main() -> int:
    errors = 0
    print("Funbox INDEX 測試版檢查器")
    print("=" * 32)

    for path in (RULES, INDEX):
        if not path.exists():
            fail(f"找不到檔案：{path}")
            errors += 1

    if errors:
        return 1

    rules_text = RULES.read_text(encoding="utf-8")
    index_text = INDEX.read_text(encoding="utf-8")

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

    # 1. RULES 商品名稱是否存在於 INDEX products。
    rule_names = {name for _, name in rules_products}
    index_names = set(js_products.values())

    # 已知正規化：RULES 的 UX-19 用「／子彈獅鷲H」，INDEX 統一顯示「子彈獅鷲」。
    rule_names_normalized = {
        name.replace("UX-19 子彈獅鷲／子彈獅鷲H", "UX-19 子彈獅鷲")
        for name in rule_names
    }

    missing_names = sorted(rule_names_normalized - index_names)
    extra_names = sorted(index_names - rule_names_normalized)

    if missing_names:
        for name in missing_names:
            fail(f"RULES 商品不在 INDEX：{name}")
            errors += 1
    else:
        print("PASS: RULES 商品都有對應 INDEX 商品")

    if extra_names:
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
