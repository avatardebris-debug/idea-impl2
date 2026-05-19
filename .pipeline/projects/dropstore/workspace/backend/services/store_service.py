"""Store management service."""

import hashlib
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from backend.models.store import Store, StoreTemplate, TemplateSection, TemplateStyle
from backend.utils.database import async_session_factory


def _generate_store_id(platform_type: str, domain: str) -> str:
    """Generate a deterministic store ID."""
    raw = f"{platform_type}:{domain}"
    return f"store_{hashlib.sha256(raw.encode()).hexdigest()[:12]}"


async def create_store(
    platform_type: str,
    store_name: str,
    store_domain: str,
    api_key: str,
    api_secret: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> Store:
    """Create a new store connection."""
    store_id = _generate_store_id(platform_type, store_domain)

    store = Store(
        store_id=store_id,
        platform_type=platform_type,
        store_name=store_name,
        store_domain=store_domain,
        api_key=api_key,
        api_secret=api_secret or "",
        status="connected",
        settings=settings or {},
    )

    async with async_session_factory() as session:
        session.add(store)
        await session.commit()
        await session.refresh(store)
    return store


async def get_store(store_id: str) -> Optional[Store]:
    """Get a store by ID."""
    async with async_session_factory() as session:
        store = await session.get(Store, store_id)
        return store


async def list_stores() -> List[Store]:
    """List all stores."""
    async with async_session_factory() as session:
        stores = await session.execute(Store.__table__.select())
        return list(stores.scalars().all())


async def update_store_status(store_id: str, status: str) -> Optional[Store]:
    """Update store status."""
    async with async_session_factory() as session:
        store = await session.get(Store, store_id)
        if store:
            store.status = status
            await session.commit()
            await session.refresh(store)
        return store


async def delete_store(store_id: str) -> bool:
    """Delete a store connection."""
    async with async_session_factory() as session:
        store = await session.get(Store, store_id)
        if store:
            await session.delete(store)
            await session.commit()
            return True
        return False


async def create_template(
    name: str,
    platform_type: str,
    category: str = "general",
    description: str = "",
    preview_image_url: str = "",
    is_premium: bool = False,
) -> StoreTemplate:
    """Create a new store template."""
    template_id = f"tmpl_{uuid.uuid4().hex[:12]}"

    template = StoreTemplate(
        template_id=template_id,
        name=name,
        description=description,
        platform_type=platform_type,
        category=category,
        preview_image_url=preview_image_url,
        is_premium=is_premium,
        is_active=True,
    )

    async with async_session_factory() as session:
        session.add(template)
        await session.commit()
        await session.refresh(template)
    return template


async def get_template(template_id: str) -> Optional[StoreTemplate]:
    """Get a template by ID."""
    async with async_session_factory() as session:
        template = await session.get(StoreTemplate, template_id)
        return template


async def list_templates(platform_type: Optional[str] = None, category: Optional[str] = None) -> List[StoreTemplate]:
    """List templates with optional filters."""
    async with async_session_factory() as session:
        query = StoreTemplate.__table__.select().where(StoreTemplate.is_active == True)
        if platform_type:
            query = query.where(StoreTemplate.platform_type == platform_type)
        if category:
            query = query.where(StoreTemplate.category == category)
        templates = await session.execute(query)
        return list(templates.scalars().all())


async def get_template_sections(template_id: str) -> List[TemplateSection]:
    """Get all sections for a template."""
    async with async_session_factory() as session:
        sections = await session.execute(
            TemplateSection.__table__.select().where(
                TemplateSection.template_id == template_id
            ).order_by(TemplateSection.display_order)
        )
        return list(sections.scalars().all())


async def get_template_style(template_id: str) -> Optional[TemplateStyle]:
    """Get styling for a template."""
    async with async_session_factory() as session:
        style = await session.execute(
            TemplateStyle.__table__.select().where(
                TemplateStyle.template_id == template_id
            )
        )
        return style.scalar_one_or_none()
