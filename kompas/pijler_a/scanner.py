"""Pijler A  Scanner logica voor het ophalen en parsen van bronnen.

Deze module bevat de core logica voor:
1. Het ophalen van content van verschillende bronnen (RSS, WebSearch, Investing.com)
2. Het parsen van de content naar gestructureerde data
3. Het extraheren van relevante signalen

De scanner werkt met de bronnen gedefinieerd in sources.py en produceert
signalen in het standaard Poort 1-formaat (kompas.core.signal.Signal).

Belangrijke principes:
- Elke bron wordt onafhankelijk gescand
- Signalen worden gevalideerd tegen het Poort 1-schema
- Conflicten tussen bronnen worden zichtbaar gemaakt
- De scanner levert RAUWE signalen (geen synthese, geen consensus)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable
from xml.etree import ElementTree as ET

from kompas.core.signal import Signal, SIGNAL_CONFIDENCE_LEVELS, validate_signal
from kompas.pijler_a.sources import (
    Source,
    SourceType,
    SourceTier,
    get_sources_for_role,
    get_sources_for_sector,
    get_websearch_queries_for_sector,
)


@runtime_checkable
class Fetchable(Protocol):
    """Protocol voor het ophalen van content van een bron.
    
    Dit is een abstractie die het mogelijk maakt om verschillende
    fetch-mechanismen te gebruiken (WebFetch, WebSearch, etc.)
    """
    
    async def fetch(self, source: Source) -> str:
        """Haalt de raw content op van een bron."""
        ...


@dataclass
class ParsedItem:
    """Een geparst item van een bron (RSS feed, web pagina, etc.)."""
    
    title: str
    link: str
    description: str | None = None
    published: str | None = None
    source_name: str = ""
    source_type: SourceType = SourceType.RSS
    
    # Voor technische analyse
    technical_indicators: dict[str, str] = field(default_factory=dict)
    
    # Metadata
    raw_content: str = ""


@dataclass
class ScanResult:
    """Resultaat van het scannen van een bron."""
    
    source: Source
    items: list[ParsedItem]
    success: bool
    error: str | None = None
    scanned_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class SignalCandidate:
    """Een kandidaat-signaal dat nog gevalideerd moet worden."""
    
    role: str
    subject: str
    text: str
    source: str
    source_tier: str
    magnitude: str
    timeframe_horizon: str
    data_confidence: str
    signal_confidence: str
    observed_at: str
    chart_timeframe: str | None = None
    related_positions: list[str] = field(default_factory=list)
    related_watchlist: list[str] = field(default_factory=list)
    
    # Metadata voor tracing
    source_id: str = ""
    raw_item: ParsedItem | None = None
    
    def to_signal(self) -> Signal:
        """Converteer naar een Signal dataclass."""
        return Signal(
            role=self.role,
            subject=self.subject,
            text=self.text,
            source=self.source,
            source_tier=self.source_tier,
            magnitude=self.magnitude,
            timeframe_horizon=self.timeframe_horizon,
            data_confidence=self.data_confidence,
            signal_confidence=self.signal_confidence,
            observed_at=self.observed_at,
            chart_timeframe=self.chart_timeframe,
            related_positions=self.related_positions,
            related_watchlist=self.related_watchlist,
        )
    
    def validate(self, is_technical: bool = False) -> tuple[bool, list[str]]:
        """Valideer het kandidaat-signaal."""
        signal = self.to_signal()
        result = validate_signal(signal, is_technical=is_technical)
        return result.ok, result.errors


class RSSParser:
    """Parser voor RSS-feeds."""
    
    @staticmethod
    def parse(rss_content: str, source: Source) -> list[ParsedItem]:
        """Parseert een RSS-feed naar ParsedItem objecten."""
        items = []
        
        try:
            root = ET.fromstring(rss_content)
            
            # Probeer item elementen te vinden (RSS 2.0)
            for item_elem in root.findall('.//item'):
                try:
                    title = item_elem.findtext('title', '')
                    link = item_elem.findtext('link', '')
                    description = item_elem.findtext('description', '')
                    published = item_elem.findtext('pubDate', '')
                    
                    if title and link:
                        items.append(ParsedItem(
                            title=title.strip(),
                            link=link.strip(),
                            description=description.strip() if description else None,
                            published=published.strip() if published else None,
                            source_name=source.name,
                            source_type=source.source_type,
                            raw_content=rss_content[:500] + "..." if len(rss_content) > 500 else rss_content,
                        ))
                except Exception:
                    continue
                    
        except ET.ParseError:
            # Probeer als plain text te parsen (sommige feeds zijn geen XML)
            pass
        
        return items


class WebPageParser:
    """Parser voor webpagina's (Investing.com, etc.)."""
    
    @staticmethod
    def parse(html_content: str, source: Source) -> list[ParsedItem]:
        """Parseert een HTML-pagina naar ParsedItem objecten.
        
        Dit is een eenvoudige parser die op zoek gaat naar:
        - Nieuwsitems (titels + links)
        - Technische indicatoren (voor technische pagina's)
        """
        items = []
        
        # Voor Investing.com technische pagina's
        if "technical" in source.url_or_query.lower():
            items.append(ParsedItem(
                title=f"Technische Analyse: {source.url_or_query}",
                link=source.url_or_query,
                description=html_content[:1000] + "..." if len(html_content) > 1000 else html_content,
                source_name=source.name,
                source_type=source.source_type,
                technical_indicators=WebPageParser._extract_technical_indicators(html_content),
                raw_content=html_content[:2000] + "..." if len(html_content) > 2000 else html_content,
            ))
        else:
            # Voor nieuwspagina's: extracteer titels en links
            items.extend(WebPageParser._extract_news_items(html_content, source))
        
        return items
    
    @staticmethod
    def _extract_technical_indicators(html: str) -> dict[str, str]:
        """Extracteert technische indicatoren uit HTML content."""
        indicators = {}
        
        # Zoek naar RSI, MACD, Moving Averages, etc.
        patterns = {
            'RSI': r'RSI\(?\d+\)?[\s:]*([\d,.-]+)',
            'MACD': r'MACD[\s:]*([\d,.-]+)',
            'MA_50': r'50[-\s]?day[\s-]?MA[\s:]*([\d,.-]+)',
            'MA_200': r'200[-\s]?day[\s-]?MA[\s:]*([\d,.-]+)',
            'Price': r'(?:Current|Last)[\s-]?Price[\s:]*([\d,.-]+)',
        }
        
        for name, pattern in patterns.items():
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                indicators[name] = match.group(1).strip()
        
        return indicators
    
    @staticmethod
    def _extract_news_items(html: str, source: Source) -> list[ParsedItem]:
        """Extracteert nieuwsitems uit HTML content."""
        items = []
        
        # Zoek naar <a> tags met titels
        # Dit is een eenvoudige regex-based parser
        # Voor betere resultaten zou je BeautifulSoup of lxml kunnen gebruiken
        
        # Patroon voor links met titels
        link_pattern = r'<a\s+[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        
        for match in re.finditer(link_pattern, html, re.IGNORECASE):
            href = match.group(1)
            title = match.group(2).strip()
            
            # Filter op relevante links
            if any(keyword in title.lower() or keyword in href.lower() 
                   for keyword in ['news', 'update', 'announces', 'reports', 'stock']):
                
                # Maak absolute URL als nodig
                if href.startswith('/'):
                    if source.url_or_query.startswith('https://'):
                        base = source.url_or_query.split('://')[1].split('/')[0]
                        href = f"https://{base}{href}"
                
                items.append(ParsedItem(
                    title=title,
                    link=href,
                    source_name=source.name,
                    source_type=source.source_type,
                    raw_content="",
                ))
        
        return items


