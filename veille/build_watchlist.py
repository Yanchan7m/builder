"""
Génère watchlist.yaml = NASDAQ-100 + S&P 500, avec le CIK SEC de chaque société.

À lancer une fois (ou de temps en temps pour rafraîchir) :
    python3 build_watchlist.py

Sources (toutes gratuites et officielles/publiques) :
  - S&P 500   : CSV maintenu (datasets/s-and-p-500-companies)
  - NASDAQ-100: liste figée ci-dessous (change rarement)
  - CIK SEC   : fichier officiel ticker -> CIK de la SEC

Le CIK est l'identifiant d'une société à la SEC : il servira à l'Étape 2
pour surveiller les dépôts 8-K (« il s'est passé un truc »).
"""
import csv
import io
import json
import sys

import httpx
import yaml

SP500_CSV = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
UA = "axone-veille (contact: ensecu2025@gmail.com)"

# NASDAQ-100 (source : Wikipédia, juin 2026). Change rarement ; à mettre à jour
# manuellement lors des rééquilibrages annuels de l'indice.
NASDAQ100 = """
ADBE AMD ABNB ALNY GOOGL GOOG AMZN AEP AMGN ADI AAPL AMAT APP ARM ASML ADSK ADP
AXON BKR BKNG AVGO CDNS CHTR CTAS CSCO CCEP CTSH CMCSA CEG CPRT COST CRWD CSX
DDOG DXCM FANG DASH EA EXC FAST FER FTNT GEHC GILD HON IDXX INSM INTC INTU ISRG
KDP KLAC KHC LRCX LIN LITE MAR MRVL MELI META MCHP MU MSFT MSTR MDLZ MPWR MNST
NFLX NVDA NXPI ORLY ODFL PCAR PLTR PANW PAYX PYPL PDD PEP QCOM REGN ROP ROST
SNDK STX SHOP SBUX SNPS TMUS TTWO TSLA TXN TRI VRSK VRTX WMT WBD WDC WDAY XEL ZS
""".split()


def fetch(url: str) -> httpx.Response:
    r = httpx.get(url, headers={"User-Agent": UA}, timeout=30, follow_redirects=True)
    r.raise_for_status()
    return r


def main() -> None:
    print("· Téléchargement de la table SEC ticker -> CIK …")
    sec = fetch(SEC_TICKERS).json()
    # index : TICKER -> (cik_padded_10, title)
    cik_by_ticker = {}
    for row in sec.values():
        t = row["ticker"].upper()
        cik_by_ticker[t] = (f"{int(row['cik_str']):010d}", row["title"])

    print("· Téléchargement de la liste S&P 500 …")
    sp_csv = fetch(SP500_CSV).text
    reader = csv.DictReader(io.StringIO(sp_csv))

    # ticker -> dict company. On fusionne S&P 500 et NASDAQ-100 sur le ticker.
    companies = {}

    def upsert(ticker: str, name: str, index_tag: str) -> None:
        ticker = ticker.upper().replace(".", "-")  # ex: BRK.B -> BRK-B
        c = companies.setdefault(
            ticker, {"ticker": ticker, "name": name, "cik": None, "indices": []}
        )
        if index_tag not in c["indices"]:
            c["indices"].append(index_tag)
        # CIK + nom officiel SEC si dispo
        if ticker in cik_by_ticker:
            c["cik"], sec_name = cik_by_ticker[ticker]
            if not c["name"]:
                c["name"] = sec_name

    for row in reader:
        upsert(row["Symbol"], row["Security"], "sp500")

    for ticker in NASDAQ100:
        name = cik_by_ticker.get(ticker, (None, ticker))[1]
        upsert(ticker, name, "nasdaq100")

    ordered = sorted(companies.values(), key=lambda c: c["ticker"])
    missing_cik = [c["ticker"] for c in ordered if not c["cik"]]

    out = {
        "_note": "Généré par build_watchlist.py — relancer pour rafraîchir. "
        "Ajouts persos possibles à la main (garder le même format).",
        "companies": ordered,
    }
    with open("watchlist.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(out, f, allow_unicode=True, sort_keys=False, width=200)

    n_sp = sum(1 for c in ordered if "sp500" in c["indices"])
    n_nq = sum(1 for c in ordered if "nasdaq100" in c["indices"])
    print(f"\n✅ watchlist.yaml généré : {len(ordered)} sociétés uniques")
    print(f"   · S&P 500    : {n_sp}")
    print(f"   · NASDAQ-100 : {n_nq}")
    print(f"   · présentes dans les deux : {n_sp + n_nq - len(ordered)}")
    if missing_cik:
        print(f"⚠️  Sans CIK SEC ({len(missing_cik)}) : {', '.join(missing_cik)}")


if __name__ == "__main__":
    sys.exit(main())
