import os
import json
import time
import hashlib
import logging
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("narrative_stream")

DB_URL = os.getenv("DB_URL", "postgresql://user:pass@localhost:5432/crypto")
engine = create_engine(DB_URL)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

PROMPT_VERSION = "narrative_v1.2"

SYSTEM_PROMPT = f"""
You are a quantitative crypto market analyst.

PROMPT_VERSION = {PROMPT_VERSION}

You MUST return STRICT JSON in the following shape:

{{
  "narratives": [
    {{
      "narrative_id": "AI_TOKENS",
      "heat_score": 0.9,
      "sentiment_score": 0.8,
      "novelty_score": 0.7,
      "coherence_score": 0.9,
      "tokens": ["TAO", "FET", "RNDR", "GRT"],
      "token_strengths": [0.95, 0.9, 0.85, 0.8],
      "token_direction_bias": [0.8, 0.75, 0.7, 0.65]
    }},
    ...
  ]
}}

Rules:
- 3–10 narratives max.
- 3–15 tokens per narrative max.
- Use UPPER_SNAKE_CASE for narrative_id.
- Tokens must be real crypto tickers; if unsure, omit them.
- No prose, no markdown. JSON ONLY.
"""

USER_PROMPT = """
Consider BTC, ETH, SOL, AI tokens, RWA tokens, L1 rotation, meme coins, restaking, DeFi.

Based on the last 24h of crypto price action, derivatives, and news (assume you have context),
identify 3–10 narratives and output them in the required JSON format only.
"""


def safe_openai_call(max_retries=3, backoff_seconds=2):
    last_error = None
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT},
                ],
                response_format={"type": "json_object"},
                max_tokens=1200,
            )
            text = resp.choices[0].message.content
            return text, json.loads(text)
        except Exception as e:
            last_error = e
            log.warning(f"[NARR] OpenAI error attempt {attempt+1}: {e}")
            time.sleep(backoff_seconds * (attempt + 1))
    raise RuntimeError(f"OpenAI narrative call failed after retries: {last_error}")


def run_narrative_stream():
    raw_text, data = safe_openai_call()
    fingerprint = hashlib.md5(raw_text.encode("utf-8")).hexdigest()

    ts = datetime.now(timezone.utc).replace(microsecond=0)
    narratives_rows = []
    nar_assets_rows = []

    narratives = data.get("narratives", []) or []
    for n in narratives:
        nid = n.get("narrative_id")
        if not nid:
            continue

        narratives_rows.append({
            "ts": ts,
            "narrative_id": nid,
            "heat_score": n.get("heat_score"),
            "sentiment_score": n.get("sentiment_score"),
            "novelty_score": n.get("novelty_score"),
            "coherence_score": n.get("coherence_score"),
            "narrative_fingerprint": fingerprint,
        })

        tokens = n.get("tokens", []) or []
        strengths = n.get("token_strengths", []) or []
        biases = n.get("token_direction_bias", []) or []

        m = min(len(tokens), len(strengths), len(biases))
        if m == 0:
            continue

        for tok, s, b in zip(tokens[:m], strengths[:m], biases[:m]):
            tok = str(tok).strip().upper()
            symbol = f"{tok}/USDT"
            nar_assets_rows.append({
                "ts": ts,
                "narrative_id": nid,
                "symbol": symbol,
                "strength": float(s),
                "direction_bias": float(b),
            })

    try:
        if narratives_rows:
            pd.DataFrame(narratives_rows).to_sql(
                "narratives", engine, if_exists="append", index=False
            )
        if nar_assets_rows:
            pd.DataFrame(nar_assets_rows).to_sql(
                "narrative_assets", engine, if_exists="append", index=False
            )
        log.info(
            f"[NARR] {ts} fp={fingerprint} saved "
            f"{len(narratives_rows)} narratives, {len(nar_assets_rows)} links"
        )
    except IntegrityError:
        # Duplicate fingerprint → identical snapshot, ignore
        log.info(f"[NARR] {ts} fp={fingerprint} duplicate, skipping inserts")


if __name__ == "__main__":
    run_narrative_stream()