class WebSearchParser:
    """Parser voor WebSearch resultaten."""
    
    @staticmethod
    def parse(search_results: str, source: Source) -> list[ParsedItem]:
        """Parseert WebSearch resultaten naar ParsedItem objecten."""
        items = []
        
        # WebSearch resultaten zijn typisch JSON of gestructureerde text
        # Voor deze implementatie gaan we uit van een eenvoudig text formaat
        
        # Probeer JSON te parsen
        try:
            import json
            results = json.loads(search_results)
            
            if isinstance(results, list):
                for result in results:
                    title = result.get('title', result.get('headline', ''))
                    link = result.get('url', result.get('link', ''))
                    description = result.get('description', result.get('snippet', None))
                    
                    if title and link:
                        items.append(ParsedItem(
                            title=title,
                            link=link,
                            description=description,
                            source_name=source.name,
                            source_type=source.source_type,
                        ))
        except (json.JSONDecodeError, AttributeError):
            # Parse als plain text
            # Zoek naar URLs en bijbehorende titels
            url_pattern = r'(https?://[^\s]+)'
            
            for match in re.finditer(url_pattern, search_results):
                url = match.group(1)
                # Zoek een titel in de buurt
                start = max(0, match.start() - 100)
                end = min(len(search_results), match.end() + 100)
                context = search_results[start:end]
                
                # Extracteer een titel
                title_match = re.search(r'[A-Z][^\n.!?]*[.!?]', context)
                title = title_match.group(0) if title_match else url
                
                items.append(ParsedItem(
                    title=title.strip(),
                    link=url,
                    source_name=source.name,
                    source_type=source.source_type,
                ))
        
        return items


