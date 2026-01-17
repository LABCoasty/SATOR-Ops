"""
Browserbase Evidence Fetcher

Fetches external evidence from web sources.
"""

import hashlib
import uuid
from datetime import datetime
from dataclasses import dataclass

from config import config


@dataclass
class EvidenceRef:
    """Reference to external evidence"""
    ref_id: str
    source: str
    url: str
    content_hash: str
    fetched_at: datetime
    incident_id: str | None = None
    title: str | None = None
    snippet: str | None = None


class BrowserbaseEvidenceFetcher:
    """
    Fetches external evidence from web sources using Browserbase.
    
    Used for one-time fetches of regulatory notices, public advisories,
    or other external context relevant to incidents.
    
    This is an optional integration that no-ops when disabled.
    """
    
    def __init__(self, enabled: bool | None = None):
        self._enabled = enabled if enabled is not None else config.enable_browserbase
        self._api_key = config.browserbase_api_key
        self._cache: dict[str, EvidenceRef] = {}
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    async def fetch_evidence(
        self, 
        url: str, 
        incident_id: str | None = None
    ) -> EvidenceRef | None:
        """
        Fetch external page content and create an evidence reference.
        
        Args:
            url: URL to fetch
            incident_id: Optional incident to associate with
            
        Returns:
            EvidenceRef with content hash, or None if disabled/failed
        """
        if not self._enabled:
            return None
        
        # Check cache
        if url in self._cache:
            return self._cache[url]
        
        try:
            content = await self._fetch_page(url)
            
            if content is None:
                return None
            
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            ref = EvidenceRef(
                ref_id=str(uuid.uuid4()),
                source="browserbase",
                url=url,
                content_hash=content_hash,
                fetched_at=datetime.utcnow(),
                incident_id=incident_id,
                title=self._extract_title(content),
                snippet=content[:500] if content else None,
            )
            
            self._cache[url] = ref
            return ref
            
        except Exception as e:
            print(f"Browserbase fetch failed: {e}")
            return None
    
    async def _fetch_page(self, url: str) -> str | None:
        """
        Fetch page content using Browserbase.
        
        In production, this would use the Browserbase API for
        JavaScript rendering and anti-bot handling.
        """
        if not self._api_key:
            # Simulated response for testing
            return f"<html><title>Evidence from {url}</title><body>Regulatory notice content...</body></html>"
        
        # In production:
        # async with browserbase.Session(api_key=self._api_key) as session:
        #     page = await session.get(url)
        #     return await page.content()
        
        return None
    
    def _extract_title(self, html: str) -> str | None:
        """Extract title from HTML content"""
        import re
        match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
        return match.group(1) if match else None
    
    async def fetch_regulatory_notice(
        self, 
        notice_id: str,
        agency: str = "EPA"
    ) -> EvidenceRef | None:
        """
        Fetch a regulatory notice by ID.
        
        Convenience method for common regulatory sources.
        """
        # Map agencies to URL patterns
        url_patterns = {
            "EPA": f"https://www.epa.gov/notices/{notice_id}",
            "OSHA": f"https://www.osha.gov/notices/{notice_id}",
            "DOE": f"https://www.energy.gov/notices/{notice_id}",
        }
        
        url = url_patterns.get(agency, f"https://regulations.gov/{notice_id}")
        return await self.fetch_evidence(url, incident_id=notice_id)
    
    def get_cached_evidence(self) -> list[EvidenceRef]:
        """Get all cached evidence references"""
        return list(self._cache.values())
    
    def clear_cache(self) -> None:
        """Clear the evidence cache"""
        self._cache.clear()


# Global fetcher instance
_fetcher: BrowserbaseEvidenceFetcher | None = None


def get_fetcher() -> BrowserbaseEvidenceFetcher:
    """Get or create the global fetcher"""
    global _fetcher
    if _fetcher is None:
        _fetcher = BrowserbaseEvidenceFetcher()
    return _fetcher
