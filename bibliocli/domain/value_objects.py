from dataclasses import dataclass
import re

@dataclass(frozen=True)
class BookSource:
    """
    Value Object representing the origin of a book.
    Ensures the source is a known, valid provider.
    """
    name: str

    def __post_init__(self):
        valid_sources = ["GUTENBERG", "WIKISOURCE", "OPENLIBRARY", "ALL_SOURCES"]
        if self.name.upper() not in valid_sources:
            raise ValueError(f"Invalid source: {self.name}. Must be one of {valid_sources}")

    def __str__(self):
        return self.name.upper()

@dataclass(frozen=True)
class BookLink:
    """
    Value Object representing a URL for a book.
    Ensures the link is a valid web address.
    """
    url: str

    def __post_init__(self):
        # Basic URL validation regex
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
        if not url_pattern.match(self.url):
            raise ValueError(f"Invalid book link: {self.url}")

    def __str__(self):
        return self.url
