def build_market_insight(platform_results: list) -> str:
    if not platform_results:
        return "市場資料不足，無法生成洞察報告。"

    total_reviews = sum(
        r.review_count or 0 for _, r in platform_results if r.review_count
    )
    ratings = [r.rating for _, r in platform_results if r.rating is not None]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    lines = ["# 市場洞察\n"]
    lines.append(f"- 涵蓋平台數：{len(platform_results)}")
    lines.append(f"- 合計評論 / 票數：{total_reviews:,}")
    if avg_rating:
        lines.append(f"- 各平台平均評分：{avg_rating}")

    platforms = [p for p, _ in platform_results]
    if "app_store" in platforms and "google_play" in platforms:
        lines.append("- 此產品同時上架 iOS 及 Android，顯示有跨平台用戶基礎。")
    if "product_hunt" in platforms:
        lines.append("- 已在 Product Hunt 曝光，具備科技早期採用者受眾。")

    lines.append("\n> 以上為自動化分析，建議人工複核後使用。")
    return "\n".join(lines)
