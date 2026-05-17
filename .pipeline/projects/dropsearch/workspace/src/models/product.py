"""Pydantic model for a scraped product."""

from pydantic import BaseModel, Field


class Product(BaseModel):
    """Represents a single product extracted from a competitor store."""

    name: str = Field(description="Product name / title")
    price: float = Field(description="Product price in store currency")
    description: str = Field(default="", description="Product description snippet")
    image_url: str = Field(default="", description="URL of the product image")
    url: str = Field(default="", description="URL of the product detail page")