class SignalExtractor:
    """Extracteert signalen uit ParsedItem objecten.
    
    Deze klasse is verantwoordelijk voor het converteren van rauwe
    ParsedItem data naar SignalCandidate objecten.
    """
    
    # Ticker mapping voor known names
    TICKER_ALIASES: dict[str, str] = {
        'ASML': 'ASML',
        'NVIDIA': 'NVDA',
        'AMD': 'AMD',
        'TSMC': 'TSM',
        'CAMECO': 'CCJ',
        'RHEINMETALL': 'RHM',
        'LOCKHEED MARTIN': 'LMT',
        'THALES': 'THA',
        'SAAB': 'SAAB-B',
        'WHEATON PRECIOUS METALS': 'WPM',
    }
    
    @classmethod
    def extract_from_item(cls, item: ParsedItem, role: str, sector: str | None = None) -> SignalCandidate | None:
        """Extracteert een signaal uit een ParsedItem."""
        
        # Bepaal het onderwerp
        subject = cls._extract_subject(item.title, item.description)
        
        # Bepaal de magnitude
        magnitude = cls._extract_magnitude(item.title, item.description)
        
        # Bepaal de tijdshorizon
        timeframe_horizon = cls._extract_timeframe(item.title, item.description)
        
        # Bepaal de databetrouwbaarheid
        data_confidence = cls._extract_data_confidence(item, role)
        
        # Bepaal de signaalbetrouwbaarheid
        signal_confidence = cls._determine_signal_confidence(role, item.source_type)
        
        # Bepaal of het technisch is
        is_technical = role == "Technical stock watchers" or "technical" in item.source_name.lower()
        
        # Chart timeframe (alleen voor technische signalen)
        chart_timeframe = None
        if is_technical and item.technical_indicators:
            # Zoek naar timeframe in de indicatoren
            for key, value in item.technical_indicators.items():
                if 'MA' in key or 'RSI' in key or 'MACD' in key:
                    chart_timeframe = "daily"  # Standaard, kan worden overschreven
                    break
        
        # Related positions en watchlist
        related_positions, related_watchlist = cls._extract_related_tickers(
            item.title + " " + (item.description or ""),
            subject
        )
        
        # Bouw het kandidaat-signaal
        candidate = SignalCandidate(
            role=role,
            subject=subject,
            text=cls._build_signal_text(item, subject),
            source=item.link if item.link else item.source_name,
            source_tier=cls._get_source_tier(item.source_type),
            magnitude=magnitude,
            timeframe_horizon=timeframe_horizon,
            data_confidence=data_confidence,
            signal_confidence=signal_confidence,
            observed_at=item.published or datetime.now(timezone.utc).isoformat(),
            chart_timeframe=chart_timeframe,
            related_positions=related_positions,
            related_watchlist=related_watchlist,
            source_id=item.source_name,
            raw_item=item,
        )
        
        return candidate
    
    @classmethod
    def _extract_subject(cls, title: str, description: str | None) -> str:
        """Extracteert het onderwerp uit de titel en beschrijving."""
        # Zoek naar bekende tickers
        text = f"{title} {description or ''}"
        
        for alias, ticker in cls.TICKER_ALIASES.items():
            if alias in text.upper() or ticker in text.upper():
                return alias
        
        # Zoek naar sector namen
        sector_keywords = [
            "Halfgeleiders", "Semiconductor", "Chip",
            "Defensie", "Defense", "Military",
            "Uranium", "Nuclear", "Nucleair",
            "Datacenter", "AI", "Infrastructure",
            "Energie", "Energy", "Oil", "Gas",
            "Gezondheidszorg", "Healthcare", "Pharma",
            "Consumentengoederen", "Consumer", "Retail",
            "Edelmetalen", "Gold", "Silver", "Precious Metals",
        ]
        
        for keyword in sector_keywords:
            if keyword.lower() in text.lower():
                return keyword
        
        # Gebruik de titel als onderwerp
        return title[:100]  # Limiteer lengte
    
    @classmethod
    def _extract_magnitude(cls, title: str, description: str | None) -> str:
        """Extracteert de magnitude uit de titel en beschrijving."""
        text = f"{title} {description or ''}"
        
        # Zoek naar percentages
        percent_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*%', text)
        if percent_match:
            return f"{percent_match.group(1)}%"
        
        # Zoek naar bedragen
        amount_match = re.search(r'(?:\$|\u20ac|€)\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', text)
        if amount_match:
            return f"${amount_match.group(1)}"
        
        # Zoek naar getallen
        number_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', text)
        if number_match:
            return number_match.group(1)
        
        return "onbekend"
    
    @classmethod
    def _extract_timeframe(cls, title: str, description: str | None) -> str:
        """Extracteert de tijdshorizon uit de titel en beschrijving."""
        text = f"{title} {description or ''}".lower()
        
        timeframe_keywords = {
            "kort termijn": ["hour", "day", "today", "short term", "immediate"],
            "middellange termijn": ["week", "weeks", "month", "months", "quarter"],
            "lange termijn": ["year", "years", "long term", "structureel", "structural"],
            "direct": ["now", "immediate", "breaking", "urgent"],
        }
        
        for timeframe, keywords in timeframe_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return timeframe
        
        return "onbekend"
    
    @classmethod
    def _extract_data_confidence(cls, item: ParsedItem, role: str) -> str:
        """Bepaalt de databetrouwbaarheid."""
        # Tier 1 bronnen hebben hoge betrouwbaarheid
        if item.source_type == SourceType.RSS and "tier 1" in item.source_name.lower():
            return "hoog"
        
        # Technische signalen zijn deterministisch
        if "technical" in role.lower():
            return "hoog"
        
        return "voorlopig"
    
    @classmethod
    def _determine_signal_confidence(cls, role: str, source_type: SourceType) -> str:
        """Bepaalt de signaalbetrouwbaarheid."""
        # Technische signalen hebben bekende valse-signalen ratio's
        if role == "Technical stock watchers":
            return "voorlopig"
        
        # Tier 1 bronnen
        if source_type == SourceType.RSS:
            return "hoog"
        
        return "voorlopig"
    
    @classmethod
    def _get_source_tier(cls, source_type: SourceType) -> str:
        """Bepaalt de source tier."""
        if source_type == SourceType.RSS:
            return "tier 1" if "tier 1" in str(source_type) else "tier 2"
        return "tier 2"
    
    @classmethod
    def _extract_related_tickers(cls, text: str, subject: str) -> tuple[list[str], list[str]]:
        """Extracteert gerelateerde tickers uit de text."""
        positions = []
        watchlist = []
        
        text_upper = text.upper()
        
        # Zoek naar alle bekende tickers
        for alias, ticker in cls.TICKER_ALIASES.items():
            if alias in text_upper or ticker in text_upper:
                # Voeg toe aan positions of watchlist
                # Voor nu: voeg toe aan beide (kan later worden gefilterd)
                if ticker not in positions:
                    positions.append(ticker)
        
        return positions, watchlist
    
    @classmethod
    def _build_signal_text(cls, item: ParsedItem, subject: str) -> str:
        """Bouwt de signaal tekst."""
        parts = [f"Onderwerp: {subject}"]
        
        if item.title:
            parts.append(f"Titel: {item.title}")
        
        if item.description:
            parts.append(f"Beschrijving: {item.description}")
        
        if item.link:
            parts.append(f"Bron: {item.link}")
        
        if item.technical_indicators:
            parts.append("Technische indicatoren:")
            for name, value in item.technical_indicators.items():
                parts.append(f"  {name}: {value}")
        
        return "\n".join(parts)


