"""
Browserbase Integration (Secondary Sponsor - Optional)

External evidence fetch for regulatory notices and public advisories.
"""

from .fetcher import BrowserbaseEvidenceFetcher, EvidenceRef

__all__ = [
    "BrowserbaseEvidenceFetcher",
    "EvidenceRef",
]
