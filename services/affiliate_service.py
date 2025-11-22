from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def convert_to_affiliate(url: str, affiliate_id: str) -> str:
    """Append or replace the affiliate tag in a given Amazon URL."""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["tag"] = [affiliate_id]
    new_query = urlencode(query, doseq=True)
    new_url = parsed._replace(query=new_query)
    return urlunparse(new_url)
