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

**Nog niet vastgesteld:** of `WebFetch` daadwerkelijk een andere/bredere
netwerktoegang heeft dan de sessieproxy die `curl` gebruikt, of dat dit
specifiek is voor investing.com. Dit moet expliciet getest worden op de
werkelijke RSS-doeldomeinen (vrt.be, standaard.be, politico.eu, sectorpers,
…) vóór Pijler A gebouwd wordt. Als `WebFetch` die ook bereikt, is het
netwerkprobleem uit bevinding 1 mogelijk al opgelost zonder dat het eerder
getest werd.

## Openstaand voor Pijler A

- Concrete RSS-feed-URLs per analistrol (stock watchers, trend viewers,
  technical stock watchers, sector specialists) — worden door Paul
  aangeleverd.
- Verificatie van die concrete URLs via `WebFetch` vóór ze in productie
  gebruikt worden.
