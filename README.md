# Kompas

Signalenmotor + dagelijkse aandelencollectie voor Paul's portefeuilles.
Volledige herbouw, losstaand van het bestaande Kompas-artifact — geen
uitbreiding op wat er stond (architectuurbeslissing 17/9/2026).

## Diagnose: waarom herbouwen

Het vorige Kompas beweerde een opportunity-engine te hebben (watchlist,
capital map die kansen tegen elkaar afweegt) maar draaide die nooit echt:
de watchlist-collectie was leeg, `capital_map/ranking` bestond niet, en de
Opportunities-tabel toonde een FOMC-trigger die al een volledige dag
opgelost was, over drie ververscycli heen, zonder herbekeken te worden.

Oorzaak: elke ververscyclus (4x/dag) besteedde zijn volledige budget aan het
herverifiëren van de zes portefeuilleposities. De kansenkant kreeg nooit een
eigen tijdslot en verloor impliciet elke keer van de portefeuille-check.
"Alles is stil" was dus een uitvoeringsfeit, geen marktfeit.

## Kernidee: twee volledig gescheiden pijlers

| | Pijler A — Signalenmotor | Pijler B — Dagelijkse aandelencollectie |
|---|---|---|
| Wat | RSS-gedreven interpretatie door vier analistrollen | Feitelijke verzameling van aandelen/ETF's (portefeuille + watchlist) |
| Aard | Interpretatie, mening, signaal | Pure data, geen interpretatie |
| Bron | RSS-feeds per rol | Google Sheet "Aandelen" (enige bron van waarheid) |
| Cadans | Eigen, onafhankelijke planning per rol | Kan vaker/regelmatiger draaien, los van Pijler A |

Scheiden is een harde vereiste: in het oude systeem verdrong Pijler B
Pijler A elke keer omdat beide om dezelfde tijd/aandacht streden. Ontkoppeld
kan Pijler A draaien ongeacht wat Pijler B die dag doet, en omgekeerd. Pas
wanneer beide apart betrouwbaar draaien, komen ze samen in een
synthese-laag.

Pijler A en Pijler B zijn, architecturaal, de personal-adapters achter twee
van de vier vervangbare poorten — zie "Architectuur — losse, vervangbare
componenten" hieronder voor waarom dat onderscheid vanaf dag 1 vastligt.

### Pijler A — drie vaste rollen + een sector-specialistenpool

Elke rol/specialist doorzoekt eigen RSS-bronnen en rapporteert apart, vóór
synthese. Conflict wordt zichtbaar gemaakt, nooit gemiddeld tot een vage
consensus.

| Rol | Kernvraag | Bron | Output |
|---|---|---|---|
| Stock watchers | Wat gebeurt er met deze naam? | Bedrijfsspecifiek nieuws per holding/watchlist-naam | Gebeurtenis + waarom relevant voor die naam |
| Trend viewers | Structurele trend of ruis? | Macro-/beleidsnieuws (geopolitiek, industriebeleid, energie, handel) | Trendbevestiging, -breuk of ruis, expliciet benoemd |
| Technical stock watchers | Wat zegt de koers zelf? | Koersactie, chartpatronen, momentum | Technisch niveau bereikt/gebroken, los van fundamentals |

