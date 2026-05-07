"""Table management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TableMetadata, TableField, FieldTypeId
from ..schemas import TableRequest, TableResponse

router = APIRouter(tags=["tables"])


@router.options("")
def options_tables():
    """Handle CORS preflight for tables endpoint."""
    from fastapi import Response
    return Response(
        status_code=200,
        headers={
            "access-control-allow-origin": "*",
            "access-control-allow-methods": "*",
            "access-control-allow-headers": "*",
        },
    )


@router.post("", status_code=201, response_model=TableResponse)
def create_table(table_request: TableRequest, db: Session = Depends(get_db)):
    """Create a new table."""
    # Check if table name already exists
    existing = db.query(TableMetadata).filter(
        TableMetadata.name == table_request.name
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Table name already exists")

    table = TableMetadata(
        name=table_request.name,
        description=table_request.description,
    )
    db.add(table)
    db.commit()
    db.refresh(table)

    # Add built-in fields
    builtin_fields = [
        TableField(table_id=table.id, name="title", field_type=FieldTypeId.TEXT, is_required=True),
        TableField(table_id=table.id, name="description", field_type=FieldTypeId.TEXT, is_required=False),
        TableField(table_id=table.id, name="status", field_type=FieldTypeId.SELECT, is_required=True, options=["draft", "published", "scheduled"]),
        TableField(table_id=table.id, name="tags", field_type=FieldTypeId.TAGS, is_required=False),
        TableField(table_id=table.id, name="publish_date", field_type=FieldTypeId.DATE, is_required=False),
        TableField(table_id=table.id, name="thumbnail_url", field_type=FieldTypeId.URL, is_required=False),
        TableField(table_id=table.id, name="youtube_video_id", field_type=FieldTypeId.TEXT, is_required=False),
        TableField(table_id=table.id, name="custom_fields", field_type=FieldTypeId.TEXT, is_required=False),
        TableField(table_id=table.id, name="created_at", field_type=FieldTypeId.DATE, is_required=False),
        TableField(table_id=table.id, name="updated_at", field_type=FieldTypeId.DATE, is_required=False),
    ]
    db.add_all(builtin_fields)
    db.commit()
    db.refresh(table)

    return TableResponse.model_validate(table)


@router.get("", response_model=dict)
def list_tables(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    db: Session = Depends(get_db),
):
    """List all tables with pagination."""
    query = db.query(TableMetadata)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (TableMetadata.name.ilike(search_term)) | (TableMetadata.description.ilike(search_term))
        )

    total = query.count()

    items = (
        query.order_by(TableMetadata.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [TableResponse.model_validate(t) for t in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{table_id}", response_model=TableResponse)
def get_table(table_id: str, db: Session = Depends(get_db)):
    """Get a specific table by ID."""
    table = db.query(TableMetadata).filter(TableMetadata.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    return TableResponse.model_validate(table)


@router.put("/{table_id}", response_model=TableResponse)
def update_table(table_id: str, table_request: TableRequest, db: Session = Depends(get_db)):
    """Update an existing table."""
    table = db.query(TableMetadata).filter(TableMetadata.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    table.name = table_request.name
    table.description = table_request.description
    db.commit()
    db.refresh(table)
    return TableResponse.model_validate(table)


@router.delete("/{table_id}", status_code=204)
def delete_table(table_id: str, db: Session = Depends(get_db)):
    """Delete a table (hard delete)."""
    table = db.query(TableMetadata).filter(TableMetadata.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    db.delete(table)
    db.commit()
    return None
