from abc import ABC, abstractmethod
from typing import Optional
from app.models import Recipe

class BaseParser(ABC):
    """Base class for all recipe parsers"""
    
    @abstractmethod
    def parse(self, url: str, **kwargs) -> Optional[Recipe]:
        """Parse a recipe from the given URL"""
        pass
    
    @abstractmethod
    def can_parse(self, url: str) -> bool:
        """Check if this parser can handle the given URL"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Parser name for logging"""
        pass
