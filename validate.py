#!/usr/bin/env python3
"""Read-only validation for the Funbox INDEX."""

from __future__ import annotations

import re
import sys
from pathlib import Path

RULES = Path("RULES.md")
INDEX = Path("index.html")
FIXED_REGIONS = {"台北市", "新北市", "桃園市", "新竹市", "新竹縣"}


def parse_rules_products(text: str) -> list[str]:
    products = []
    in_table = False
    for line in text.splitlines():
        if line.strip().startswith("| 型號代碼 |"):
            in_table = True
            continue
        if in_table:
            if not line.strip().startswith("|"):
                break
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[0] not in {"型號代碼", "---"}:
                products.append(cells[1])
    return products


def main() -> int:
    errors: list[str] = []
    rules_text = RULES.read_text(encoding="utf-8")
    index_text = INDEX.read_text(encoding="utf-8")

    tracked = parse_rules_products(rules_text)
    if not tracked:
        errors.append("RULES.md：找不到指定追蹤商品表。")
    tracked_set = set(tracked)

    product_match = re.search(r"const products=\{(.*?)\};", index_text, re.S)
    if not product_match:
        errors.append("INDEX：找不到 const products。")
        products = {}
    else:
        products = dict(re.findall(r'(\w+):\s*"([^"]+)"', product_match.group(1)))

    index_product_set = set(products.values())
    for name in index_product_set:
        if name not in tracked_set:
            errors.append(f"INDEX 商品未列入 RULES：{name}")

    if "UX-19 子彈獅鷲H" in index_product_set:
        errors.append("INDEX：UX-19 子彈獅鷲H 應統一顯示為 UX-19 子彈獅鷲。")
    if "CX-00 迪卡狂怒 FT3-60T" in index_product_set:
        errors.append("INDEX：CX-00 迪卡狂怒 FT3-60T 應統一顯示為 CX-00 迪卡狂怒。")

    shops_match = re.search(r"const shops=\[(.*?)\];\s*const regions=", index_text, re.S)
    if not shops_match:
        errors.append("INDEX：找不到 const shops。")
        shops = []
    else:
        shops = re.findall(
            r'\{region:"([^"]+)",name:"([^"]+)",time:"([^"]+)"(.*?)\}',
            shops_match.group(1),
            re.S,
        )

    seen_shops: set[tuple[str, str]] = set()
    for region, name, time, rest in shops:
        if region not in FIXED_REGIONS:
            errors.append(f"INDEX：出現固定 5 地區以外的地區：{region} / {name}")
        key = (region, name)
        if key in seen_shops:
            errors.append(f"INDEX：門市重複：{region} / {name}")
        seen_shops.add(key)
        if not time.strip():
            errors.append(f"INDEX：門市沒有抽選時間：{region} / {name}")
        for key_name, url in re.findall(r',([a-zA-Z]\w*):"([^"]+)"', rest):
            if key_name not in products:
                errors.append(f"INDEX：{region} / {name} 使用未知商品 key：{key_name}")
            if not url.startswith("https://lin.ee/"):
                errors.append(f"INDEX：{region} / {name} 的 LINE 連結格式異常：{url}")

    regions_match = re.search(r'const regions=\[(.*?)\];', index_text, re.S)
    if regions_match:
        regions = re.findall(r'"([^"]+)"', regions_match.group(1))
        if set(regions) != FIXED_REGIONS or len(regions) != len(FIXED_REGIONS):
            errors.append(f"INDEX：regions 必須恰好為固定 5 地區，目前為：{regions}")
    else:
        errors.append("INDEX：找不到 const regions。")

    if errors:
        print("❌ Validation failed")
        for error in errors:
            print(f"- {error}")
        return 1

    print("✅ RULES 商品清單可讀")
    print(f"✅ INDEX 商品均屬 RULES 指定追蹤商品（{len(index_product_set)} 個）")
    print("✅ UX-19 / CX-00 名稱正規化規則通過")
    print(f"✅ 固定 5 地區與門市結構通過（{len(shops)} 家）")
    print("✅ LINE 連結格式通過")
    print("✅ validate.py 為唯讀檢查，不會修改 INDEX")
    print("Validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
