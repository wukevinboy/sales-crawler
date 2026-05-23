def build_competitor_summary(app_name: str, platform_results: list) -> str:
    if not platform_results:
        return f"未找到 {app_name} 的競品資料。"

    lines = [f"# {app_name} 競品分析摘要\n"]
    for platform, res in platform_results:
        platform_label = {"app_store": "App Store (iOS)", "google_play": "Google Play", "product_hunt": "Product Hunt"}.get(platform, platform)
        lines.append(f"## {platform_label}")
        lines.append(f"- 名稱：{res.app_name}")
        if res.rating is not None:
            lines.append(f"- 評分：{res.rating}")
        if res.review_count is not None:
            lines.append(f"- 評論數 / 票數：{res.review_count:,}")
        if hasattr(res, "installs") and res.installs:
            lines.append(f"- 下載量：{res.installs}")
        lines.append("")

    return "\n".join(lines)
