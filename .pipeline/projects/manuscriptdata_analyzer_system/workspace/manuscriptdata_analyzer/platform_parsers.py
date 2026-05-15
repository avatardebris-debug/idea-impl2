from typing import List, Dict, Any, Type

class PlatformParser:
    """Base class for platform-specific CSV parsers."""
    PLATFORM_NAME = "Unknown"
    
    @classmethod
    def can_parse(cls, headers: List[str]) -> bool:
        """Return True if this parser can handle the given headers."""
        raise NotImplementedError
        
    @classmethod
    def parse_row(cls, row: Dict[str, str]) -> Dict[str, Any]:
        """Normalize a row into the canonical schema."""
        raise NotImplementedError

class KDPParser(PlatformParser):
    PLATFORM_NAME = "Amazon KDP"
    
    @classmethod
    def can_parse(cls, headers: List[str]) -> bool:
        norm = [h.strip().lower() for h in headers]
        return "asin" in norm and "kenp read" in norm or "royalties" in norm
        
    @classmethod
    def parse_row(cls, row: Dict[str, str]) -> Dict[str, Any]:
        norm = {k.strip().lower(): v for k, v in row.items()}
        return {
            "date": norm.get("date", ""),
            "book_title": norm.get("title", ""),
            "units_sold": int(float(norm.get("units sold", 0) or 0)),
            "revenue": float(norm.get("royalties", 0) or 0),
            "platform": cls.PLATFORM_NAME
        }

class KoboParser(PlatformParser):
    PLATFORM_NAME = "Kobo"
    
    @classmethod
    def can_parse(cls, headers: List[str]) -> bool:
        norm = [h.strip().lower() for h in headers]
        return "kobo store" in norm or "kobo id" in norm
        
    @classmethod
    def parse_row(cls, row: Dict[str, str]) -> Dict[str, Any]:
        norm = {k.strip().lower(): v for k, v in row.items()}
        return {
            "date": norm.get("transaction date", ""),
            "book_title": norm.get("item name", ""),
            "units_sold": int(float(norm.get("qty", 0) or 0)),
            "revenue": float(norm.get("net earnings", 0) or 0),
            "platform": cls.PLATFORM_NAME
        }

class AppleBooksParser(PlatformParser):
    PLATFORM_NAME = "Apple Books"
    
    @classmethod
    def can_parse(cls, headers: List[str]) -> bool:
        norm = [h.strip().lower() for h in headers]
        return "apple identifier" in norm or "customer price" in norm
        
    @classmethod
    def parse_row(cls, row: Dict[str, str]) -> Dict[str, Any]:
        norm = {k.strip().lower(): v for k, v in row.items()}
        return {
            "date": norm.get("begin date", ""),
            "book_title": norm.get("title", ""),
            "units_sold": int(float(norm.get("quantity", 0) or 0)),
            "revenue": float(norm.get("extended partner share", 0) or 0),
            "platform": cls.PLATFORM_NAME
        }

class BarnesAndNobleParser(PlatformParser):
    PLATFORM_NAME = "Barnes & Noble Press"
    
    @classmethod
    def can_parse(cls, headers: List[str]) -> bool:
        norm = [h.strip().lower() for h in headers]
        return "ean" in norm and "bn.com" in norm or "nook" in norm
        
    @classmethod
    def parse_row(cls, row: Dict[str, str]) -> Dict[str, Any]:
        norm = {k.strip().lower(): v for k, v in row.items()}
        return {
            "date": norm.get("order date", ""),
            "book_title": norm.get("title", ""),
            "units_sold": int(float(norm.get("units", 0) or 0)),
            "revenue": float(norm.get("royalty", 0) or 0),
            "platform": cls.PLATFORM_NAME
        }

# For fallback/generic:
class GenericSalesParser(PlatformParser):
    PLATFORM_NAME = "Generic"
    
    @classmethod
    def can_parse(cls, headers: List[str]) -> bool:
        norm = [h.strip().lower() for h in headers]
        return "revenue" in norm and "units sold" in norm
        
    @classmethod
    def parse_row(cls, row: Dict[str, str]) -> Dict[str, Any]:
        norm = {k.strip().lower(): v for k, v in row.items()}
        return {
            "date": norm.get("date", ""),
            "book_title": norm.get("book title", norm.get("title", "")),
            "units_sold": int(float(norm.get("units sold", 0) or 0)),
            "revenue": float(norm.get("revenue", 0) or 0),
            "platform": norm.get("platform", cls.PLATFORM_NAME)
        }

PARSERS: List[Type[PlatformParser]] = [
    KDPParser, KoboParser, AppleBooksParser, BarnesAndNobleParser, GenericSalesParser
]

def detect_platform(headers: List[str]) -> Type[PlatformParser]:
    for p in PARSERS:
        if p.can_parse(headers):
            return p
    return GenericSalesParser
