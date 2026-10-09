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

**Geïmplementeerd en getest (18/9/2026)** in `kompas/pijler_b/parser.py` —
onderstaande stappen zijn nu code, geen prosa-instructie meer. Zet de
ruwe, ongestructureerde pivot-tabeldump van de Google Sheet om naar de
generieke Poort 2-vorm (naam, aantal, waarde, cost, gain, totaalregel).
Dit hoort volledig bij deze adapter — een andere portefeuillebron
(Bolero, een snapshot, een custodian-feed) heeft hier niets aan en krijgt
zijn eigen, andere vertaallaag of geen enkele. Zie "Code — hoe het gebouwd
is" verderop voor de volledige module-indeling en hoe de tests te draaien.

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

## Materialiteitsdrempel voor macro-only signalen (22/9/2026)

Paul, over het Japan-monetair-beleid-signaal (het origineel van 18/9 én
het vervolg van 21/9): "remove the last japan paragraph. monetary
polici. i don't know how it passes every filter." Terecht nagekeken in
plaats van gewoon verwijderd: beide documenten hadden
`related_positions: []` en `related_watchlist: []` -- geen enkele link
naar iets dat Paul bezit of volgt. Het vervolgsignaal erkende dat zelfs
zelf, in zijn eigen `capital_view.reasoning`: "wordt pas een positie
waard zodra er een concreet Japan-blootgesteld signaal bijkomt" -- en
werd toch gepubliceerd. `validate_signal` checkt of een signaal goed
onderbouwd en compleet is (bron, omvang, tijdshorizon, betrouwbaarheid),
nooit of het uberhaupt relevant is. Dat is het echte gat: een macro-
signaal zonder positie-/watchlist-link en zonder verband met iets anders
kan elke kwaliteitscheck perfect doorstaan en toch pure ruis zijn.

**Nieuwe publicatiedrempel voor een macro/trend-signaal zonder
related_positions/related_watchlist-tag**: het moet op zichzelf ofwel
(a) een werkelijk zeldzaam of ongewoon groot gebeuren zijn, geen
routineuze, geplande centrale-bank-vergadering (de Fed-hike van 16/9
kwalificeert -- eerste verhoging in 3+ jaar; een gewone BOJ-vergadering
met een incrementele hike niet), ofwel (b) expliciet de onderbouwing
leveren voor een ANDER, wel actionable signaal (zoals de Fed-hike de
IWDA-`verhoog_bestaand`-call draagt), ofwel (c) zelf reeds gekwantificeerde,
ongewone inzet hebben (een oorlogseffect van 40% verstoorde
raffinagecapaciteit, een tarievenoorlog van USD 27,6 miljard) ook zonder
directe positielink -- "breed zoeken buiten de portefeuille" blijft
expliciet toegestaan, maar het signaal moet op eigen kracht substantieel
zijn, niet enkel netjes ingevuld. Dit is bewust GEEN mechanische regel in
`validate_signal` -- "is dit uberhaupt de moeite" is een oordeel dat
begrip vereist (was dit de eerste hike in 3 jaar, of een routineuze
vergadering?), geen keyword-check. Het blijft een verplichte afweging in
het schrijfproces zelf, gedocumenteerd hier en in de Routine-prompt.

Beide Japan-documenten (18/9 en 21/9) zijn verwijderd uit `events`.

## Thematische breedte — niet blijven hangen in datacenters (22/9/2026)

Paul: "please don't stay stuck in datacenters.. there still real wars,
trade wars, some lunatic presidents." Nagerekend: van de 18 signalen op
dat moment waren er 9 -- de helft -- rechtstreeks AI/chip/datacenter-
gethematiseerd (AMD x3, Huawei, Datacenter Lanaken x2, ASML x2, Uranium/
HALEU). Echte harde geopolitiek (oorlog, handelsoorlog, politieke
onvoorspelbaarheid) kwam nauwelijks aan bod -- Venezuela (goudbewaring,
geen oorlog), olie/Iran-diplomatie en het Zweeds defensie-orderboek waren
het enige dat in de buurt kwam. Geen enkel signaal over de daadwerkelijke
oorlog in Oekraine, geen handelsoorlog-signaal los van chips.

Zelfde onderliggende patroon als "Het 'wacht'-probleem" hieronder, nu
thematisch in plaats van per-headline: AI/chips is het dominante
financiele verhaal van 2026, dus een brede zoekopdracht blijft daar
vanzelf in hangen, ook al is de instructie om "breed te zoeken" op zich
gevolgd. Twee echte, nieuwe signalen geschreven als tegenwicht: Oekraine
se aanhoudende drone-campagne tegen Russische olieraffinaderijen (~40%
van de raffinagecapaciteit verstoord op het hoogtepunt -- een fysiek,
gemeten oorlogseffect, geen diplomatieke aankondiging), en de aparte
VS-Canada-handelsoorlog rond Section 338-tarieven (wederzijds 50% op
elk USD 27,6 miljard), die losstaat van de veel besproken VS-China-
verhoudingen en daardoor makkelijk wordt overgekeken.

**Nieuwe vaste pool-toevoeging**: `Sector specialist – Geopolitiek`
(oorlog, conflict, sancties, politieke onvoorspelbaarheid) staat er nu
expliciet naast de bestaande sectorspecialisten -- niet als eenmalige
uitzondering, maar als structureel onderdeel van de pool, zodat dit niet
opnieuw wegzakt. De Routine-prompt is bijgewerkt om elke cyclus expliciet
te wegen of de AI/chip-thematiek weer domineert, en zo ja, bewust
elders te zoeken.

## AI-bubbelmonitor (9/10/2026)

Paul, na Ray Dalio's waarschuwing in Bloomberg (7/10) dat AI "een klassieke
bubbel" is die dicht bij het barstpunt zit: "Houden jullie actief bubbel
breek signalen bij? Ik zou niet weten wat te monitoren hiervoor maar jullie
vast wel. [...] Het komt er op aan om de signalen tijdig te zijn."

Tot dan niet systematisch: signalen over AI kwamen binnen als ze toevallig
de materialiteitsdrempel haalden. Nu: `kompas.core.bubble_monitor` met zes
vaste indicatoren, elk met geschreven drempels voor oranje en rood --
rente, krediet voor AI, investeringen van de grote techbedrijven,
AI-omzet en chips, breedte van de beurs, hefboom en cash-out. Ze volgen
Dalio's eigen mechanisme (AI-investeringen op schuld ontmoeten een
stijgende rente; vermogen moet omgezet worden in geld) plus de klassieke
laat-in-de-bubbel-tekens. Het niveau volgt één vaste regel: alarm bij drie
keer rood, opletten bij één rood of drie oranje, anders rustig.

De avondcyclus van Pijler A schrijft elke avond één meting
(`bubble_monitor/{datum}`, via `bubble_reading_doc`); een status
verandert alleen op een feit met bron. Verandert het niveau, dan komt er
ook een signaal in de recap. Bij "alarm" opent de ochtendcall ermee. De
pagina toont de laatste meting.

Eerlijke grenzen, ook op de pagina: één keer per dag, niet live; het
verhoogt de kans om een breuk te zien aankomen, het voorspelt de top niet;
Dalio waarschuwt al sinds januari 2026, dus "opletten" kan maanden duren.
Een meting is nooit een verkooporder -- de regel "nooit verkoop voorstellen"
blijft staan tot Paul zelf iets anders beslist.

## Verhandelbaarheid: een idee dat Paul niet kan kopen is geen idee (7/10/2026)

Paul: "copx bestaat niet in medirect? wel in bolero maar is blijkbaar niet
verhandelbaar door bepaalde kosten die door de emittent niet doorgegeven
zijn." Een Belgische broker mag een fonds niet laten verhandelen als de
uitgever geen essentiële informatie en kostengegevens (KID) aanlevert. De
Global X Copper Miners UCITS ETF (COPX, IE0003Z9E2Y3) valt daaronder.

`kompas.core.capital_call.KNOWN_UNTRADABLE` houdt zulke instrumenten bij;
`validate_capital_call` weigert een call die er een als subject noemt of
het ISIN in de redenering zet. Het team moet dan een verhandelbaar
alternatief op hetzelfde idee noemen -- voor koper: de iShares Copper Miners
UCITS ETF (COPM, IE00063FT9K6, Euronext Amsterdam). Voorkeur voor fondsen
van grote uitgevers op beurzen waar Paul al handelt (Amsterdam, Parijs,
Londen); meldt Paul dat iets niet te koop is, dan komt het in die lijst.

