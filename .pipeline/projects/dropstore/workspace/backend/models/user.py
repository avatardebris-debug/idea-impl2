"""User, Team, and Role ORM models for team & role management."""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func

from backend.utils.database import Base


class User(Base):
    """A user account in the Dropstore platform."""
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    first_name = Column(String, default="")
    last_name = Column(String, default="")
    avatar_url = Column(String, default="")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Team(Base):
    """A team/workspace that owns stores and catalogs."""
    __tablename__ = "teams"

    team_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    owner_id = Column(String, nullable=False)
    plan = Column(String, default="free")  # free, pro, enterprise
    max_members = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TeamMember(Base):
    """A member of a team with a specific role."""
    __tablename__ = "team_members"

    member_id = Column(String, primary_key=True)
    team_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    role = Column(String, nullable=False)  # owner, admin, editor, viewer
    permissions = Column(JSON, default=dict)  # Fine-grained permissions
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)


class Role(Base):
    """A role definition with associated permissions."""
    __tablename__ = "roles"

    role_id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)  # owner, admin, editor, viewer
    description = Column(Text, default="")
    permissions = Column(JSON, nullable=False)  # Dict of permission keys
    is_system_role = Column(Boolean, default=True)  # System-defined vs custom
    created_at = Column(DateTime(timezone=True), server_default=func.now())
