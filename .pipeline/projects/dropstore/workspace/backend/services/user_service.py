"""User and team management service."""

import hashlib
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from backend.models.user import User, Team, TeamMember, Role
from backend.utils.database import async_session_factory


def _generate_user_id() -> str:
    """Generate a unique user ID."""
    return f"user_{uuid.uuid4().hex[:12]}"


def _generate_team_id() -> str:
    """Generate a unique team ID."""
    return f"team_{uuid.uuid4().hex[:12]}"


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return hashlib.sha256(password.encode()).hexdigest()


async def create_user(
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
) -> User:
    """Create a new user account."""
    user_id = _generate_user_id()

    user = User(
        user_id=user_id,
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        is_active=True,
        is_verified=False,
    )

    async with async_session_factory() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def get_user(user_id: str) -> Optional[User]:
    """Get a user by ID."""
    async with async_session_factory() as session:
        user = await session.get(User, user_id)
        return user


async def get_user_by_email(email: str) -> Optional[User]:
    """Get a user by email."""
    async with async_session_factory() as session:
        user = await session.execute(
            User.__table__.select().where(User.email == email)
        )
        return user.scalar_one_or_none()


async def verify_user(user_id: str) -> Optional[User]:
    """Mark a user as verified."""
    async with async_session_factory() as session:
        user = await session.get(User, user_id)
        if user:
            user.is_verified = True
            user.verified_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(user)
        return user


async def create_team(name: str, description: str = "") -> Team:
    """Create a new team."""
    team_id = _generate_team_id()

    team = Team(
        team_id=team_id,
        name=name,
        description=description,
        is_active=True,
    )

    async with async_session_factory() as session:
        session.add(team)
        await session.commit()
        await session.refresh(team)
    return team


async def get_team(team_id: str) -> Optional[Team]:
    """Get a team by ID."""
    async with async_session_factory() as session:
        team = await session.get(Team, team_id)
        return team


async def list_teams(user_id: str) -> List[Team]:
    """List all teams a user belongs to."""
    async with async_session_factory() as session:
        members = await session.execute(
            TeamMember.__table__.select().where(TeamMember.user_id == user_id)
        )
        member_list = list(members.scalars().all())
        team_ids = [m.team_id for m in member_list]

        if not team_ids:
            return []

        teams = await session.execute(
            Team.__table__.select().where(Team.team_id.in_(team_ids))
        )
        return list(teams.scalars().all())


async def add_team_member(
    team_id: str,
    user_id: str,
    role: str = "member",
) -> TeamMember:
    """Add a user to a team."""
    member_id = f"mem_{uuid.uuid4().hex[:12]}"

    member = TeamMember(
        member_id=member_id,
        team_id=team_id,
        user_id=user_id,
        role=role,
        is_active=True,
    )

    async with async_session_factory() as session:
        session.add(member)
        await session.commit()
        await session.refresh(member)
    return member


async def remove_team_member(team_id: str, user_id: str) -> bool:
    """Remove a user from a team."""
    async with async_session_factory() as session:
        member = await session.execute(
            TeamMember.__table__.select().where(
                (TeamMember.team_id == team_id) &
                (TeamMember.user_id == user_id)
            )
        )
        member_obj = member.scalar_one_or_none()
        if member_obj:
            member_obj.is_active = False
            await session.commit()
            return True
        return False


async def get_team_members(team_id: str) -> List[TeamMember]:
    """Get all active members of a team."""
    async with async_session_factory() as session:
        members = await session.execute(
            TeamMember.__table__.select().where(
                (TeamMember.team_id == team_id) &
                (TeamMember.is_active == True)
            )
        )
        return list(members.scalars().all())


async def update_team_member_role(team_id: str, user_id: str, role: str) -> Optional[TeamMember]:
    """Update a team member's role."""
    async with async_session_factory() as session:
        member = await session.execute(
            TeamMember.__table__.select().where(
                (TeamMember.team_id == team_id) &
                (TeamMember.user_id == user_id)
            )
        )
        member_obj = member.scalar_one_or_none()
        if member_obj:
            member_obj.role = role
            await session.commit()
            await session.refresh(member_obj)
        return member_obj


async def get_user_roles(user_id: str) -> List[Dict[str, Any]]:
    """Get all roles for a user across all teams."""
    async with async_session_factory() as session:
        members = await session.execute(
            TeamMember.__table__.select().where(
                (TeamMember.user_id == user_id) &
                (TeamMember.is_active == True)
            )
        )
        member_list = list(members.scalars().all())

        roles = []
        for member in member_list:
            team = await session.get(Team, member.team_id)
            roles.append({
                "team_id": member.team_id,
                "team_name": team.name if team else "Unknown",
                "role": member.role,
            })
        return roles
