import re
import unicodedata


def remove_urls(text: str) -> str:
    """
    Removes HTTP/HTTPS URLs from the input text.
    """
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    return url_pattern.sub('', text)


def normalize_whitespace(text: str) -> str:
    """
    Replaces multiple spaces, newlines, and tabs with a single space.
    """
    return re.sub(r'\s+', ' ', text).strip()


def normalize_unicode(text: str) -> str:
    """
    Normalizes unicode characters to NFKD representation.
    """
    return unicodedata.normalize('NFKD', text)


def clean_text(text: str, to_lower: bool = True) -> str:
    """
    Full text cleaning pipeline: URL removal, unicode normalization,
    whitespace cleaning, and optional lowercasing.
    """
    if not text:
        return ""
    
    cleaned = remove_urls(text)
    cleaned = normalize_unicode(cleaned)
    cleaned = normalize_whitespace(cleaned)
    
    if to_lower:
        cleaned = cleaned.lower()
        
    return cleaned
