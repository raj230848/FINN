"""Bounded public-document access. Never allow user URLs to reach local services."""
import ipaddress
import socket
import time
from urllib.parse import urljoin, urlparse
import httpx

HEADERS = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US,en;q=0.9'}
ARCHIVES = {'nsearchives.nseindia.com', 'archives.nseindia.com', 'www.bseindia.com', 'www.nseindia.com', 'api.bseindia.com'}

class SourceError(ValueError):
    pass

def domain(url: str) -> str:
    return (urlparse(url).hostname or '').lower().removeprefix('www.')

def validate_url(url: str, allowed_domains: set[str]) -> None:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or '').lower()
        port = parsed.port
    except ValueError:
        raise SourceError('Malformed primary-document URL.') from None
    if parsed.scheme != 'https' or parsed.username or parsed.password or port not in (None, 443):
        raise SourceError('Only public HTTPS primary-document URLs on port 443 are accepted.')
    if not any(host == d or host.endswith('.' + d) for d in allowed_domains):
        raise SourceError('Use a company-issued document on its verified website or an NSE/BSE archive.')
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise SourceError('The source hostname could not be resolved.') from exc
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise SourceError('Private, reserved and local network addresses are not accepted.')

def fetch_public(url: str, allowed_domains: set[str], max_bytes: int = 20_000_000,timeout_seconds: float=18) -> tuple[bytes, str]:
    started=time.monotonic()
    with httpx.Client(headers=HEADERS, timeout=httpx.Timeout(timeout_seconds, connect=min(8,timeout_seconds)), follow_redirects=False) as client:
        for _ in range(4):
            validate_url(url, allowed_domains)
            if time.monotonic()-started>timeout_seconds:raise SourceError('Source download exceeded its time budget. Please retry the primary document.')
            try:
                with client.stream('GET', url) as response:
                    if response.is_redirect:
                        target=response.headers.get('location')
                        if not target:raise SourceError('Source redirect did not identify a document.')
                        url = urljoin(url,target)
                        continue
                    if response.status_code != 200:
                        raise SourceError(f'Source returned HTTP {response.status_code}. It may restrict automated access; no fallback data was substituted.')
                    content = bytearray()
                    advertised=response.headers.get('content-length','')
                    if advertised.isdigit() and int(advertised)>max_bytes:
                        raise SourceError(f'Source exceeds the configured {max_bytes:,}-byte download limit.')
                    for part in response.iter_bytes():
                        if time.monotonic()-started>timeout_seconds:raise SourceError('Source download exceeded its time budget. Please retry the primary document.')
                        content.extend(part)
                        if len(content) > max_bytes:
                            raise SourceError(f'Source exceeds the configured {max_bytes:,}-byte download limit.')
                    return bytes(content), url
            except httpx.HTTPError as exc:
                raise SourceError(f'Source unavailable ({type(exc).__name__}). Retry or use a primary document from another permitted issuer URL.') from exc
    raise SourceError('Too many document redirects.')
