"""Product catalog management service."""

import hashlib
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from backend.models.product import Product, ProductVariant, ProductImage, ProductTag
from backend.utils.database import async_session_factory


def _generate_product_id() -> str:
    """Generate a unique product ID."""
    return f"prod_{uuid.uuid4().hex[:12]}"


def _generate_variant_id() -> str:
    """Generate a unique variant ID."""
    return f"var_{uuid.uuid4().hex[:12]}"


def _generate_image_id() -> str:
    """Generate a unique image ID."""
    return f"img_{uuid.uuid4().hex[:12]}"


def _generate_tag_id() -> str:
    """Generate a unique tag ID."""
    return f"tag_{uuid.uuid4().hex[:12]}"


async def create_product(
    title: str,
    price: float,
    description: str = "",
    compare_at_price: Optional[float] = None,
    cost_price: Optional[float] = None,
    sku: Optional[str] = None,
    category: str = "general",
    tags: Optional[List[str]] = None,
    is_active: bool = True,
    source_supplier_id: Optional[str] = None,
    source_product_id: Optional[str] = None,
) -> Product:
    """Create a new product."""
    product_id = _generate_product_id()

    product = Product(
        product_id=product_id,
        title=title,
        description=description,
        price=price,
        compare_at_price=compare_at_price,
        cost_price=cost_price,
        sku=sku,
        category=category,
        tags=tags or [],
        is_active=is_active,
        source_supplier_id=source_supplier_id,
        source_product_id=source_product_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    async with async_session_factory() as session:
        session.add(product)
        await session.commit()
        await session.refresh(product)
    return product


async def get_product(product_id: str) -> Optional[Product]:
    """Get a product by ID."""
    async with async_session_factory() as session:
        product = await session.get(Product, product_id)
        return product


async def list_products(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    tag: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Product]:
    """List products with optional filters."""
    async with async_session_factory() as session:
        query = Product.__table__.select()
        if category:
            query = query.where(Product.category == category)
        if is_active is not None:
            query = query.where(Product.is_active == is_active)
        if min_price is not None:
            query = query.where(Product.price >= min_price)
        if max_price is not None:
            query = query.where(Product.price <= max_price)
        if tag:
            query = query.where(Product.tags.contains([tag]))
        query = query.order_by(Product.created_at.desc()).limit(limit).offset(offset)
        products = await session.execute(query)
        return list(products.scalars().all())


async def update_product(product_id: str, **kwargs) -> Optional[Product]:
    """Update product information."""
    async with async_session_factory() as session:
        product = await session.get(Product, product_id)
        if product:
            for key, value in kwargs.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            product.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(product)
        return product


async def create_variant(
    product_id: str,
    title: str,
    price: float,
    compare_at_price: Optional[float] = None,
    sku: Optional[str] = None,
    inventory_quantity: int = 0,
    weight: Optional[float] = None,
    options: Optional[Dict[str, str]] = None,
    is_active: bool = True,
) -> ProductVariant:
    """Create a new product variant."""
    variant_id = _generate_variant_id()

    variant = ProductVariant(
        variant_id=variant_id,
        product_id=product_id,
        title=title,
        price=price,
        compare_at_price=compare_at_price,
        sku=sku,
        inventory_quantity=inventory_quantity,
        weight=weight,
        options=options or {},
        is_active=is_active,
    )

    async with async_session_factory() as session:
        session.add(variant)
        await session.commit()
        await session.refresh(variant)
    return variant


async def get_variant(variant_id: str) -> Optional[ProductVariant]:
    """Get a variant by ID."""
    async with async_session_factory() as session:
        variant = await session.get(ProductVariant, variant_id)
        return variant


async def list_variants(product_id: str) -> List[ProductVariant]:
    """List all variants for a product."""
    async with async_session_factory() as session:
        variants = await session.execute(
            ProductVariant.__table__.select().where(
                ProductVariant.product_id == product_id
            )
        )
        return list(variants.scalars().all())


async def update_variant(variant_id: str, **kwargs) -> Optional[ProductVariant]:
    """Update variant information."""
    async with async_session_factory() as session:
        variant = await session.get(ProductVariant, variant_id)
        if variant:
            for key, value in kwargs.items():
                if hasattr(variant, key):
                    setattr(variant, key, value)
            await session.commit()
            await session.refresh(variant)
        return variant


async def create_product_image(
    product_id: str,
    url: str,
    alt_text: str = "",
    position: int = 0,
    is_primary: bool = False,
) -> ProductImage:
    """Create a new product image."""
    image_id = _generate_image_id()

    image = ProductImage(
        image_id=image_id,
        product_id=product_id,
        url=url,
        alt_text=alt_text,
        position=position,
        is_primary=is_primary,
    )

    async with async_session_factory() as session:
        session.add(image)
        await session.commit()
        await session.refresh(image)
    return image


async def get_product_images(product_id: str) -> List[ProductImage]:
    """Get all images for a product."""
    async with async_session_factory() as session:
        images = await session.execute(
            ProductImage.__table__.select().where(
                ProductImage.product_id == product_id
            ).order_by(ProductImage.position)
        )
        return list(images.scalars().all())


async def create_product_tag(
    product_id: str,
    name: str,
    color: str = "",
) -> ProductTag:
    """Create a new product tag."""
    tag_id = _generate_tag_id()

    tag = ProductTag(
        tag_id=tag_id,
        product_id=product_id,
        name=name,
        color=color,
    )

    async with async_session_factory() as session:
        session.add(tag)
        await session.commit()
        await session.refresh(tag)
    return tag


async def get_product_tags(product_id: str) -> List[ProductTag]:
    """Get all tags for a product."""
    async with async_session_factory() as session:
        tags = await session.execute(
            ProductTag.__table__.select().where(
                ProductTag.product_id == product_id
            )
        )
        return list(tags.scalars().all())


async def get_product_stats(product_id: str) -> Dict[str, Any]:
    """Get statistics for a product."""
    async with async_session_factory() as session:
        product = await session.get(Product, product_id)
        if not product:
            return {}

        variants = await session.execute(
            ProductVariant.__table__.select().where(
                ProductVariant.product_id == product_id
            )
        )
        variant_list = list(variants.scalars().all())

        images = await session.execute(
            ProductImage.__table__.select().where(
                ProductImage.product_id == product_id
            )
        )
        image_list = list(images.scalars().all())

        return {
            "total_variants": len(variant_list),
            "total_inventory": sum(v.inventory_quantity for v in variant_list),
            "total_images": len(image_list),
            "has_primary_image": any(img.is_primary for img in image_list),
        }
