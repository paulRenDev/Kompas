# Kompas — RSS/netwerktoegang signaalscan

Onderzoeksnotities voor Pijler A (Signalenmotor) van de Kompas-herbouw: welke
externe bronnen zijn effectief bereikbaar vanuit een Claude Code-sessie, en
via welk mechanisme (directe `curl` via de sessieproxy versus `WebFetch`).

## Bevinding 1 — directe curl naar nieuwsbronnen: grotendeels geblokkeerd

Rechtstreekse `curl`-aanroepen via de sessieproxy naar vrijwel alle geteste
nieuwsbronnen gaven een 403 (beleid):

- Politico
- De Standaard
- FT
- BBC
- CNBC
- WSJ
- ECB
- Fed

Uitzonderingen:
- `feeds.nos.nl` — werkte volledig.
- `fd.nl` — het domein zelf was bereikbaar, maar het exacte RSS-pad is niet
  gevonden.

**Diagnose:** het netwerkbeleid laat enkel kale apex-domeinen door (bv.
`vrt.be`), niet de `www.`- of `feeds.`-subdomeinen waar de effectieve feeds
op staan.

## Bevinding 2 — WebFetch: mogelijk bredere toegang dan curl (17/9/2026)

Een live test met `WebFetch` op de technische pagina van investing.com voor
ASML leverde wél bruikbare data op, terwijl directe `curl`-aanroepen naar
vergelijkbare domeinen eerder geblokkeerd werden.

Resultaat van die test (technische indicatoren, al berekend door de bron
zelf):

| Indicator | Waarde | Oordeel |
|---|---|---|
| RSI(14) | 49,99 | neutraal |
| MACD(12,26) | -1,07 | sell |
| 50-daags gemiddelde | 1.425,56 | sell |
| 200-daags gemiddelde | 1.472,12 | sell |
| Totaaloordeel | — | Strong Sell |

**Kanttekening:** dit zijn indicatoren die investing.com zelf al berekende,
geen eigen berekening op ruwe koersdata. Volgens de bronhiërarchie (sectie 11
van de oude Kompas-spec) is dit tier 2 (financiële journalistiek/aggregator),
geen tier 1 — moet in de output ook zo gelabeld worden, nooit gepresenteerd
als Kompas' eigen berekening.

**Vastgesteld (17/9/2026):** `WebFetch` heeft wel degelijk andere/bredere
netwerktoegang dan de sessieproxy die `curl` gebruikt — maar niet
onbeperkt. Een brede test van ~25 kandidaat-bronnen (zie Bevinding 3)
toont een specifieke deny-list op de `WebFetch`-egress-proxy zelf, geen
generiek subdomein-probleem.

## Bevinding 3 — brede WebFetch-test van kandidaat-RSS-bronnen (17/9/2026)

Elke URL hieronder is live getest met `WebFetch`, niet aangenomen.

### Bevestigd werkend

| Bron | URL | Bruikbaar voor |
|---|---|---|
| VRT NWS | `https://www.vrt.be/vrtnws/nl.rss.articles.xml` | algemeen Vlaams nieuws — ongefilterd op onderwerp |
| NOS | `https://feeds.nos.nl/nosnieuwsalgemeen` | algemeen Nederlands nieuws — ongefilterd op onderwerp |
| ECB persberichten | `https://www.ecb.europa.eu/rss/press.html` | Trend viewers — monetair beleid, tier 1 |
| Fed persberichten | `https://www.federalreserve.gov/feeds/press_all.xml` | Trend viewers — monetair beleid, tier 1 |
| Investing.com — aandelennieuws | `https://www.investing.com/rss/news_25.rss` | Stock watchers — algemeen, niet per naam gefilterd |
| Investing.com — grondstoffen/futures | `https://www.investing.com/rss/news_11.rss` | Sector specialist – Uranium/Energie — olie, gas, metalen |
| Investing.com — economische indicatoren | `https://www.investing.com/rss/news_95.rss` | Trend viewers — macro-economische data |
| Investing.com — forex | `https://www.investing.com/rss/news_1.rss` | minder relevant, valuta/macro |
| Investing.com — technische pagina per ticker | (geen RSS, page-fetch, bv. `/equities/asml-holding-nv-technical`) | Technical stock watchers — al bevestigd in vorige sessie (zie Bevinding 2) |

Het volledige `investing.com`-domein lijkt open te staan op de egress-proxy
— zowel de RSS-categoriefeeds als losse pagina's (technische analyse per
ticker) werken. Dat maakt het vandaag de enige domeinbrede, betrouwbare
bron.

### Geblokkeerd — `EGRESS_BLOCKED` (expliciete deny-list, geen subdomein-probleem)

De Standaard, BBC (`feeds.bbci.co.uk`), Politico EU, Google News, SEC
EDGAR, World Nuclear News, Defense News, DatacenterDynamics,
SemiEngineering, Yahoo Finance (`feeds.finance.yahoo.com`), IAEA, EIA,
Tom's Hardware, Seeking Alpha, Kalshi, IMF, NATO, EU Commission
(`ec.europa.eu`), MarketWatch, Euractiv, BusinessWire, GlobeNewswire,
TradingEconomics, Techmeme, Dow Jones (`feeds.content.dowjones.io`).

Dit is een expliciete foutcode (`EGRESS_BLOCKED`) van de proxy zelf, niet
een timeout of 403 van de bron — bevestigt een deny-list op domeinniveau,
los van of het een apex- of subdomein is (`www.vrt.be` werkt,
`www.marketwatch.com` niet — geen patroon, gewoon per-domein).

### Ander soort fout — vermoedelijk ook geblokkeerd, andere foutcode

`www.reuters.com`, `www.standaard.be`, `feeds.bbci.co.uk`,
`www.politico.eu`, `www.marketwatch.com`, `www.euractiv.com`: "Claude Code
is unable to fetch" — geen `EGRESS_BLOCKED`-label, maar in de praktijk
even onbruikbaar. Niet verder onderzocht of dit een ander mechanisme is.

**Kritieke bevinding voor het sector-specialistenpool-ontwerp:** geen
enkele sector-specifieke vakpersbron (halfgeleiders, defensie,
nucleair/uranium, datacenters) is bereikbaar gebleken. De enige
sector-relevante bron die werkt, is investing.com's generieke
"commodities & futures"-categorie (olie/gas/metalen) — nuttig voor een
Sector specialist – Uranium/Energie, maar er is nog niets werkend voor
Sector specialist – Halfgeleiders, – Defensie of – Datacenter-infra. Dit
is vandaag de grootste blocker voor de sector-specialistenpool, groter dan
het aantal specialisten zelf.

## Openstaand voor Pijler A

- **Sectorspecifieke vakpers** (halfgeleiders, defensie, datacenters):
  geen enkele bron bevestigd werkend — nog te onderzoeken (andere
  domeinen proberen, of overwegen of Google/Bing-achtige geaggregeerde
  zoekresultaten via `WebSearch` een alternatief zijn voor sectoren zonder
  eigen bereikbare vakpers).
- **Stock watchers per naam**: `investing.com/rss/news_25.rss` is
  algemeen, niet gefilterd per holding/watchlist-naam — een per-naam
  aanpak (page-fetch van de company-newspagina per ticker, zoals al
  gebruikt voor de technische pagina) is nog niet getest voor alle 6
  holdings + 24 watchlist-namen.
- Verdere kandidaten testen zodra Paul specifieke bronnen aanlevert die
  hij zelf al leest/vertrouwt.