**Sector specialisten zijn geen vierde rij in deze tabel, maar een pool**
(bijgesteld 17/9/2026, uit de sectoranalist-review + Paul's beslissing:
"we moeten meerdere sector analysten hebben, het gaat niet over slechts
vijf sectoren"). Eén generalist die halfgeleiders, defensie, energie,
uranium én datacenters tegelijk moet dekken, produceert structureel
oppervlakkige cross-sector-verhaaltjes — echte diepte komt van smalle,
diepe specialisten, niet van één breed overzicht.

- Elke sector die relevant is (via portefeuille, watchlist, of het
  anti-bevestigingsbias-quotum buiten portefeuille/watchlist — zie
  hieronder) krijgt zijn **eigen** sector-specialist-instantie: bv.
  "Sector specialist — Halfgeleiders", "Sector specialist —
  Uranium/Nucleair", "Sector specialist — Defensie", "Sector specialist —
  Datacenter-infra", enzovoort.
- Het aantal is niet vast — het schaalt met hoeveel sectoren daadwerkelijk
  gevolgd worden, niet met een vooraf bepaald lijstje van vijf of tien.
  Nieuwe sectoren (nieuwe holding, nieuwe watchlist-naam, of een nieuwe
  "buiten"-sector voor het anti-bias-quotum) krijgen een nieuwe
  specialist-instantie; een sector die niet meer relevant is, verliest
  zijn instantie — dezelfde levenscyclus-logica als de watchlist.
- Een cross-sector spotlight (zoals "defensie → halfgeleiders") ontstaat
  pas wanneer **twee specifieke specialisten** elkaar kruisen — nooit als
  output van één generalistische pass over meerdere sectoren tegelijk.
- **Geopolitiek is niet enkel voor Trend viewers.** Elke sector-specialist
  volgt ook de geopolitiek die specifiek zijn eigen sector raakt
  (exportcontroles die halfgeleiders raken, sancties die energie/defensie
  raken, handelsbeleid dat specifieke ketens raakt) — als onderdeel van
  zijn sectorbrede vakpers, niet als apart kanaal. Trend viewers dekken de
  macro-laag (brede geopolitieke/beleidsverschuivingen); een
  sector-specialist dekt hoe die verschuiving specifiek zijn sector raakt.

Cadans: de drie vaste rollen én de volledige sector-specialistenpool
draaien allemaal gelijktijdig, niet gestaggerd — op de twee dagelijkse
Kompas-verversmomenten (09:00 CEST en 18:00 CEST), zodat de synthese
altijd met volledige, gelijktijdige input werkt, hoeveel specialisten er
ook in de pool zitten.

Zie `docs/kompas-rss-signaalscan.md` voor de netwerktoegang-research
(curl vs. WebFetch) die aan concrete RSS-bronkeuzes voorafgaat.

### Pijler B — de dagelijkse aandelencollectie

Puur feitelijk, geen interpretatie — het fundament waar Pijler A's signalen
tegen worden gelegd. Dit is de personal adapter achter Poort 2
(Portefeuillebron); alles hieronder tot en met de vertaallaag is
adapter-intern en irrelevant voor een toekomstige andere adapter.

- Bron: Google Sheet "Aandelen" (fileId `1l1XSohzp0wS8JAQFaMTGkJe0zrur1BKbZdkbN6MLR7A`),
  read-only, enige bron van waarheid voor holdings-/watchlist-identiteit,
  aantallen, cost, actuele waarde en gain.
- Reconciliatiediscipline: eigen som van de zichtbare posities altijd
  vergelijken met de sheet's eigen totaalregel; bij afwijking publicatie
  stoppen tot verklaard.
- Watchlist-volledigheid: tellen tegen de volledige ledger (ACTIVE=2), nooit
  enkel tegen de vorige bekende toestand.
- Cadans: kan onafhankelijk en desgewenst vaker draaien dan Pijler A, zonder
  dat dit ten koste gaat van de signalenmotor.
- **Aanbevelingshistoriek per watchlist-naam**: elke entry houdt een array
  bij (datum, aanbeveling, welke rol, reden) — niet enkel de laatste status.
- **Levenscyclus/opruiming**: geen bevestiging of nieuw signaal over een
  naam gedurende N cycli (voorlopig: 6 cycli = 3 dagen) → gemarkeerd voor
  herbeoordeling → van de lijst als niemand het opnieuw bevestigt. Voorkomt
  dat de watchlist, net als in het oude Kompas, alleen maar aangroeit.
- **Actieve posities krijgen dezelfde continue behandeling als de
  watchlist**: elke cyclus een expliciete houd/verkoop/bijkoop-aanbeveling
  per positie in de synthese-laag, met dezelfde actiedrempel-discipline als
  decision objects — niet enkel wanneer toevallig een signaal binnenkomt.

Technische verbinding (al werkend): `mcp__Google_Drive__read_file_content`,
strikt read-only. Drie tabbladen: `live` (actuele PORTEFEUILLE- en
Watchlist-tabel), `Data` (transactieledger sinds 2015, ACTIVE=1 = huidige
holdings), `watchListData` (watchlist-ledger, ACTIVE=2 = actieve
watchlist-namen).

#### Vertaallaag van de Google Sheet-adapter (ruwe dump → Poort 2-vorm)

Onderstaande stappen zetten de ruwe, ongestructureerde pivot-tabeldump van
de Google Sheet om naar de generieke Poort 2-vorm (naam, aantal, waarde,
cost, gain, totaalregel). Dit hoort volledig bij deze adapter — een andere
portefeuillebron (Bolero, een snapshot, een custodian-feed) heeft hier
niets aan en krijgt zijn eigen, andere vertaallaag of geen enkele.

1. Roep `mcp__Google_Drive__read_file_content` aan met
   `fileId: "1l1XSohzp0wS8JAQFaMTGkJe0zrur1BKbZdkbN6MLR7A"`. Read-only —
   nooit proberen te schrijven.
2. De output overschrijdt meestal de tool-outputlimiet en landt in een
   lokaal bestand (JSON, schema `{fileContent: string}`). Extraheer met
   `jq -r '.fileContent' <pad> > <scratchpad-bestand>` en werk verder met
   grep/awk/sed op platte tekst — nooit de volledige inhoud rechtstreeks
   inladen.
3. De platte tekst is één doorlopende markdown-pipe-tabel-dump van alle
   tabbladen na elkaar, zonder duidelijke scheiding. Vind de grenzen via de
   headerrij van elk blok, niet via regelnummers (die verschuiven bij elke
   refresh):
   - `live`/PORTEFEUILLE: header start met
     `Name | TICKER | EXCHANGE | Type effect | currency | purchaseDate (min) | Nbr | totPurValueEUR | valueEUR | ...`
     — gevolgd door de 6 actieve holdings.
   - `live`/Watchlist: header start met
     `Name | TICKER | EXCHANGE | Type effect | currency | OPM | setDate (min) | Nbr | totSetValueEUR | ...`
     — gevolgd door de actieve watchlist-namen (nu 24).
   - `Data` (ledger sinds 2015): header start met
     `| Datum | Transactie | Type effect | Details | Waarde | Munt | YYYY | MM | Type_effect | Name | inversedValue | ACTIVE | EXCHANGE | Aantal | TICKER | ...`
     — ACTIVE op kolom 14 (na de lege eerste kolom), TICKER op kolom 17.
     ACTIVE=1 = nu actieve holding.
   - `watchListData`: zelfde soort header, andere kolomvolgorde op het einde
     (OPM, aantal, prijs, nameDate i.p.v. PurPrice, NameDate). ACTIVE=2 =
     actieve watchlist-naam.
4. Kritieke valkuil: ga nooit uit van een vaste kolomindex — tel opnieuw af
   tegen de headerrij van het specifieke blok. Verderop in de dump
   (rond regel 1470+ in een recente pull) staat een ander pivot-overzicht
   ("PORTEFEUILLE DETAIL") met afwijkende kolomstructuur; de
   ledger-kolomindex daarop toepassen geeft stille, foutieve output.
5. Verplichte reconciliatie vóór publicatie: tel ACTIVE=2-tickers over de
   volledige `watchListData`-ledger en vergelijk met het aantal rijen in de
   live Watchlist-tabel — moet exact overeenkomen. Bereken zelf
   totalCost/totalValue/totalGain/gainPct uit de zes actieve posities en
   vergelijk met de sheet's eigen totaalrij — bij afwijking stoppen, nooit
   publiceren met een onverklaard verschil.

## Signaalversheid — geen herhaling zonder wijziging

Directe les uit de diagnose hierboven: een geheugen dat alleen *kan*
detecteren dat iets al eerder gezegd is, maar publicatie niet blokkeert, is
decoratie. Daarom, vóór elke publicatie van een signaal:

- Verplichte query tegen `events` voor dezelfde naam/sector: bestaat er al
  een niet-vervallen signaal met dezelfde kern?
- Zo ja: alleen opnieuw publiceren bij een materiële wijziging (nieuwe
  cijfers, technisch niveau gebroken, nieuwe sectordata) — anders wordt het
  signaal stilzwijgend onderdrukt, nooit herhaald.
- Deze check is een harde publicatievoorwaarde, net als de reconciliatie in
  Pijler B — geen los "nice to have".

## Verdieping via Claude — geen chat in de tool zelf (bijgesteld 17/9/2026)

Geen chatfunctie in de Kompas-pagina zelf. Wanneer iets op de pagina Paul's
aandacht trekt en hij dieper wil graven, doet hij dat in een gewone
Claude-conversatie (claude.ai/code), niet in Kompas — precies zoals deze
sessie nu werkt. Wat daar moet kloppen is niet een nieuwe feature, maar een
gewoonte: die Claude-sessie moet, wanneer Paul een naam/signaal/sector uit
Kompas aanhaalt, meteen de context uit de Kompas-database kunnen ophalen in
plaats van bij nul te beginnen.

- Elke Claude-sessie die met Kompas te maken heeft, haalt die context op via
  dezelfde `ArtifactData`-tool tegen dezelfde artifact-url, met
  `get`/`list`/`query` tegen `events`/`watchlist`/`wallet-positions` — geen
  apart chat-threadsysteem, geen aparte opslag van gesprekshistoriek per
  rol. De bestaande `events`-collectie (signaal: wie, wanneer, wat, bron) is
  het geheugen; een Claude-sessie leest die net als de synthese-laag zelf
  doet.
- Live websearch/WebFetch voor verdieping gebeurt gewoon binnen die
  Claude-conversatie zelf, zoals in elke andere sessie — geen apart
  budget- of chat-mechanisme nodig, want het is geen los kanaal binnen de
  tool.

## Anti-bevestigingsbias — uitdaging is een vereiste, geen bijeffect

Elke input in dit systeem (watchlist, portefeuille, zelfs de gevolgde
sectoren) is afgeleid van wat Paul al bezit of al interessant vindt. Vier
onafhankelijke rollen lossen het *gemiddelde-tot-vage-consensus*-probleem
op — ze lossen niet het *enkel lezen over eigen namen*-probleem op.

- Sector specialists krijgen een vast quotum sectoren/thema's **buiten** de
  portefeuille en watchlist, puur omdat ze bewegen — niet omdat Paul ze al
  volgt.
- Een positie die cyclus na cyclus hetzelfde bullish-signaal krijgt zonder
  ooit tegengeluid, is zelf een waarschuwingssignaal (mogelijke
  bevestigingsbias in de bronnenselectie, geen marktfeit) en wordt apart
  gemarkeerd, nooit stil herhaald.

## Architectuur — losse, vervangbare componenten (17/9/2026)

Kernidee, rechtstreeks uit de bank-PM review: "het zijn toch altijd
dezelfde dingen waarmee gewerkt wordt" — een signaalbron, een
portefeuillebron, een geheugen, een publicatiekanaal. Voor Paul is elk
daarvan vandaag één specifieke keuze (RSS + vier rollen, Google Sheet,
ArtifactData, Artifact-pagina), maar de synthese-logica mag daar nooit
rechtstreeks van afhangen. Daarom bestaat Kompas uit een **kern**
(domeinlogica, nooit vervangbaar) rond vier **poorten** (interfaces), elk
met vandaag precies één **adapter** (de personal-implementatie), maar
zonder dat de kern ooit een adapter rechtstreeks aanspreekt.

### De kern — adapter-onafhankelijk
- Synthese-laag: combineert signalen + portefeuille/watchlist-toestand tot
  capital map + decision objects.
- Signaalversheid: dedup-regel tegen het geheugen vóór publicatie.
- Anti-bevestigingsbias-regels: sectorquotum buiten portefeuille,
  markering bij herhaald eenzijdig signaal.
- Watchlist-levenscyclus: aanbevelingshistoriek + staleness-opruiming.
- Publicatietrio (validatie vóór output).

De kern kent alleen de vier poort-interfaces hieronder — nooit of een
signaal van RSS komt of van iets anders, nooit of een positie uit een
Google Sheet komt of van een broker.

### Poort 1 — Signaalbron (Pijler A)
Interface: levert signalen als `{rol, naam/sector, tekst, bron, brontier,
omvang, tijdshorizon, databetrouwbaarheid, signaalbetrouwbaarheid,
tijdstip}` (technische signalen ook: `timeframe`).
- **Personal adapter (nu)**: vier RSS-gedreven analistrollen (stock
  watchers, trend viewers, technical stock watchers, sector specialists).
- **Andere adapter (bv. een bank)**: de eigen signalenengine/researchdesk
  van die bank — de kern moet niet weten of een signaal van RSS komt of van
  een intern team, zolang het in dezelfde vorm binnenkomt.

**Verplichte velden, harde publicatievoorwaarde (17/9/2026, uit de
sectoranalist-review):** zonder deze velden kan de synthese-laag geen
advies-consensus bouwen — een claim zonder omvang, tijdshorizon of
citeerbare bron is niet combineerbaar met een ander signaal, en dus
onbruikbaar voor een decision object. Een signaal dat één van deze velden
mist, wordt niet gepubliceerd:
- **`bron`**: citeerbaar en specifiek (het artikel, de uitgever, het
  beleidsdocument) — nooit enkel een categorie ("sectorpers", "tier 1").
  Een bron die niemand kan terugvinden, is niet controleerbaar en dus niet
  publiceerbaar.
- **`brontier`**: de bestaande tier-classificatie (tier 1/2/…) — blijft,
  maar vervangt nooit een echte bronvermelding.
- **`omvang`**: een indicatie van hoe groot/materieel dit is (bv.
  percentage van omzet, geschatte impact) — geen vage kwalificatie zonder
  getal.
- **`tijdshorizon`**: wanneer dit zichtbaar zou moeten worden (volgende
  kwartaalcijfers, komende weken, structureel/jaren) — zonder tijdshorizon
  is een signaal niet te toetsen.
- **`databetrouwbaarheid`** en **`signaalbetrouwbaarheid`** (gesplitst
  17/9/2026, uit de technical-analyst-review — vervangt het eerdere,
  samengevoegde `vertrouwensniveau`): twee losse assen, nooit tot één
  woord samengevoegd.
  - `databetrouwbaarheid`: is het onderliggende cijfer correct berekend
    (bv. een RSI-waarde is deterministisch, dus hoog) — zegt niets over
    of het iets voorspelt.
  - `signaalbetrouwbaarheid`: hoe voorspellend is dit soort signaal
    historisch (technische patronen hebben gekende valse-signalen-ratio's;
    een speculatieve sector-link heeft dat per definitie niet) — expliciet
    speculatief / voorlopig / hoog, nooit stilzwijgend als feit
    gepresenteerd.
- **`timeframe`** (verplicht, enkel voor technische signalen): het
  chart-timeframe waarop de indicator berekend is (dag/week/…) — een
  technisch niveau zonder timeframe is niet te interpreteren; een
  "Strong Sell" op dagbasis betekent iets anders dan op weekbasis voor een
  positie die weken tot maanden aangehouden wordt.

### Poort 2 — Portefeuillebron (Pijler B)
Interface: levert holdings + watchlist + aantallen/cost/waarde/gain, plus
een eigen totaalregel om tegen te reconciliëren.
- **Personal adapter (nu)**: Google Sheet "Aandelen" (read-only). Deze
  adapter bevat een eigen **vertaallaag** (ruwe pivot-tabeldump → deze
  generieke vorm) — zie "Vertaallaag van de Google Sheet-adapter" onder
  Pijler B. Die vertaallaag hoort volledig bij déze adapter, nooit bij de
  poort-interface of de kern.
- **Andere adapters (zelfde interface)**: een Bolero-rekening
  (brokerage-API), een portefeuille-snapshot op een vast tijdstip, een
  custodian-feed van een bank — altijd dezelfde vorm: naam, aantal, waarde,
  cost, gain, en een totaalregel om tegen te reconciliëren. Zo'n adapter
  heeft mogelijk een heel andere vertaallaag (of geen: een brokerage-API
  levert vaak al gestructureerde velden, geen ledger-kolommen om af te
  tellen) — dat is per adapter, nooit gedeeld.

**Nog niet nu, wél al voorzien:** naast deze vier poorten komt er ooit een
vijfde dimensie bij — wie de gebruiker/klant is, met de opties en
klantgegevens die daaraan hangen (nodig zodra dit multi-tenant wordt, zie
"Klant-identiteit" in Open vragen). Voor Paul's eigen gebruik is er precies
één impliciete gebruiker, dus dit wordt nu niet ontworpen.

### Poort 3 — Geheugen/opslag
Interface: `get`/`list`/`query`/write op events/watchlist/decisions, met
versiebeveiliging (`if_version`).
- **Personal adapter (nu)**: `ArtifactData` tegen de vaste artifact-url.
- **Andere adapter**: een gedeelde/enterprise database — nodig zodra dit
  multi-tenant wordt (zie de bank-PM review hiervoor).

### Poort 4 — Publicatiekanaal
Interface: toon de synthese aan een lezer.
- **Personal adapter (nu)**: de Artifact HTML-pagina (`Ververs
  Kompas`-knop, vaste url).
- **Andere adapter**: een bank-app-scherm, een PDF-rapport, een
  API-response voor een derde partij.

### Wat dit voor de bouwvolgorde betekent
Geen wijziging in wát er eerst gebouwd wordt: nog steeds Poort 2's
personal adapter (Google Sheet) als eerste effectieve implementatie. De
wijziging is dat die adapter vanaf dag 1 **achter de Poort 2-interface**
gebouwd wordt, nooit rechtstreeks door de synthese-laag aangeroepen. Zonder
die scheiding zou elke latere aanpassing (andere portefeuillebron, ander
signalenteam) dwars door de synthese-logica moeten; met de scheiding
verandert alleen de adapter.

## Waar de twee pijlers samenkomen

Een aparte synthese-/aggregatielaag combineert de vier analistoordelen van
Pijler A (met onderling conflict zichtbaar gehouden) met de feitelijke
portefeuille-/watchlist-toestand van Pijler B. Daaruit ontstaan pas een
capital map die kansen tegen elkaar en tegen cash afweegt, en
decision-objecten per positie/watchlist-naam met een concrete actiedrempel.
Deze laag kan pas werken zodra Pijler A daadwerkelijk data aanlevert.

## Geheugen: een activiteitendatabase

Derde, doorlopende component naast de twee pijlers: een database die
bijhoudt wat er eerder gebeurde.

Legt vast:
- Elk signaal van een analistrol (wie, wanneer, wat, welke bron).
- Elke beslissing uit de synthese-laag (status, reden, wat de mening zou
  veranderen).
- Wat er nadien werkelijk gebeurde (outcome, timing, klopte de inschatting?).

Zonder geheugen herhaalt Kompas zichzelf — precies het patroon dat tot deze
herbouw leidde (dezelfde ASML-trigger drie cycli na elkaar herhaald zonder
controle).

**Belangrijk (bijgesteld 17/9/2026): dit is een interne component, geen
pagina-onderdeel.** De `events`-collectie groeit voor altijd — dat is
precies waarom hij nooit als "activiteitenlog"-tabel op de Kompas-pagina
zelf getoond wordt: een groeiende lijst tonen is geen UI, het is een
databaseleeg-scherm. De kern *gebruikt* dit geheugen (signaalversheid,
staleness, audit), de pagina *toont* enkel de bewuste, begrensde afleidingen
ervan die al elders staan: de aanbevelingshistoriek per watchlist-naam
(begrensd tot die ene naam) en de decision objects (begrensd tot actieve
posities/watchlist-namen). Geheugen bijhouden en geheugen tonen zijn
losse dingen — Kompas doet het eerste altijd, het tweede nooit rechtstreeks.

### De Kompas-database

Gedeelde database via de `ArtifactData`-tool (apart van de `Artifact`-tool
zelf). Vaste patronen:

- Elke actie vereist de artifact-url:
  `https://claude.ai/code/artifact/9f6bc549-e4df-4082-874b-cf5907bbaab0`.
- Lezen: `get` (één document), `list` (een collectie), `query` (gefilterd).
- Schrijven: `set`/`update`/`batch` — gebruik `batch` (tot 50 writes,
  atomisch) zodra meerdere documenten wijzigen in één cyclus.
- Pin elke write met `if_version`, de versie gezien bij het laatste lezen.
  Een write zonder `if_version` overschrijft blind; een gepinde write die
  niet meer klopt faalt netjes.
- Bestaande collecties: `wallet/state`, `wallet-positions/<ticker>`,
  `meta/last_refresh` werken al. `watchlist`, `capital_map/ranking`,
  `events` staan leeg/bestaan niet — dit moet Pijler A gaan vullen.

## Publicatiemechaniek — de validatietrio

Vóór elke publicatie van de HTML-pagina (via de `Artifact`-tool, altijd
dezelfde vaste url):

1. **HTML-tagbalans** — elk openend tag matchen met zijn sluitend tag
   (self-sluitende/void-tags genegeerd); vangt kapotte markup vóór
   publicatie.
2. **copyRow-knoptekst** — check dat de 'Ververs Kompas'-knop nog exact naar
   de vaste artifact-URL verwijst.
3. **POSITIONS-herberekening** — totalCost/totalValue/totalGain/gainPct en
   kern/satelliet-percentages herberekenen uit de POSITIONS-array en
   vergelijken met de sheet's eigen totalen; bij afwijking niet publiceren.

## Netwerktoegang: wat werkt en wat niet

Zie `docs/kompas-rss-signaalscan.md`. Samengevat: directe `curl` naar bijna
alle geteste nieuwsbronnen gaf 403 (enkel `feeds.nos.nl` werkte volledig);
`WebFetch` bereikte wel investing.com waar `curl` naar vergelijkbare
domeinen faalde — moet nog expliciet getest worden op de echte
RSS-doeldomeinen vóór Pijler A gebouwd wordt.

## Bekende openstaande technische schuld

- `real_holdings.json` (in de Stocazzo-repo) is stale: 26+ dagen oud t.o.v.
  sessiedatum 17/9/2026 — de Google Apps Script-sync
  (`portfolio_sync.gs`) lijkt maar één keer gedraaid te hebben. Nog niet
  verder onderzocht.
- Oude scanner-code (`scanners/*.py` in Stocazzo, 12+ bestanden) wordt
  nergens meer geïmporteerd — dode code, cosmetische opruiming, niet
  relevant voor Kompas zelf.

## Open vragen

- [x] **Cadans per rol** (17/9/2026): alle vier rollen draaien gelijktijdig,
  op de twee dagelijkse verversmomenten (09:00 CEST, 18:00 CEST).
- [x] **Concrete RSS-bronnenlijst — deels beantwoord** (17/9/2026):
  ~25 kandidaat-bronnen live getest met `WebFetch`
  (`docs/kompas-rss-signaalscan.md`, Bevinding 3). Bevestigd werkend:
  VRT NWS, NOS, ECB-persberichten, Fed-persberichten, en het volledige
  `investing.com`-domein (RSS-categorieën aandelen/grondstoffen/economie/
  forex + technische pagina's per ticker). **Blocker opgelost (zelfde
  dag):** geen enkele sector-specifieke vakpersbron werkt als vaste
  RSS-feed, maar `WebSearch` blijkt niet aan dezelfde domein-deny-list
  onderhevig — live getest op halfgeleiders en defensie, beide gaven
  actuele, citeerbare resultaten van domeinen die via directe `WebFetch`
  net geblokkeerd waren. Een sector-specialist zonder eigen bereikbare
  feed gebruikt dus `WebSearch` met een sectorspecifieke zoekopdracht per
  cyclus — zie `docs/kompas-rss-signaalscan.md`, Bevinding 4.
- [x] **Automatisering vs. menselijke review** (17/9/2026): volledig
  autonoom — geen check-in-moment per signaal vóór de synthese-laag.
- [x] **Architectuur** (17/9/2026): volledig nieuw artifact + databaseschema
  in een eigen repo (`paulRenDev/kompas`), geen uitbreiding op het
  bestaande Kompas.
- [x] **Signaalversheid** (17/9/2026): publicatie van een herhaald signaal
  zonder materiële wijziging wordt onderdrukt — harde publicatievoorwaarde
  (zie "Signaalversheid" hierboven).
- [x] **Chat-in-de-tool** (17/9/2026): bewust geschrapt — geen chatfunctie
  in Kompas zelf. Verdieping gebeurt in een gewone Claude-conversatie, die
  context ophaalt uit de bestaande database (zie "Verdieping via Claude"
  hierboven).
- [x] **Componentarchitectuur** (17/9/2026): kern + vier vervangbare
  poorten (signaalbron, portefeuillebron, geheugen, publicatiekanaal), elk
  met vandaag één personal adapter — zie "Architectuur — losse, vervangbare
  componenten" hierboven.
- [x] **Sector-specialistenpool in plaats van één generalist** (17/9/2026,
  Paul's beslissing: "we moeten meerdere sector analysten hebben, het gaat
  niet over slechts vijf sectoren"): elke gevolgde sector krijgt een eigen,
  smalle specialist-instantie; het aantal schaalt met wat relevant is,
  geen vast lijstje — zie "Pijler A" hierboven.
- [ ] **Sectorquotum buiten portefeuille/watchlist**: hoeveel van de
  specialist-pool moet structureel sectoren volgen die niets met Paul's
  huidige posities te maken hebben, puur voor tegengeluid — als
  verhouding (bv. 1 op 3), of als vast aantal? Nog te beslissen.
- [ ] **Staleness-drempel watchlist**: is 6 cycli (3 dagen) de juiste
  termijn vóór een naam gemarkeerd wordt voor herbeoordeling, of moet dit
  per sector/type verschillen? Nog te beslissen.
- [x] **Verplichte signaalvelden** (17/9/2026, bijgesteld na de
  technical-analyst-review): elk signaal moet omvang, tijdshorizon,
  databetrouwbaarheid, signaalbetrouwbaarheid en een citeerbare
  (niet-categorische) bron hebben, anders geen publicatie; technische
  signalen ook een `timeframe` — zie Poort 1 hierboven. Zonder deze
  velden kan de synthese-laag geen advies-consensus bouwen.
- [ ] **Klant-identiteit** (erkend 17/9/2026, niet ontworpen): een vijfde
  dimensie naast de vier poorten — wie de gebruiker/klant is, met opties en
  klantgegevens. Voor Paul's eigen gebruik is er precies één impliciete
  gebruiker; pas relevant zodra dit multi-tenant wordt. Niet nu bouwen.
- [ ] **Juridisch kader voor autonome aanbevelingen** (erkend 17/9/2026,
  niet blocking): een manuele review-stap past niet in dit systeem
  (draait volledig autonoom, zonder mens in de cyclus). Of dat een
  probleem is, hangt af van wie het aanbiedt en aan wie — een bank die
  eigen klanten op hun echte portefeuille adviseert zit in
  gereguleerd-advies-territorium; een fantasyfund/beleggerswedstrijd
  (geen echt geld, geen adviesrelatie) of financiële journalistiek
  (algemene modelportefeuille-commentaar, niet aan een geïdentificeerde
  klant gekoppeld) valt daar doorgaans buiten. Geen juridisch advies —
  bij een echte bank-uitrol hoort dit door een jurist bevestigd te worden.
  Voor Paul's persoonlijk gebruik niet van toepassing.
- [x] **Disclaimer** (17/9/2026): standaard, altijd toevoegen — "geen
  beleggingsadvies, enkel ter informatie, doe zelf onderzoek" op elke
  publicatie. Goedkoop, geen reden om het niet te doen. Beschermt het
  fantasyfund-/journalistiek-scenario mee (onderscheid algemene info vs.
  geïndividualiseerd advies), maar verandert niets aan de juridische
  classificatie zodra het substantieel geïndividualiseerd advies is (bv.
  een bank op een klant se eigen portefeuille) — een label, geen schild.

## Status

Nog niets gebouwd. Volgende stap: RSS-feed-URL's per rol ontvangen van
Paul, dan Pijler B (bestaat grotendeels al) als eerste effectief
implementeren.
