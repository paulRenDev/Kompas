"""Pijler A  Bronnen configuratie.

Beheert de RSS-feeds en WebSearch zoekopdrachten voor elke analistrol.
Gebaseerd op de bevindingen in docs/kompas-rss-signaalscan.md.

Bronnen zijn onderverdeeld in:
1. Werkende RSS-feeds (direct bereikbaar via WebFetch)
2. WebSearch zoekopdrachten (voor bronnen die niet als RSS beschikbaar zijn)
3. Investing.com pagina's (direct bereikbaar, geen RSS maar wel bruikbaar)

Elke bron heeft:
- Een unieke identifier
- Een type (rss, websearch, investing_page)
- De URL of zoekopdracht
- De bijbehorende rol(ren)
- Tier classificatie
- Sector focus (indien van toepassing)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar

from kompas.pijler_a.roles import (
    STOCK_WATCHERS,
    TREND_VIEWERS,
    TECHNICAL_STOCK_WATCHERS,
    SectorSpecialist,
)


class SourceType(Enum):
    """Type bron voor het ophalen van data."""
    RSS = "rss"              # Directe RSS-feed
    WEBSEARCH = "websearch"  # WebSearch zoekopdracht
    INVESTING_PAGE = "investing_page"  # Investing.com nieuwspagina


class SourceTier(Enum):
    """Tier classificatie voor bronnen (zie README, Poort 1)."""
    TIER_1 = "tier 1"  # Primaire bron (officiële persberichten, centrale banken)
    TIER_2 = "tier 2"  # Secundaire bron (financiële journalistiek, aggregators)


@dataclass(frozen=True)
class Source:
    """Definieert een bron voor Pijler A."""

    id: str
    name: str
    source_type: SourceType
    url_or_query: str
    tier: SourceTier
    
    # Welke rol(ren) gebruiken deze bron
    roles: list[str] = field(default_factory=list)
    
    # Sector focus (indien van toepassing)
    sector: str | None = None
    
    # Beschrijving
    description: str = ""
    
    # Voor WebSearch: extra parameters
    search_params: dict[str, str] = field(default_factory=dict)


# ============================================================================
# Werkende RSS-feeds (bevestigd in docs/kompas-rss-signaalscan.md)
# ============================================================================

# Algemene nieuwsbronnen
RSS_SOURCES: list[Source] = [
    Source(
        id="vrt_nws",
        name="VRT NWS",
        source_type=SourceType.RSS,
        url_or_query="https://www.vrt.be/vrtnws/nl.rss.articles.xml",
        tier=SourceTier.TIER_2,
        roles=[STOCK_WATCHERS.name, TREND_VIEWERS.name],
        description="Algemeen Vlaams nieuws",
    ),
    Source(
        id="nos_nieuws",
        name="NOS Nieuws",
        source_type=SourceType.RSS,
        url_or_query="https://feeds.nos.nl/nosnieuwsalgemeen",
        tier=SourceTier.TIER_2,
        roles=[STOCK_WATCHERS.name, TREND_VIEWERS.name],
        description="Algemeen Nederlands nieuws",
    ),
    
    # Centrale banken (Tier 1 voor Trend viewers)
    Source(
        id="ecb_press",
        name="ECB Persberichten",
        source_type=SourceType.RSS,
        url_or_query="https://www.ecb.europa.eu/rss/press.html",
        tier=SourceTier.TIER_1,
        roles=[TREND_VIEWERS.name],
        description="ECB persberichten (monetair beleid)",
    ),
    Source(
        id="fed_press",
        name="Federal Reserve Persberichten",
        source_type=SourceType.RSS,
        url_or_query="https://www.federalreserve.gov/feeds/press_all.xml",
        tier=SourceTier.TIER_1,
        roles=[TREND_VIEWERS.name],
        description="Fed persberichten (monetair beleid)",
    ),
    
    # Investing.com RSS-feeds (Tier 2)
    Source(
        id="investing_stock_news",
        name="Investing.com Aandelennieuws",
        source_type=SourceType.RSS,
        url_or_query="https://www.investing.com/rss/news_25.rss",
        tier=SourceTier.TIER_2,
        roles=[STOCK_WATCHERS.name],
        description="Algemeen aandelennieuws",
    ),
    Source(
        id="investing_commodities",
        name="Investing.com Grondstoffen",
        source_type=SourceType.RSS,
        url_or_query="https://www.investing.com/rss/news_11.rss",
        tier=SourceTier.TIER_2,
        roles=[STOCK_WATCHERS.name],
        sector="Energie",
        description="Grondstoffen en futures nieuws",
    ),
    Source(
        id="investing_economic",
        name="Investing.com Economische Indicatoren",
        source_type=SourceType.RSS,
        url_or_query="https://www.investing.com/rss/news_95.rss",
        tier=SourceTier.TIER_2,
        roles=[TREND_VIEWERS.name],
        description="Macro-economische data",
    ),
    Source(
        id="investing_forex",
        name="Investing.com Forex",
        source_type=SourceType.RSS,
        url_or_query="https://www.investing.com/rss/news_1.rss",
        tier=SourceTier.TIER_2,
        roles=[TREND_VIEWERS.name],
        description="Valuta en macro nieuws",
    ),
]


# ============================================================================
# WebSearch zoekopdrachten (voor sector specialisten)
# ============================================================================

# Sector-specifieke zoekopdrachten
SECTOR_SEARCH_QUERIES: dict[str, list[str]] = {
    "Halfgeleiders": [
        "semiconductor industry news",
        "chip manufacturing news",
        "AI chip demand news",
        "TSMC ASML NVIDIA news",
    ],
    "Defensie": [
        "defense industry news",
        "military spending news",
        "defense contracts news",
        "Lockheed Martin Rheinmetall Thales news",
    ],
    "Uranium/Nucleair": [
        "uranium mining news",
        "nuclear energy news",
        "Cameco Kazatomprom news",
        "nuclear power expansion news",
    ],
    "Datacenter-infra": [
        "datacenter industry news",
        "AI infrastructure news",
        "cloud computing demand news",
        "Crusoe Equinix Digital Realty news",
    ],
    "Energie": [
        "energy sector news",
        "oil gas prices news",
        "renewable energy news",
        "energy transition news",
    ],
    "Gezondheidszorg": [
        "healthcare sector news",
        "pharmaceutical industry news",
        "biotech news",
        "medical technology news",
    ],
    "Consumentengoederen": [
        "consumer staples news",
        "food beverage industry news",
        "retail sector news",
        "consumer goods demand news",
    ],
    "Edelmetalen": [
        "precious metals news",
        "gold silver prices news",
        "Wheaton Precious Metals news",
        "mining industry news",
    ],
    "Infrastructuur": [
        "infrastructure investment news",
        "construction sector news",
        "transportation logistics news",
        "public infrastructure news",
    ],
}


# Anti-bevestigingsbias quotum: sectoren buiten portefeuille/watchlist
ANTI_BIAS_SECTORS: list[str] = [
    "Automotive",
    "Financial Services",
    "Real Estate",
    "Telecommunications",
    "Materials",
    "Utilities",
]


# WebSearch bronnen voor sector specialisten
WEBSEARCH_SOURCES: list[Source] = [
    Source(
        id=f"websearch_{sector.lower().replace('/', '_').replace(' ', '_')}",
        name=f"WebSearch {sector}",
        source_type=SourceType.WEBSEARCH,
        url_or_query=f"{sector} news",
        tier=SourceTier.TIER_2,
        roles=["Sector specialist"],
        sector=sector,
        description=f"WebSearch zoekopdrachten voor {sector}",
        search_params={"time_range": "last_24_hours", "language": "en"},
    )
    for sector in list(SECTOR_SEARCH_QUERIES.keys()) + ANTI_BIAS_SECTORS
]


# ============================================================================
# Investing.com nieuwspagina's (direct bereikbaar, geen RSS)
# ============================================================================

INVESTING_PAGES: list[Source] = [
    Source(
        id="investing_stock_market_news",
        name="Investing.com Stock Market News",
        source_type=SourceType.INVESTING_PAGE,
        url_or_query="https://www.investing.com/news/stock-market-news",
        tier=SourceTier.TIER_2,
        roles=[STOCK_WATCHERS.name, TREND_VIEWERS.name],
        description="Stock market nieuws pagina",
    ),
    Source(
        id="investing_technology_news",
        name="Investing.com Technology News",
        source_type=SourceType.INVESTING_PAGE,
        url_or_query="https://www.investing.com/news/technology-news",
        tier=SourceTier.TIER_2,
        roles=[STOCK_WATCHERS.name],
        sector="Halfgeleiders",
        description="Technologie en halfgeleiders nieuws",
    ),
    Source(
        id="investing_commodities_page",
        name="Investing.com Commodities Page",
        source_type=SourceType.INVESTING_PAGE,
        url_or_query="https://www.investing.com/commodities/",
        tier=SourceTier.TIER_2,
        roles=[STOCK_WATCHERS.name],
        sector="Energie",
        description="Grondstoffen overzichtspagina",
    ),
]


# ============================================================================
# Technische bronnen (voor Technical Stock Watchers)
# ============================================================================

# Technische pagina's per ticker (dynamisch gegenereerd)
TECHNICAL_SOURCES_TEMPLATE: str = "https://www.investing.com/equities/{ticker}-technical"


# ============================================================================
# Hulpfuncties
# ============================================================================

def get_sources_for_role(role_name: str) -> list[Source]:
    """Get alle bronnen voor een specifieke rol."""
    sources = []
    
    # Voeg RSS bronnen toe
    for source in RSS_SOURCES:
        if role_name in source.roles:
            sources.append(source)
    
    # Voeg Investing.com pagina's toe
    for source in INVESTING_PAGES:
        if role_name in source.roles:
            sources.append(source)
    
    return sources


def get_sources_for_sector(sector: str) -> list[Source]:
    """Get alle bronnen voor een specifieke sector."""
    sources = []
    
    # Voeg WebSearch bronnen toe
    for source in WEBSEARCH_SOURCES:
        if source.sector == sector:
            sources.append(source)
    
    # Voeg Investing.com pagina's toe voor deze sector
    for source in INVESTING_PAGES:
        if source.sector == sector:
            sources.append(source)
    
    return sources


def get_websearch_queries_for_sector(sector: str) -> list[str]:
    """Get WebSearch zoekopdrachten voor een sector."""
    return SECTOR_SEARCH_QUERIES.get(sector, [])


def get_technical_source_url(ticker: str) -> str:
    """Genereer de URL voor de technische pagina van een ticker."""
    return TECHNICAL_SOURCES_TEMPLATE.format(ticker=ticker)


def get_all_sources() -> list[Source]:
    """Get alle beschikbare bronnen."""
    return RSS_SOURCES + WEBSEARCH_SOURCES + INVESTING_PAGES


def get_sources_for_stock_watchers(tickers: list[str]) -> list[Source]:
    """Get bronnen voor Stock Watchers voor specifieke tickers.
    
    Voor elke ticker:
    - Technische pagina (Investing.com)
    - WebSearch zoekopdracht voor de ticker
    """
    sources = []
    
    for ticker in tickers:
        # Technische pagina
        sources.append(Source(
            id=f"technical_{ticker}",
            name=f"Technical {ticker}",
            source_type=SourceType.INVESTING_PAGE,
            url_or_query=get_technical_source_url(ticker),
            tier=SourceTier.TIER_2,
            roles=[STOCK_WATCHERS.name],
            description=f"Technische analyse voor {ticker}",
        ))
        
        # WebSearch voor de ticker
        sources.append(Source(
            id=f"websearch_{ticker}",
            name=f"WebSearch {ticker}",
            source_type=SourceType.WEBSEARCH,
            url_or_query=f"{ticker} stock news",
            tier=SourceTier.TIER_2,
            roles=[STOCK_WATCHERS.name],
            description=f"WebSearch voor {ticker} nieuws",
            search_params={"time_range": "last_24_hours"},
        ))
    
    return sources