class Scanner:
    """Hoofdscanner voor Pijler A.
    
    Deze klasse coördineert het scannen van alle bronnen voor alle rollen
    en levert een lijst van SignalCandidate objecten.
    """
    
    def __init__(self):
        self.parser_map = {
            SourceType.RSS: RSSParser,
            SourceType.WEBSEARCH: WebSearchParser,
            SourceType.INVESTING_PAGE: WebPageParser,
        }
    
    def scan_source(self, source: Source) -> ScanResult:
        """Scant een enkele bron en retourneert het resultaat."""
        # In een echte implementatie zou hier de fetch gebeuren
        # Voor nu: simuleer een succesvolle scan
        
        # Bepaal welke parser te gebruiken
        parser_class = self.parser_map.get(source.source_type, RSSParser)
        
        # Simuleer content (in productie: echte fetch)
        if source.source_type == SourceType.RSS:
            raw_content = f"<rss><channel><item><title>Test Item from {source.name}</title><link>{source.url_or_query}</link></item></channel></rss>"
        elif source.source_type == SourceType.WEBSEARCH:
            raw_content = f'["{{title: "Test Search from {source.name}", url: "{source.url_or_query}"}}]'
        else:
            raw_content = f"<html>Test content from {source.name}</html>"
        
        # Parse de content
        try:
            items = parser_class.parse(raw_content, source)
            return ScanResult(
                source=source,
                items=items,
                success=True,
            )
        except Exception as e:
            return ScanResult(
                source=source,
                items=[],
                success=False,
                error=str(e),
            )
    
    def scan_role(self, role_name: str) -> list[SignalCandidate]:
        """Scant alle bronnen voor een specifieke rol."""
        sources = get_sources_for_role(role_name)
        candidates = []
        
        for source in sources:
            result = self.scan_source(source)
            if result.success:
                for item in result.items:
                    candidate = SignalExtractor.extract_from_item(item, role_name, source.sector)
                    if candidate:
                        candidates.append(candidate)
        
        return candidates
    
    def scan_sector_specialist(self, sector: str) -> list[SignalCandidate]:
        """Scant alle bronnen voor een sector specialist."""
        sources = get_sources_for_sector(sector)
        candidates = []
        
        role_name = f"Sector specialist  {sector}"
        
        for source in sources:
            result = self.scan_source(source)
            if result.success:
                for item in result.items:
                    candidate = SignalExtractor.extract_from_item(item, role_name, sector)
                    if candidate:
                        candidates.append(candidate)
        
        return candidates
    
    def scan_all_roles(self) -> dict[str, list[SignalCandidate]]:
        """Scant alle rollen en retourneert signalen per rol."""
        from kompas.pijler_a.roles import FIXED_ROLES, SECTOR_SPECIALISTS
        
        results = {}
        
        # Scan vaste rollen
        for role in FIXED_ROLES:
            candidates = self.scan_role(role.name)
            results[role.name] = candidates
        
        # Scan sector specialisten
        for specialist in SECTOR_SPECIALISTS:
            candidates = self.scan_sector_specialist(specialist.sector)
            results[specialist.full_name] = candidates
        
        return results
    
    def validate_candidates(self, candidates: list[SignalCandidate]) -> tuple[list[Signal], list[SignalCandidate]]:
        """Valideert een lijst van kandidaat-signalen.
        
        Returns: (valid_signals, invalid_candidates)
        """
        valid_signals = []
        invalid_candidates = []
        
        for candidate in candidates:
            is_technical = candidate.role == "Technical stock watchers"
            is_valid, errors = candidate.validate(is_technical=is_technical)
            
            if is_valid:
                valid_signals.append(candidate.to_signal())
            else:
                invalid_candidates.append(candidate)
        
        return valid_signals, invalid_candidates
