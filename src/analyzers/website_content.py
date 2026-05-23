import os

import anthropic


def analyze_website_content(title: str, description: str) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = f"""以下是一個競品軟體的英文資訊：
標題：{title}
說明：{description}

請用繁體中文回答：
1. 用 2-3 句話說明這個產品的定位和核心功能（大意）
2. 列出 3-5 個產品特點（每條一行，以「・」開頭）

格式（嚴格遵守，不要加其他內容）：
大意：<2-3句描述>
特點：
・<特點1>
・<特點2>
・<特點3>"""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()

    summary = ""
    features = ""
    if "大意：" in raw and "特點：" in raw:
        parts = raw.split("特點：", 1)
        summary = parts[0].replace("大意：", "").strip()
        features = parts[1].strip()
    else:
        summary = raw

    return {"summary_zh": summary, "features_zh": features}