## "Stilgevallen?" en het potje (6/10/2026)

Paul: "en stilgevallen? laatste update is van gisteren avond? btw je moet
100 euro niet letterlijk nemen. wat als ik nu een potje had waarin zou ik
investeren."

**Niet stilgevallen, wel onzichtbaar.** Op 6/10 liepen beide ochtendruns:
de portefeuille werd om 06:47 UTC ingelezen, de signalencyclus draaide
07:12-07:16 UTC en schreef een nieuwe call, maar vond geen nieuw materieel
signaal. De pagina toonde enkel het tijdstip van het nieuwste signaal
(zondagavond), dus een eerlijke lege cyclus zag eruit als een dode. Nieuw:
elke Pijler A-cyclus schrijft aan het eind `meta/last_cycle_a`
(`cycle_a_doc`: wanneer, hoeveel signalen en syntheses, of de call
bijgewerkt is), ook als er niets materieels was. De pagina toont dat als
"team keek laatst: ..." onder het laatste signaal.

**Het bedrag is niet letterlijk.** EUR 100 staat voor "geld dat nu aan het
werk kan". De call gaat over WAT het team zou kopen, niet over hoeveel:
een aandeel van meer dan EUR 100 is een geldig antwoord, en de eis "moet
met EUR 100 te kopen zijn" van 30/9 vervalt. De pagina zegt nu "Als het
team nu geld vrij had". `cap_check` blijft de vangrail, met EUR 100 als
nominale eenheid.

## EUR 100-vraag = de beste kans nu, de verdeling is een vangrail (30/9/2026)

Paul: "if the team will always only advice on the weight dispersion of the
existing stocks then I will always have to rebalance every position. It's
a never ending story. The idea of the 100 eur move is that my team feels
opportunities and when asked what would you invest your 100 eur now, what
investment would that be."

Hij heeft gelijk, en de fout zat in het ontwerp, niet in één call. Sinds
de teamverdeling van 28/9 stuurde elke EUR 100-call naar "de sleeve die het
verst onder haar marge zit" -- eerst NUCL tot energietransitie gevuld was,
dan IWDA omdat die NUCL-aankopen de kern verdunden. Zo wordt de vraag een
rekenoefening op wat hij al heeft, en elke aankoop maakt de volgende
"nodig". Dat is herbalanceren, en daar vroeg hij niet om.

Wat nu geldt:

- **De call beantwoordt één vraag:** als het team vandaag EUR 100 had,
  welke belegging zou het kopen, en waarom nu? Dat mag een bestaande
  positie zijn, een naam die Paul volgt (de watchlist is een vijver van
  kansen, nooit "de portefeuille") of iets nieuws. Het moet uit de
  signalen en syntheses van de cyclus komen, met een concreet waarom-nu,
  Farah se sterkste tegenargument en een trigger die het idee laat
  vervallen. *(Een eis "haalbaar met EUR 100" stond hier; die vervalt op
  6/10 -- het bedrag is niet letterlijk, zie de sectie hierboven.)*
- **De verdeling is een vangrail, geen takenlijst.**
  `kompas.core.allocation.cap_check` vervangt `steer_target`: het kiest
  nooit, het zegt enkel of EUR 100 extra een sleeve boven haar plafond
  duwt. Een sleeve onder haar minimum is informatie, geen opdracht. Een
  nieuwe naam buiten de sleeves is toegestaan en is een reden om de
  verdeling te herzien als Paul hem koopt. Op de pagina heet het blok nu
  "Teamverdeling -- vangrail, geen takenlijst", en "onder marge" krijgt geen
  waarschuwingskleur meer; enkel "boven plafond" doet dat.
- **"wacht"** mag enkel met een concreet, gedateerd moment binnen enkele
  dagen dat de call noemt -- anders is er altijd wel iets dat het team
  het liefst zou kopen.
- Gevolgde calls worden nog steeds erkend (`meta/last_refresh.changes`),
  maar een gevolgde call is geen reden om hetzelfde opnieuw te zeggen,
  noch om "het gat" dat hij achterliet te vullen.

De eerste call in die geest (30/9 avond): WIRE, de Xtrackers
Electrification Technologies & Smart Grid UCITS ETF -- de netbottleneck
(Siemens Energy EUR 51 miljard aan netorders, levertijden 3+ jaar; koper op
recordniveau) is het stuk energietransitie dat INRE en NUCL niet dekken.
Farah se bezwaar staat erbij: geen puur netfonds, veel AI-datacentervraag,
een jong en klein fonds. Energietransitie komt ermee op ongeveer 19,2%,
onder het plafond.

## Waarom het team bleef zeggen "koop NUCL" (30/9/2026)

Paul: "Why do you keep asking to add nucl? I did it twice now on the teams
advice but they don't seem to notice??" Nagerekend: NUCL ging van 12 naar
18 stukken (twee keer 3). Drie echte fouten, geen interpretatiekwestie:

1. **De portefeuille werd enkel 's avonds ingelezen.** De ochtendcall
   van 30/9 draaide op de inlezing van 29/9 18:49 en schreef als feit
   "sinds gisteravond niets bijgestuurd" -- iets wat hij niet kon weten.
   Fix: de Pijler B-Routine draait nu ook 's ochtends (06:45 UTC, vóór
   Pijler A), enkel om in te lezen. En een call mag nooit meer beweren
   dat er niets gekocht is zonder een inlezing ná de vorige call die dat
   aantoont.
2. **Aankopen werden niet als zodanig gezien.** Nieuw:
   `position_changes` legt bij elke inlezing vast wat er sinds de vorige
   inlezing gekocht of verkocht is (`meta/last_refresh.changes`). Beide
   Routines moeten dat eerst lezen en het benoemen ("je volgde de call")
   voor ze een nieuwe call maken.
3. **Het stoppunt schoof op.** Eerst "tot ~17%", dan "tot het midden van
   de marge", terwijl de teamverdeling niet zei wat er moet gebeuren als
   alle sleeves binnen hun marge zitten -- dus improviseerde elke call.
   Nieuw: `kompas.core.allocation.steer_target`, één vaste regel in code:
   eerst de sleeve het verst onder haar minimum, anders de sleeve het verst
   onder het midden van haar marge. Na Paul se aankopen gaf die regel meteen
   een ander antwoord: kern wereldwijd (IWDA), niet meer NUCL.
   *Dezelfde avond teruggedraaid -- zie de sectie hierboven: bijsturen naar
   de marges was zelf de fout, niet enkel het verschuivende stoppunt.*

Daarnaast bleek het vijfde getal in de totaalrij van de sheet géén
dagverschil te zijn maar het verschil met een oudere momentopname-rij
eronder. De "−€34 vandaag" van 28/9 was dus fout gelabeld. De dagbeweging
wordt nu berekend uit de Change(vsYday%)-kolom per positie
(`portfolio_day_change_eur`).

Een run die stopt, schrijft voortaan waarom (`meta/last_attempt`), zodat
een stille mislukking -- zoals de avondrun van 30/9, die na een minuut
zonder uitleg stopte -- zichtbaar wordt.

## Avondupdate portefeuille en teamverdeling (28/9/2026)

Paul: "an update end of day of my positions would be nice, as would a
short round up like this would do good in the evening update" -- na een
portefeuille-analyse waarin hij er ook op wees: "don't take into account
my watchlist. these are not positions." Diezelfde avond bijgestuurd:
"don't repeat the actual wallet i have it in sheets. look at it to
evaluate next to the other signals", en: "hou niet vast aan de
doelstellingen % verdeling die zijn oud. ik wil dat het team me stuurt
en energy transition maakt er natuurlijk ook deel van uit."

**De portefeuille wordt gelezen, niet herhaald.** "Posities zijn een
signaal-attribuut, nooit de paginastructuur" blijft dus volledig
gelden: de pagina toont geen positielijst, geen bedragen per positie.
Wel het oordeel van het team erover: een korte avond-round-up
(`kompas/core/roundup.py`, max 900 tekens) en de teamverdeling per
sleeve (marge, huidig gewicht, onder/binnen/boven). De watchlist speelt
hierin nooit mee -- die blijft enkel een tag-bron voor signalen.

