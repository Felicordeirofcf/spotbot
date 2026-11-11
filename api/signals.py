"""Função serverless da Vercel: varre o mercado e devolve os sinais em JSON.

Somente leitura: usa apenas dados PÚBLICOS de mercado da Binance.
Não usa chave de API e não envia ordens.
"""
from __future__ import annotations

import json
import sys
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot.binance_client import BinanceClient  # noqa: E402
from bot.config import Config  # noqa: E402
from bot.scanner import EXCLUDED_BASES, LEVERAGED_SUFFIXES, scan  # noqa: E402

# Endpoint oficial da Binance só para dados públicos de mercado
MARKET_DATA_URLS = ("https://data-api.binance.vision", "https://api.binance.com")
TOP_N = 40


def top_symbols(client: BinanceClient, cfg: Config) -> list[str]:
    """Pares em USDT mais negociados, sem stablecoins/alavancados (sem baixar exchangeInfo)."""
    q = cfg.quote_asset
    rows = []
    for t in client.ticker_24h():
        sym = t["symbol"]
        if not sym.endswith(q):
            continue
        base = sym[: -len(q)]
        if base in EXCLUDED_BASES or (base.endswith(LEVERAGED_SUFFIXES) and len(base) > 4):
            continue
        vol = float(t["quoteVolume"])
        # pares sem negociação recente aparecem com volume zero/count zero
        if vol >= cfg.min_24h_volume_quote and int(t.get("count", 1)) > 0:
            rows.append((vol, sym, t))
    rows.sort(reverse=True)
    return [s for _, s, _ in rows[: cfg.top_n_symbols]]


def build_payload(client: BinanceClient, cfg: Config) -> dict:
    started = time.time()
    symbols = top_symbols(client, cfg)
    signals, analyzed = scan(client, cfg, symbols, workers=10)
    return {
        "generated_at": int(time.time() * 1000),
        "took_ms": int((time.time() - started) * 1000),
        "analyzed": analyzed,
        "params": {"take_profit_pct": cfg.take_profit_pct, "stop_loss_pct": cfg.stop_loss_pct,
                   "fee_pct": cfg.fee_pct, "quote": cfg.quote_asset},
        "signals": [{"symbol": s.symbol, "entry": s.entry, "take_profit": s.take_profit, "stop": s.stop,
                     "score": round(s.score, 1), "reasons": s.reasons} for s in signals],
    }


def config_from_query(query: str) -> Config:
    cfg = Config(top_n_symbols=TOP_N)
    qs = parse_qs(query)
    values = {}
    if "tp" in qs:
        values["take_profit_pct"] = qs["tp"][0]
    if "sl" in qs:
        values["stop_loss_pct"] = qs["sl"][0]
    if values:
        cfg.update(values)  # valida faixas; ValueError se inválido
    return cfg


class handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict, cache: str) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", cache)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            cfg = config_from_query(urlparse(self.path).query)
        except (ValueError, TypeError) as exc:
            return self._send(400, {"error": str(exc)}, "no-store")
        last_error = None
        for url in MARKET_DATA_URLS:
            try:
                payload = build_payload(BinanceClient(base_url=url), cfg)
                payload["source"] = url
                # CDN da Vercel guarda por 2 min e serve versão anterior enquanto atualiza
                return self._send(200, payload, "public, s-maxage=120, stale-while-revalidate=600")
            except Exception as exc:
                last_error = exc
        self._send(502, {"error": f"Falha ao consultar a Binance: {last_error}"}, "no-store")