**De teamverdeling vervangt de doelpercentages uit de sheet**
(`kompas/core/allocation.py`, collectie `allocation_views`, de nieuwste
geldt). Sleeves met een marge, een reden per sleeve, Vera se narratief
en Farah se tegenwerping -- zelfde discipline als een Synthesis. Eerste
versie (28/9): kern wereldwijd 55–60% (IWDA), energietransitie 15–20%
(NUCL + INRE, de enige sleeve die bewust groeit, hard plafond 20%),
waarde 10–15% (IWVL), defensief 10–15% (HLTW + COSW); geen opkomende
markten voorlopig (TSMC- en China/Taiwan-risico). Sturen gebeurt enkel
met nieuw geld, nooit via verkopen. Stabiel op zich: een nieuwe versie
komt er alleen als de eigen trigger afgaat of er een positie bij komt of
verdwijnt -- sturing die elke dag verschuift, is geen sturing. Een
positie die geen sleeve claimt, is op zich al een reden om te herzien.

**Signalen van 4 dagen of ouder verdwijnen van de pagina** ("4 dagen oud
en meer is nogal veel he. misschien losslaten."). Een verhaal dat na
drie dagen nog loopt, blijft zichtbaar via een vers vervolgsignaal, niet
via het oude. Dit is een weergaveregel op de pagina; de database houdt
alles.

**Pijler B stond tien dagen stil.** `mcp__Google_Drive__read_file_content`
geeft sinds september 2026 enkel nog een steekproef per tabblad terug,
geen volledige rijen -- de oude parser vond zijn headers niet meer en er
draaide geen automatische Pijler B-cyclus. De database stond nog op 18/9
en miste de Clean Energy-ETF (INRE, gekocht 21/9) en 4 IWDA-stukken van
dezelfde dag. Fix: een CSV-adapter (`parse_aandelen_csv`) op de export
van het "live"-tabblad via
`download_file_content(exportMimeType="text/csv")`. Beide formaten gaan
door dezelfde rij-gebaseerde header-regels; eerste echte run
reconcilieert tot op €0,04 (afronding, binnen tolerantie).

**Aparte Routine, weekdagen na de Europese slotbel** (`45 16 * * 1-5`:
18:45 CEST nu, 17:45 CET na de wintertijd -- beide na de sluiting van
Euronext om 17:30). Pijler B blijft zo los van Pijler A, zoals vanaf dag
1 vereist. De Routine ververst de posities (inclusief het verwijderen van
verkochte posities via `stale_position_doc_ids`), schrijft de round-up en
de EUR 100-call van die avond -- die weet als enige de slotkoersen en de
stand tegenover de teamverdeling. Pijler A schrijft daarom enkel nog 's
ochtends een capital call, ook tegen de teamverdeling gewogen.

**Openstaand bij aanmaak**: de Routine (`trig_014TxpQ79uMX6CmD3yEKJJxp`)
kon vanuit de bouwsessie geen Google Drive-connector meekrijgen. Zonder
die connector stopt elke run bij stap 1 en schrijft niets -- bewust, want
een round-up op verouderde cijfers is erger dan geen. De connector moet
eenmalig toegevoegd worden in de Routines-instellingen op claude.ai.

## EUR 100-vraag: één antwoord per cyclus, niet één per item (24/9/2026)

Paul, direct na het megaverhalen-onderzoek hierboven: "you can't just
keep repeating to wait. make it a separate line. If we (and by we i
mean the team) had 100 to spend, take this. in the end i will decide if
i follow. so remove it from every item and add one new item with what
you'd do with 100 eur." En, apart: "i think you should also drop items
when not relevant. only when the story is still relevant keep it
otherwise move on. its a daily recap."

Twee echte architectuurwijzigingen, geen extra regels op de bestaande
structuur:

**1. `capital_view` verhuisde van elk item naar één ding per cyclus.**
Elke Signal en elke Synthesis droeg tot nu toe zijn eigen `capital_view`
-- vandaar de 12-op-12 "wacht" uit het megaverhalen-onderzoek hierboven,
en drie afzonderlijke "wacht"-oordelen op zowel MP Materials als
Oekraine in plaats van één samengebrachte lezing. `capital_view` is
volledig verwijderd van `Signal` en `Synthesis` (`kompas/core/signal.py`,
`kompas/core/synthesis.py`). In de plaats: `kompas/core/capital_call.py`,
een nieuw `CapitalCall`-object -- exact één per cyclus, gebouwd NA alle
signalen en syntheses van die cyclus, dat alles samen afweegt (`considered`
noemt wat er afgewogen is) en één keer antwoord geeft op "als het team
vandaag 100 euro had, wat zou het doen." Weggeschreven naar een eigen
`capital_calls`-collectie (`capital_call_doc` in `kompas_db.py`), nooit
naar `events` of `synthesis`. Een echte "wacht" zonder specifiek subject
blijft een geldig antwoord -- dit dwingt geen actie af, het dwingt enkel
dat er nog maar ÉÉN keer per cyclus geantwoord wordt, niet N keer.
`web/index.html` toont deze ene call in een eigen sectie boven de
Synthese-sectie ("Het team se EUR 100-vraag"), met Paul's eigen
formulering erbij: "Paul beslist zelf of hij dit volgt." De oude
wacht/actie-verhouding in de headerregel is meeverhuisd, nu berekend over
de `capital_calls`-geschiedenis in plaats van over losse signalen.

**2. Recap-levenscyclus: `relevant` + `closed_reason` op Signal en Synthesis.**
Een signaal wordt nooit verwijderd (zie de materialiteitsdrempel-sectie
hierboven voor waarom de database een eerlijk archief blijft) -- maar
het hoeft niet permanent in de dagelijkse recap te blijven staan zodra
het eigen verhaal is afgerond, achterhaald, of overtroffen door iets
anders. Nieuw veld `relevant: bool = True` plus `closed_reason: str |
None`, verplicht ingevuld zodra `relevant=False` (dezelfde discipline als
elk ander veld: "niet relevant" zonder reden is even goedkoop als een
ongefundeerde "wacht" was). De live pagina filtert nu op `relevant !==
false` voor zowel `events` als `synthesis` voordat er iets gegroepeerd
of getoond wordt -- een gesloten signaal verdwijnt uit de recap, blijft
gewoon bestaan in de database. De Routine-cyclus moet dit expliciet
beoordelen (zie de bijgewerkte Routine-prompt): bij elke cyclus nagaan
of een nog-relevant verhaal daadwerkelijk nog relevant is, en zo niet,
sluiten met een echte reden via een `update`-write op het bestaande
document (nooit door het te herschrijven met signal_event_doc, en nooit
door het te verwijderen).

Geen enkel bestaand signaal of synthese-document is met terugwerkende
kracht aangepast door deze wijziging -- oude `capital_view`-velden in
al gepubliceerde documenten blijven gewoon staan als historisch record;
alleen nieuwe schrijfacties volgen het nieuwe model.

## Twee megaverhalen, niet meer thema's — de "themes don't change" klacht (24/9/2026)

Paul: "the themes dont change at all." Eerst nagerekend in plaats van
verdedigd: van de laatste 12 signalen (22-24/9, na de vorige thematische-
breedte-fix) zijn er wel degelijk vijf echte categorieen aanwezig --
oorlog/geopolitiek (Oekraine x3, Taiwan), handelsoorlog/grondstoffen (MP
Materials x3, VS-Canada), energie (Elia, Europese gasvoorraden),
defensie-tech (Thales) en chips (Huawei-vervolg). Op categorieniveau is
de vorige fix dus wel degelijk blijven staan.

Maar dieper kijken laat iets anders zien: 8 van de 12 signalen zijn geen
5 onafhankelijke verhalen, het zijn herhaalde check-ins op precies TWEE
lopende megaverhalen -- de Trump-Xi-top (Huawei, MP Materials x3, Taiwan
= 5 signalen) en het Oekraiense staakt-het-vuren-voorstel (Oekraine x3).
En van diezelfde 12 signalen heeft letterlijk elk exemplaar
`capital_view.action = "wacht"` -- geen enkele uitzondering sinds IWDA
(21/9). Hetzelfde patroon als "Het wacht-probleem" hieronder, alleen is
het onderwerp verschoven van "AI/chips" naar "vandaag se grootste
geopolitieke ontwikkeling" -- de instructie om breed te zoeken wordt
gevolgd, maar de instructie om niet op EEN verhaal te blijven hangen
kennelijk niet, ook al staat die er al sinds 22/9.

**Waarom dit keer geen nieuwe alinea in de Routine-prompt**: drie eerdere
ronden prosaregels (vroeg zoeken i.p.v. headline-achterna, trigger-
verantwoording, thematische breedte) losten elk hun eigen specifieke
symptoom op, maar het onderliggende patroon -- vasthouden aan het
grootste lopende verhaal van het moment -- overleefde alle drie. Nog een
alinea uitleg is voorspelbaar even makkelijk te rationaliseren als de
vorige drie. In plaats daarvan een mechanische regel, geen oordeelsvraag:

**Nieuwe harde eis**: elke cyclus met 3+ nieuwe of vervolgde signalen
moet minstens 1 signaal bevatten over een subject dat nog geen enkele
eerdere entry heeft in `events` -- een echt nieuw onderwerp, geen
vervolg op iets dat al loopt. Dit is mechanisch controleerbaar (query
`events` op `subject`, tel of er minstens 1 subject bij zit met 0
eerdere hits) en kan dus niet weg-geredeneerd worden zoals een "zoek
breed"-instructie dat wel kan. Vervolgsignalen op lopende megaverhalen
(Trump-Xi, Oekraine-staakt-het-vuren) blijven toegestaan en gewenst
zolang trigger-verantwoording (zie hieronder) echt is -- deze regel
verbiedt niet het volgen van een groot verhaal, ze verbiedt dat het de
ENIGE bron van signalen wordt per cyclus.

Derde, geverifieerde bevinding: de `synthesis`-collectie bevat na drie
dagen precies EEN document (AMD, 22/9). MP Materials en Oekraine kregen
elk drie signalen over drie cycli (22-24/9) -- exact het "2+ signalen
over hetzelfde subject"-criterium dat de Routine-prompt al sinds 22/9
verplicht een Synthesis voorschrijft -- maar geen van beide kreeg er een.
Ze bleven drie losse, herhaalde "wacht"-oordelen per subject in plaats
van een door Vera samengevoegde, door Farah tegengesproken lezing. Dat
verklaart een deel van het "voelt herhaald aan"-gevoel los van het
megaverhaal-probleem hierboven: dezelfde vaststelling drie keer na
elkaar herformuleren leest als stilstand, ook als de synthese-stap zelf
die stilstand zou doorbreken of expliciet bevestigen. De Synthesis-regel
was dus niet verkeerd, hij werd gewoon niet uitgevoerd -- vandaar
hieronder een expliciete, niet-overslaanbare check in plaats van een
voorwaardelijke "indien van toepassing"-formulering.

Dat lost het topic-deel op. Het lost het wacht-deel niet op, en dat
blijft na deze sessie een open vraag: is 12/12 wacht een
uitvoeringsprobleem (nog steeds te voorzichtig) of een reeel feit (alle
12 situaties zijn werkelijk nog onopgelost)? Bij lezing van de
individuele reasoning-velden lijkt het merendeel oprecht onopgelost (top
nog niet afgerond, staakt-het-vuren onbevestigd) -- maar dat is dezelfde
conclusie die drie weken geleden ook plausibel klonk voor AMD/ASML, en
toen bleek de onderliggende oorzaak wel degelijk een bias. Geen
verzonnen fix hiervoor totdat er echt bewijs is; blijft expliciet
openstaan.

## Het "wacht"-probleem — waarom bijna elk signaal daar landt (22/9/2026)

Paul, bot: "maar het lukt nog niet echt he?" Nagerekend in plaats van
verdedigd: van de 14 signalen met een `capital_view` zeggen 13 "wacht".
De enige uitzondering is IWDA — een indexfonds bijkopen na een dip, de
minst onderscheidende belegging die bestaat. Geen enkel individueel
aandeel-signaal heeft ooit tot een `nieuwe_positie` geleid.

**Eerste, te snelle diagnose**: "wacht" is gratis — een specialist kan
nooit ongelijk krijgen door te wachten, terwijl een overtuigde
`nieuwe_positie` zichtbaar fout kan blijken. Waar. Maar de scherpere
diagnose, na het echt doorlezen van de 13 wacht-redenen: bijna elke
technische lezing citeert "overbought" als reden (AMD RSI 80,7, ASML RSI
73,8, Cameco's eigen "Strong Sell"-label) — en dat is geen toeval. AMD op
USD 1.000 miljard marktkapitalisatie, Huawei tegen Nvidia, de
Fed-renteverhoging: dit zijn de grootste financiële krantenkoppen van de
dag op het moment dat Kompas ze vindt. Iets dat al de topheadline is, is
per definitie meestal al gelopen — vandaar overbought, vandaar wacht. Dit
is dezelfde "voor de hand liggende naam"-bias die al eerder opdook bij
ASML (zie Open vragen, feedparser-discussie) — ze is niet verdwenen, enkel
verschoven van "bekend aandeel" naar "vandaag se grootste headline".

**De fix is niet: de lat voor "nieuwe_positie" verlagen.** Kopen in
extreme, reeds gelopen momentum is een eigen fout, niet de oplossing voor
overmatige voorzichtigheid. De fix zit vroeger in de keten: bronnen
zoeken VOOR iets een headline wordt, niet erna. Twee concrete
aanpassingen, doorgevoerd in de Routine-prompt:

1. **Vroeg zoeken, niet de grootste headline achterna**: expliciete
   waarschuwing tegen het patroon "grootste financiële headline van de
   dag" — sectorvakpers, bedrijfsspecifieke persberichten en
   nichebronnen leveren vaker een signaal op VOOR de markt het al
   verwerkt heeft, wat de enige manier is om ooit tot een geloofwaardige
   `nieuwe_positie` te komen zonder in extended momentum te kopen.
2. **Trigger-verantwoording**: een vervolg op een bestaand "wacht"-signaal
   moet expliciet ingaan op de eigen `trigger` van het vorige signaal —
   is die voorwaarde intussen vervuld? Zo ja, is een nieuwe reflexmatige
   "wacht" niet genoeg; er moet een echte heroverweging staan, ook als de
   uitkomst opnieuw wacht is. Dit voorkomt dat een trigger een lege
   belofte blijft die nooit wordt ingelost.

Geen enkel bestaand signaal is met terugwerkende kracht omgezet naar een
ander standpunt — dat zou precies het soort verzinsel zijn dat dit hele
document probeert te vermijden. De verhouding wacht/actie is nu ook
zichtbaar op de pagina zelf (`web/index.html`), zodat dit patroon niet
verborgen blijft in de details van individuele signalen.

## Communicatie-exec review — voelt dit gemeend en fris? (21/9/2026)

Paul: "let every time a new update occurs a communication exec go through
the proposed output. she will be responsible to make sure this document
feels genuine and fresh." Een nieuwe, verplichte stap in het
schrijfproces — NA het onderzoeken/verifiëren/valideren van een signaal,
VOOR het geschreven wordt — gericht op stijl en toon, niet op feiten (die
horen al bij `validate_signal` en de zoek-verifieer-stap zelf).

Direct getest tegen de 11 signalen die op dat moment live stonden, en de
echte bevindingen waren niet cosmetisch: elk signaal opende met exact
dezelfde structuur (Onderwerp-Werkwoord-Cijfer); het woord "--" als
verbindingsteken kwam in bijna elke zin voor; "expliciet" kwam herhaald
terug in ongerelateerde signalen; de drie vervolg-signalen begonnen
allemaal letterlijk met "Update op het signaal van 18/9:". Het zwaarste
punt: vier verschillende rollen (Stock watchers, Trend viewers, Technical
stock watchers, een sector-specialist) klonken allemaal identiek — dat
ondermijnt net de reden om een POOL van specialisten te hebben in plaats
van één generalist. Alle 11 herschreven (enkel proza/toon, geen enkel
feit, cijfer, datum of bron gewijzigd) en live gepubliceerd.

Dit is bewust GEEN mechanische regel (geen verboden-woordenlijst, geen
lint-check op "--") — "fris" is geen eigenschap die een keyword-filter
zinvol kan afdwingen; dat zou net het soort schijnoplossing zijn die
"we're not pretending here" moet vermijden. Het blijft een redactionele
stap die wie een signaal schrijft zelf uitvoert: herlees de tekst en
`capital_view.reasoning` kritisch vóór het schrijven — klinkt dit als
gemeende, specifieke analyse, of als een sjabloon met andere cijfers
erin? Rollen mogen en moeten van elkaar verschillen in stem, niet enkel
in onderwerp.

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

**Gebroken helft gevonden (21/9/2026, Paul: "is the datacenter item still
relevant? it was news from last friday. same from japan and venezuela")**:
signaalversheid voorkomt HERHALING van een onveranderd signaal, maar er was
niets dat een cyclus dwong om terug te gaan en te CHECKEN of een
lopend/speculatief signaal intussen ontwikkeld is. Drie signalen van 18/9
stonden drie dagen ongewijzigd, en alle drie bleken bij echte controle
verouderd te zijn zonder dat de pagina dat liet zien: het Lanaken-signaal
had intussen een bedrijfsnaam (Switch Datacenters) die op 18/9 nog
ontbrak; het BOJ-signaal se eigen lezing (versnellende hikecyclus =
haviksachtig) werd tegengesproken door de daadwerkelijke marktreactie
(JGB-yield en yen allebei omlaag, duifachtig); het Venezuela-signaal bleef
onbevestigd en kreeg er een concrete procedurele blokkade bij (BoE wacht
op een VK-hofbevel dat nog niet is aangevraagd). Alle drie zijn nu
bijgewerkt als nieuwe signalen op hetzelfde onderwerp (`find_prior_signals`
matcht ze correct als vervolg, geen duplicaat). Twee structurele fixes:
(1) elke kaart toont nu de leeftijd van het signaal (`ageBadge` in
`web/index.html`), met een visuele marker vanaf 3 dagen ("check op
vervolg") — leeftijd is nu zichtbaar i.p.v. stilzwijgend; (2) de
tweemaaldaagse Routine-prompt is bijgewerkt om bij elke cyclus expliciet
ook bestaande speculatieve/lopende signalen op vervolg te checken, niet
enkel nieuwe onderwerpen te zoeken.

**Bijgesteld, zelfde dag**: de fix hierboven maakte vervolg-checks
verplicht bij elke cyclus, ongeacht wat er verder gebeurt — Paul corrigeerde
dat meteen: "perhaps it had developped but other things are more
important. no need to follow up on venezuela, or the belgian data center
if other big thing unfold. we want to find opportunities. that's up to
the specialists to determine." Het doel is opportuniteiten vinden, niet
een checklist afwerken — vervolg op een bestaand signaal is één mogelijke
bron van waarde naast nieuwe ontdekkingen, geen verplichting die daarmee
concurreert. De Routine-prompt is opnieuw bijgesteld: vervolg-checks zijn
nu een afweging voor de specialisten (verdient dit een plek t.o.v. een
mogelijk grotere nieuwe opportuniteit?), geen mechanische regel op
signaalleeftijd. De leeftijdsindicator op de pagina zelf blijft staan —
dat is pure transparantie (hoe oud is dit?), geen actie-dwang.

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

### Posities zijn een signaal-attribuut, nooit de paginastructuur (18/9/2026)

Paul: "in the final output we don't need to see the actual positions.
the analysts have to take it into account but even there need to
broaden to the things that actually happen. so these position is just
one signal amongst many many others." Dit gaat verder dan het
sectorquotum hierboven — het is een structureel principe voor zowel
Pijler A als de publicatie:

- **Analisten scannen niet enkel op positie-/watchlist-naam.** "Raakt
  dit een positie?" is één van de velden op een signaal (net als
  `omvang`, `tijdshorizon`, …), nooit het filter dat bepaalt of iets
  gedekt wordt. Een rol die feitelijk alleen maar posities/watchlist
  afgaat, is precies de bevestigingsbias die hierboven al erkend werd —
  nu expliciet ook voor Stock watchers en niet enkel voor de
  sector-specialistenpool.
- **De gepubliceerde pagina leidt met signalen/gebeurtenissen, niet met
  een positie- of watchlist-tabel.** Portefeuille-detail stond al niet
  op de pagina (zie eerder — "ga naar de sheet"); dit trekt het door:
  ook de watchlist wordt geen eigen, leidende sectie meer. Een signaal
  dat een positie raakt, toont dat als tag/context ("raakt: ASML,
  watchlist") — de positie is metadata op het signaal, niet omgekeerd.
- **Definitief besloten voor `web/index.html`** (18/9/2026, Paul: "I
  want you to use it as 1 of many signals but I don't want to see it. I
  already have it on my sheets"): geen "debug"-tussenstap — de pagina
  toont **nooit** posities/watchlist, ook niet tijdelijk. De ruwe
  Pijler B-data blijft wél volledig bestaan in de database
  (`wallet/state`, `wallet-positions/<ticker>-<exchange>`,
  `watchlist/<ticker>`) en wordt door Pijler A/de synthese-laag gebruikt
  om een signaal te taggen (`related_positions`/`related_watchlist`) —
  enkel de pagina zelf toont het nooit, want dat staat al in de sheet.
  `web/index.html` toont sinds deze beslissing uitsluitend de
  signalenfeed; geen aparte "verificatie"- of debug-sectie meer.

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

## Code — hoe het gebouwd is (18/9/2026, eerste echte implementatie)

Pijler B bestaat nu als werkende, geteste code — niet enkel als ontwerp.
Modulaire indeling, elk stuk met één verantwoordelijkheid, geen
vermenging van interpretatie ("intelligence") met vaste logica (Pijler B
heeft toevallig geen interpretatie — "puur feitelijk" — dus is dit
volledig deterministische code, precies zoals het hoort):

```
kompas/
  core/
    schema.py       — Poort 2-vormen (Position, WatchlistEntry, …).
                       Adapter-onafhankelijk: dit is de kern se contract,
                       niet iets van de Google Sheet-adapter.
  pijler_b/
    parser.py        — vertaallaag. Pure functie: ruwe dump-tekst in,
                        schema-objecten uit. Geen I/O.
    reconcile.py      — reconciliatie tegen de sheet's eigen totaalrij.
                        Pure functie, harde ok/niet-ok-poort.
    cycle.py          — orchestratie: parser → reconcile → (bij ok)
                        schrijf-payloads bouwen. Neemt ruwe tekst als
                        input, dus nog steeds test­baar zonder live sessie.
  db/
    kompas_db.py      — bouwt de ArtifactData-schrijfpayloads (pure). De
                        écht MCP-aanroepen (lezen via
                        mcp__Google_Drive__read_file_content, schrijven
                        via ArtifactData.batch) staan hier gedocumenteerd
                        als runbook, niet als code — dat kán geen bare
                        Python zijn, want die tools bestaan enkel binnen
                        een levende Claude-sessie. Eerlijk vermeld in de
                        module-docstring, niet weggemoffeld.
tests/
  fixtures/aandelen_sample.txt  — synthetische maar structureel identieke
                                   dump (dezelfde val-rijen als de echte
                                   sheet), geen echte portefeuillecijfers
                                   in git.
  test_parser.py, test_reconcile.py, test_cycle.py
```

**Getest, 17/17 groen**, stdlib-only (`unittest`, geen dependency),
draai vanuit de repo-root: `python3 -m unittest discover -s tests`. De
fixture-tests coderen de twee echte fouten uit "Werkelijke
portefeuille-structuur" hierboven als regressietests (een decoy-totaalrij
die niet gebruikt mag worden; setDate/totSetValueEUR die nooit als
purchaseDate/totPurValueEUR gelezen mag worden) — niet enkel de
happy path.

**Ook getest tegen de echte, live sheet** (niet enkel de fixture): zelfde
uitkomst als de handmatige verificatie eerder deze sessie —
gereconcilieerd (afwijking €0,05, enkel sheet-afronding, binnen
tolerantie), 6 posities, 24 watchlist-namen, 32 documenten klaar om te
schrijven. Dat resultaat staat nergens in git (de echte portefeuillecijfers
horen daar niet in) — enkel hier gemeld als bewijs dat het werkte.

**Nog niet gedaan:** de twee IO-randen echt uitvoeren binnen een
levende sessie (fetch + write via ArtifactData) — vandaag bewezen tot
en met de write-payloads, niet tot en met een echte schrijfactie in de
Kompas-database. Geen trigger die dit automatisch 2x/dag laat draaien.
Pijler A (signalenmotor) en de synthese-laag zijn nog niet aangeraakt.

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

**Correctie (18/9/2026):** deze sectie verwees eerder naar
`https://claude.ai/code/artifact/9f6bc549-e4df-4082-874b-cf5907bbaab0` —
dat is het **oude, Stocazzo-gekoppelde** Kompas-artifact, nog steeds
actief (het bleek bij een echte schrijfpoging deze sessie live en
recent bijgewerkt: rijke decision-journals per positie, ververst
vanochtend 09:00 CEST). Dat is precies het systeem dat deze herbouw
moest vervangen ("we wanted a new build because the old one wasn't
serving the purpose") — de vermelding hier was een overname uit het
oorspronkelijke ontwerpdocument, nooit gecorrigeerd tot dit moment.
**Nooit naar die url schrijven vanuit deze build.**

Deze build heeft zijn **eigen, nieuwe** artifact + database:
`https://claude.ai/artifact/9NceTjMZzLgV99KMEGGh1e` (aangemaakt
18/9/2026, bevestigd leeg bij aanmaak). Gedeelde database via de
`ArtifactData`-tool (apart van de `Artifact`-tool zelf). Vaste patronen:

- Elke actie vereist deze artifact-url (zie hierboven).
- Lezen: `get` (één document), `list` (een collectie), `query` (gefilterd).
- Schrijven: `set`/`update`/`batch` — gebruik `batch` (tot 50 writes,
  atomisch) zodra meerdere documenten wijzigen in één cyclus.
- Pin elke write met `if_version`, de versie gezien bij het laatste lezen.
  Een write zonder `if_version` overschrijft blind; een gepinde write die
  niet meer klopt faalt netjes.
- Collecties (18/9/2026, deze nieuwe database): `wallet/state`,
  `wallet-positions/<ticker>-<exchange>` (composite id — zie
  `kompas/db/kompas_db.py`, een bare ticker botst voor IWDA op AMS+LON),
  `watchlist/<ticker>`, `meta/last_refresh` — allemaal net voor het eerst
  gevuld door de echte Pijler B-cyclus, zie "Code — hoe het gebouwd is."
  `capital_map/ranking`, `events` bestaan nog niet — voor Pijler A.

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

## Werkelijke portefeuille-structuur (geverifieerd 18/9/2026 — live tegen de sheet)

Eerste keer dat de Google Sheet-verbinding en de vertaallaag écht getest
zijn deze sessie, in plaats van enkel beschreven. Resultaat: de aanname
achter de mockup en een deel van dit document klopt niet.

- **PORTEFEUILLE is geen stock-picking boek — het zijn 6 ETF's**, samen
  ≈ €5.846 waarde (aankoopwaarde €5.731,85, gain €114,20 = 1,99%,
  gereconcilieerd en exact kloppend met de sheet's eigen samenvattingsrij).
  Thematisch/factor-based met vaste doelbandbreedtes: 60% MSCI World
  (IWDA, twee noteringen), 15–20% Value (IWVL), 10% Health Care (HLTW),
  10% Consumer Staples (COSW), 5–10% Uranium (NUCL). Er zit geen ASML,
  NVDA, Cameco of Rheinmetall *in de portefeuille* — dat was een verkeerde
  aanname in de mockup.
- **Watchlist (24 namen) is echt watch-materiaal, geen bezit** (correctie
  18/9/2026, Paul: "watch list isn't owned its actual watch material" — ik
  had dit fout gelezen). Kolomnamen in dit blok zijn `setDate` en
  `totSetValueEUR`, niet `purchaseDate`/`totPurValueEUR` zoals in
  PORTEFEUILLE — structureel gelijkend blok, andere betekenis: `setDate`
  is wanneer de naam op de watchlist gezet werd, `totSetValueEUR` de
  referentiewaarde op dát moment (voor 1 hypothetisch aandeel), en
  `Rendement(EUR%)` toont dus "wat had ik gewonnen/gemist als ik toen 1
  aandeel had gekocht" — een conviction-/gemiste-kans-indicator, geen
  echte P&L. De 24 namen (ASML, NVDA, AMD, TSM, Cameco, Rheinmetall,
  Lockheed Martin, Thales, Saab, Wheaton Precious Metals, e.a.) zijn dus
  wél instapkandidaten, zoals oorspronkelijk ontworpen — brede spreiding
  over halfgeleiders, defensie, mijnbouw, medtech, industrie,
  infrastructuur.
  **Zelfcorrectie op de vorige versie van deze sectie:** ik had `setDate`
  gelezen als een aankoopdatum en de gain als echte P&L, puur omdat het
  blok dezelfde vorm heeft als PORTEFEUILLE — exact de valkuil die de
  vertaallaag-instructies beschrijven (nooit een kolomindex/betekenis
  aannemen, altijd aftellen tegen de headerrij van dát specifieke blok),
  hier optredend als een *semantische* versie van diezelfde val, niet enkel
  een positionele.
- **Impact op het ontwerp:** de oorspronkelijke indeling klopt dus alsnog —
  de 6 ETF's in PORTEFEUILLE zijn de echte "actieve posities"
  (houd/verkoop/bijkoop + bandbreedte-bewaking: zit Uranium nog binnen
  5–10%?), en de 24 watchlist-namen zijn instapkandidaten met een
  actiedrempel (zoals de decision objects al modelleerden). Wat wél moet
  worden meegenomen: `Rendement(EUR%) sinds setDate` is een authentiek,
  bruikbaar gegeven voor de watchlist-weergave (toont hoe lang gewacht
  wordt en tegen welke kost) — nog niet verwerkt in het ontwerp of de
  mockup.
- **De reconciliatie-discipline werkt, maar is scherp**: bij het narekenen
  greep ik zelf eerst de verkeerde "totaalrij" (een ander cumulatief
  overzicht verderop in de dump) vóór de juiste samenvattingsrij bovenaan
  bleek te kloppen — exact de valkuil die de vertaallaag-instructies
  hierboven al beschreven. Bevestigt dat die waarschuwing terecht is, niet
  theoretisch.

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
- **Aanvullende bronnenlijst van Paul getest** (18/9/2026): geopolitiek/
  macro/sector-kandidaten (International Crisis Group, Chatham House,
  BNP Paribas Economic Research, OilPrice, Ars Technica, FDA) allemaal
  `EGRESS_BLOCKED` via directe `WebFetch` — zelfde patroon als Bevinding 3,
  RSS-endpoint of niet maakt geen verschil, het is domeinniveau geblokkeerd.
  `WebSearch` blijft wél werken op deze domeinen (bv. `crisisgroup.org`
  live getest, actuele resultaten met bruikbare bronvermelding) — Bevinding
  4 bevestigd op een bredere set. Conclusie ongewijzigd: sector-specialisten
  zonder bereikbare feed gebruiken `WebSearch`, geen directe RSS-parse,
  zolang dit binnen een Claude-sessie draait.
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
  **Heropend door de PM-scope-review (21/9/2026)**: `capital_view` (zie
  Poort 1 hieronder) is de eerste feature die er structureel uitziet als
  een aanbeveling (nieuwe_positie/verhoog_bestaand/wacht + reden) i.p.v.
  een plat signaal, ook al is de framing bewust hypothetisch ("als ik
  EUR 100 vrij had"). Verandert de conclusie niet voor Paul se eigen
  gebruik, maar dit is het punt om op terug te komen als dit ooit
  richting een andere gebruiker (bank, derde partij) zou gaan.
- [x] **Disclaimer** (17/9/2026): standaard, altijd toevoegen — "geen
  beleggingsadvies, enkel ter informatie, doe zelf onderzoek" op elke
  publicatie. Goedkoop, geen reden om het niet te doen. Beschermt het
  fantasyfund-/journalistiek-scenario mee (onderscheid algemene info vs.
  geïndividualiseerd advies), maar verandert niets aan de juridische
  classificatie zodra het substantieel geïndividualiseerd advies is (bv.
  een bank op een klant se eigen portefeuille) — een label, geen schild.
- [ ] **TODO — dichter bij de expert-reviewed mockup blijven** (18/9/2026,
  Paul: "I think you need to keep more to the mockup we made with the
  experts"). De huidige `web/index.html` is een sterk vereenvoudigde
  signalenfeed (platte kaarten); de mockup uit de sector-/technical-
  analyst-reviews had rijkere structuur: sector-spotlightkaarten met
  omvang/tijdshorizon/bron/vertrouwen in een apart blok, expliciete
  conflict-callouts tussen rollen, capital map/ranking met scorebalken,
  decision objects met actiedrempel. Nog niet doorgevoerd — enkel
  vastgelegd als te doen, geen ontwerpbeslissing genomen over hoe de twee
  te verzoenen (rijke kaarten + "geen posities tonen" staan niet
  haaks op elkaar, maar zijn nog niet samen uitgewerkt).
  **Voortgang (18/9/2026)**: de mockup effectief gelezen (`project/Main.dc.html`
  van het canvas). Drie stukken zijn nu echt gebouwd, tegen echte
  signalen uit de database (geen mock-data):
  1. **Sector-spotlight** — `kompas/pijler_a/spotlight.py`
     (`cross_specialist_subjects`, puur, getest): een onderwerp dat door
     2+ verschillende rollen geraakt is, krijgt de rijke spotlight-kaart
     (omvang/horizon/bron-blok, geraakt-tags); één rol op één onderwerp
     blijft in het compacte rollen-grid. Vandaag heeft geen enkel echt
     signaal een tweede rol op hetzelfde onderwerp — de sectie toont dus
     eerlijk een lege staat i.p.v. een verzonnen kruising.
  2. **Conflict-callout** — bewust NIET mechanisch afgeleid (twee
     signalen met afwijkende betrouwbaarheid is geen conflict-detectie,
     dat vereist het lezen van beide teksten). Nieuw optioneel veld
     `Signal.conflict_note`: een auteur zet dit zelf, na het lezen van
     een eerder signaal over hetzelfde onderwerp. Nog geen enkel echt
     signaal heeft dit veld gezet, dus de sectie is nu verborgen
     (`display:none`) i.p.v. leeg getoond.
  3. **`web/index.html` herbouwd** in de mockup's visuele taal (IBM Plex
     Mono/Sans, kaartstijl, spotlight/rollen-grid/conflict-layout) maar
     volledig data-gedreven vanuit `events`, met behoud van beide
     thema's (licht/donker) — de mockup zelf was single-theme static.
  
  **Nog bewust NIET meegenomen, met reden**: Watchlist-tabel, capital
  map/ranking, en decision objects. De mockup se decision-objectsectie
  is expliciet gestructureerd "per positie / watchlist-naam" met een
  `kernpositie`-label en positiebeheer-acties ("verhoog positie met max.
  1 satelliet-eenheid") — dat structureert de pagina rond posities,
  precies wat "Posities zijn een signaal-attribuut, nooit de
  paginastructuur" verbiedt. Mijn voorstel, niet doorgevoerd zonder
  Paul se akkoord: (a) Watchlist tonen kán zonder de regel te breken —
  niet als duplicaat van Paul se privé Google Sheet-watchlist, maar als
  een eigen, door Kompas se analistenpool gecureerde lijst (nieuwe
  namen die een signaal opleverden, los van wat al in de Sheet staat) —
  dit is exact wat Paul zelf voorstelde ("if the tool comes up with
  other interesting stock ideas, I might add it"); (b) capital
  map/ranking en decision objects kunnen wel, maar herschreven in
  signaal-ruimte i.p.v. positie-ruimte: een kansen-score per onderwerp
  (niet per positie), geen `kernpositie`-label, geen concrete
  aandelen-/eenheidsacties. Nog niet gebouwd — wacht op Paul se akkoord
  over deze twee punten specifiek, niet op een volledige nieuwe
  discussie.
- [x] **`Signal.capital_view` — de "EUR 100"-vraag** (21/9/2026, Paul se
  framing: als ik EUR 100 vrij had, zou dit signaal het (A) in een nieuwe
  naam zetten, (B) een bestaande positie laten groeien, of (C) wachten op
  een beter moment?). Optioneel veld, zelfde plaats als
  `related_positions`/`conflict_note` — nooit een apart, positie-gekeyed
  sectie zoals de mockup se decision objects. Geen allocatie%, aantal of
  P&L wordt getoond; `verhoog_bestaand` vereist een echte
  `related_positions`-tag (`validate_signal` controleert dit — een
  watchlist-naam is geen positie, kan dus niet "groeien").
  Toegepast op de 4 signalen van vandaag: alle vier landen eerlijk op
  "wacht", elk om een andere, in de tekst onderbouwde reden (macro-signaal
  zonder aandeel-hoek; de HALEU-bron zelf noemt de korte-termijn-impact
  beperkt; ASML se cijfers en analistenoordeel wijzen niet dezelfde kant
  uit; ASML se technische plaatje is bullish maar overbought). Geen
  "nieuwe_positie"/"verhoog_bestaand"-voorbeeld geforceerd om variatie te
  tonen — dat zou precies het soort verzinsel zijn dat de rest van dit
  project probeert te vermijden.
  **Review door specialisten + PM (21/9/2026, op Paul se vraag)** — twee
  echte bevindingen, geen formaliteit:
  1. *Specialisten*: niets koppelde `capital_view` aan
     `signal_confidence`, dus een `speculatief`-signaal kon toch
     `nieuwe_positie` krijgen — dat overschat een signaal dat de auteur
     zelf als onbewezen labelde (exact de fout bij het technische
     ASML-signaal, dat toevallig "wacht" koos, maar de regel dwong dat
     niet af). **Gefixed**: `validate_signal` verwerpt nu
     `nieuwe_positie` op een speculatief signaal — minstens "voorlopig"
     vereist.
  2. *PM/scope*: `capital_view` ziet er structureel uit als een
     aanbeveling (actie + reden), ook al is de framing hypothetisch. Geen
     codewijziging — heropent "Juridisch kader voor autonome
     aanbevelingen" hierboven met een expliciete verwijzing naar deze
     feature. Ook genoteerd om te bewaken tijdens de week-test: als
     "wacht" altijd de uitkomst is, is dit misschien schijn-besluitvorming
     in plaats van een echte aanvulling — pas op als een reeks signalen
     met sterke, uiteenlopende bewijslast toch allemaal op "wacht"
     uitkomt.
- [ ] **TODO — standalone `feedparser` + directe Anthropic API als
  alternatieve Poort 1-adapter** (18/9/2026, Paul deelde een
  Python-script: `feedparser` + `Anthropic()`-client, buiten een Claude-
  sessie om). Sluit aan bij de eerdere Routines-vs-GitHub-Actions-
  discussie: dit is precies het patroon dat portabiliteit zou geven
  (geen MCP/sessie-afhankelijkheid). Twee concrete gebreken in het
  gedeelde script, niet doorgevoerd naar productie: (1) de opgegeven
  URL's (yahoo.com, marketwatch.com, seekingalpha.com) zijn homepages,
  geen RSS-feed-endpoints — `feedparser` zou hier leeg op teruggeven,
  (2) het model (`claude-3-5-sonnet-20241022`) is een verouderde,
  gedateerde snapshot — nu `claude-opus-5` (standaard) of `claude-sonnet-5`
  (hoger volume/goedkoper).
  **Beslissing (18/9/2026, "ask the senior developer")**: nu niet bouwen.
  Twee redenen, geen smaak: (1) de schrijfkant (`ArtifactData`) heeft nog
  geen externe API — een standalone script zou wél kunnen lezen/analyseren,
  maar nergens naartoe kunnen schrijven, dus het sluit de lus niet; (2) het
  script se patroon ("vat deze batch headlines samen" in één niet-agentic
  call) is een kwaliteitsstap terug tegenover het multi-stap, geverifieerde
  proces dat de drie echte signalen tot nu toe opleverde (zoek → tweede
  zoekopdracht ter verificatie → eerlijk relevantie-oordeel over
  portefeuille-/watchlist-link) — nu automatiseren zou een ondiepere aanpak
  vastklikken dan wat handmatig al werkt. Zelfde regel als bij de
  Routines-vs-GitHub-Actions-afweging: geen automatiseringsinfrastructuur
  vóór het geautomatiseerde proces zijn waarde bewezen heeft. Blijft TODO,
  heropenen zodra Poort 3 een externe schrijf-API heeft óf het handmatige
  proces een herhaalbare stap is geworden die effectief te automatiseren
  valt.

## Status

**Oude Kompas volledig vervangen, geen twee actieve takken meer** (21/9/2026,
Paul: "this artefact should completely replace the old one. i don't want
two active branches"). Ontdekt tijdens deze sessie: twee bestaande Routines
("Kompas ochtendrefresh" en "Kompas avondrefresh", sinds 24/8/2026) draaiden
al die tijd nog gewoon door, en verversten dagelijks het OUDE
Stocazzo-gekoppelde Kompas-artifact
(`https://claude.ai/code/artifact/9f6bc549-e4df-4082-874b-cf5907bbaab0`) —
precies de url die overal in dit document als "nooit naar schrijven"
gemarkeerd staat. Beide Routines zijn nu uitgeschakeld (niet verwijderd —
geschiedenis blijft bewaard, `enabled: false`). Dit build se eigen artifact
(`https://claude.ai/artifact/9NceTjMZzLgV99KMEGGh1e`) is vanaf nu de enige
actieve Kompas.

**Pijler A draait nu ook automatisch, week-test gestart** (21/9/2026): een
nieuwe Routine (`0 7,16 * * *`, elke firing een verse sessie) draait de
signalencyclus tweemaal daags. Voor het opstarten was de database drie dagen
lang stil blijven staan op de 3 signalen van 18/9 — de sector-spotlight en
conflict-callout hadden dus nooit een kans om te vullen, niet omdat de
mechaniek niet werkt maar omdat de cyclus zelf nooit herhaald werd. Vier
nieuwe, echte signalen erbij geschreven (Fed-renteverhoging, een
HALEU-brandstofcontract, en een echte cross-role spotlight op ASML —
Stock watchers x Technical stock watchers, twee onafhankelijke, niet-
verzonnen lezingen op hetzelfde onderwerp). Elk signaal kreeg ook een
`capital_view` (zie Poort 1/Open vragen) — alle vier landen eerlijk op
"wacht".

**Pijler B draait echt, end-to-end, voor het eerst** (18/9/2026). Niet
enkel code en tests: een volledige, live cyclus is met de hand uitgevoerd
— sheet gelezen, vertaald, gereconcilieerd, en **32 documenten
daadwerkelijk geschreven** naar `https://claude.ai/artifact/9NceTjMZzLgV99KMEGGh1e`,
deze build se eigen, nieuwe database (bevestigd leeg bij aanmaak, dus
een echte eerste schrijving, geen overschrijving van iets bestaands).
Een minimale statuspagina (`web/index.html`, ook in de repo) leest die
database live en toont wat erin staat. 17/17 tests groen, plus deze ene
echte run als bewijs dat het ook buiten de tests werkt.

Wat dit run zelf nog blootlegde en meteen gefixed is: de sheet houdt
`IWDA` op twee beurzen (AMS en LON) als aparte posities — een write
sleutel op enkel de ticker zou de twee laten botsen. Opgelost met een
`ticker-exchange`-composite-id, met een regressietest die dat specifiek
reproduceert (zie `test_duplicate_ticker_on_two_exchanges_does_not_collide`).

**Belangrijke correctie deze sessie**: de database-url verwees eerder
naar het oude, Stocazzo-gekoppelde Kompas-artifact
(`.../artifact/9f6bc549-...`) — nog steeds actief, met rijke
decision-journals, ververst vanochtend. Dat is precies het systeem dat
deze herbouw moest vervangen. Nooit beschreven, nu gecorrigeerd: deze
build heeft zijn eigen artifact + database, volledig gescheiden.

**Pijler A is gestart** (18/9/2026): `kompas/core/signal.py` legt het
Poort 1-schema en de harde publicatievoorwaarde vast als code
(`validate_signal`), `kompas/pijler_a/freshness.py` de
signaalversheid-lookup, `kompas/db/kompas_db.py` bouwt en valideert het
schrijf-document voor `events`. 32/32 tests groen (zie
`tests/test_signal.py`, `test_freshness.py`, `test_signal_event_doc.py`).

**Eén echt signaal geschreven, niet gesimuleerd**, en bewust **niet**
gekoppeld aan een positie — een live WebSearch naar wat er die dag
daadwerkelijk gebeurde (niet naar een van Paul's namen) vond de
BOJ-renteverhoging van 18/9/2026 (+25bp naar 1,25%, hoogste niveau sinds
1995, stemming 7-2 — CNBC, tier 1). Gevalideerd, gecheckt tegen een lege
`events`-collectie (dus fris), geschreven naar `events/japan-monetair-beleid-2026-09-18-trend-viewers`.
Bewust `related_positions`/`related_watchlist` leeg gelaten — geen van
de 6 ETF's is Japan-/JPY-specifiek, en een tag forceren om het signaal
"relevanter" te doen lijken zou precies ingaan tegen "Posities zijn een
signaal-attribuut" hierboven.

`web/index.html` toont sinds Paul's definitieve beslissing (zie
"Posities zijn een signaal-attribuut" hierboven) **uitsluitend** de
signalenfeed — geen Portefeuille/Posities/Watchlist-sectie meer, ook
niet als debug-weergave. Die data bestaat en wordt gebruikt, wordt
alleen nooit meer op de pagina getoond.

**Twee signalen erbij** (18/9/2026, Paul: "maybe my positions are not
interesting at all nor my watchlist. Think out of the box and use real
signals from rss feeds") — beide uit de al-geverifieerde RSS-bronnen
(`docs/kompas-rss-signaalscan.md`), niet uit WebSearch:
- **VRT NWS** (rechtstreeks RSS-feed): een aangekondigde investering van
  €1 miljard in een datacenter op de voormalige Sappi-site in Lanaken —
  een lokaal, Nederlandstalig signaal dat Engelstalige financiële media
  niet zouden oppikken. Eerlijk gelabeld: geen investeerbare naam
  geïdentificeerd achter dit specifieke project, het signaal is
  thematisch (de AI-datacentergolf wordt tastbaar tot in kleine
  industriesteden).
- **Investing.com commodities-feed** + verdiepende `WebSearch`: Venezuela
  zou USD 4 miljard aan goudreserves verhuizen van de Bank of England
  naar de NY Fed — geopolitiek/edelmetalen-signaal, bewust **niet**
  getagd aan Wheaton Precious Metals (wél op de watchlist) omdat er geen
  directe operationele link is, enkel een gedeeld "goud"-thema — te los
  om als "raakt" te tellen.

Alle drie signalen tot nu toe hebben lege `related_positions`/
`related_watchlist` — geen enkele is geforceerd gekoppeld aan iets wat
Paul al bezit of volgt. Dat is het bewijs dat het principe werkt, niet
een toevallige uitkomst.

Nog te bouwen, in volgorde: (1) een daadwerkelijk triggermechanisme voor
de twee dagelijkse cycli (09:00 en 18:00 CEST) — vandaag is elke cyclus
eenmalig met de hand gedraaid, niets automatiseert dit nog; besproken
maar bewust nog niet aangezet (zie de discussie hierboven over
Routines vs. GitHub Actions — senior-engineer keuze: eerst bewijzen dat
het de moeite waard is, dan pas automatiseren), (2) Pijler A uitbreiden
naar de eigenlijke rollen/sector-specialistenpool als herhaalbaar
proces (vandaag: één hand-geschreven signaal, geen rol-per-rol-cyclus),
(3) een concreet documentschema voor `capital_map/ranking` en de
synthese-laag zelf — nog enkel prosa-vormbeschrijving, (4) de mockup
herbouwen op deze geverifieerde, echte data en het signaal-leidende
principe (nu nog fictieve namen/cijfers, positie-centrische structuur).
