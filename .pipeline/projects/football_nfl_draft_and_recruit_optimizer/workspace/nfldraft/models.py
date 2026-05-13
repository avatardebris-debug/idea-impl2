"""Core data models for NFL draft and recruit optimizer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Position(Enum):
    """NFL positions."""
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    OL = "OL"
    DL = "DL"
    LB = "LB"
    CB = "CB"
    S = "S"
    K = "K"
    P = "P"
    LS = "LS"
    EDGE = "EDGE"
    NT = "NT"
    ILB = "ILB"
    OLB = "OLB"
    G = "G"
    T = "T"
    C = "C"
    FS = "FS"
    SS = "SS"
    H = "H"  # Holder
    UNKNOWN = "UNKNOWN"


class DraftRound(Enum):
    """NFL draft rounds."""
    ROUND_1 = 1
    ROUND_2 = 2
    ROUND_3 = 3
    ROUND_4 = 4
    ROUND_5 = 5
    ROUND_6 = 6
    ROUND_7 = 7

    @classmethod
    def from_int(cls, value: int) -> DraftRound:
        return cls(value)


class RecruitStatus(Enum):
    """Recruiting target status."""
    UNCOMMITTED = "uncommitted"
    COMMITTED = "committed"
    INTERESTED = "interested"
    OFFERED = "offered"
    DE_COMMITTED = "decommitted"


@dataclass
class Player:
    """Represents a player (college prospect, free agent, or NFL player)."""
    name: str
    position: Position
    overall_rating: float = 0.0  # 0-100
    age: int | None = None
    height: str = ""  # e.g., "6-2"
    weight: int = 0  # lbs
    college: str = ""
    state: str = ""
    hometown: str = ""
    salary: float | None = None
    contract_length: int | None = None  # years
    stats: dict = field(default_factory=dict)  # e.g., {"passing_yards": 3000, "tds": 25}
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    draft_projected_round: Optional[int] = None
    draft_projected_pick: Optional[int] = None
    recruiting_rank: Optional[int] = None  # national recruiting rank
    recruiting_class_year: Optional[int] = None
    is_free_agent: bool = False
    is_college_prospect: bool = False
    is_nfl_player: bool = False

    def __post_init__(self):
        if not isinstance(self.position, Position):
            self.position = Position(self.position)
        if self.overall_rating < 0:
            raise ValueError("overall_rating cannot be negative")
        if self.overall_rating > 100:
            raise ValueError("overall_rating cannot exceed 100")

    @property
    def value_score(self) -> float:
        """Compute a cost-effectiveness score (higher is better)."""
        salary = self.salary if self.salary is not None else 0.0
        age = self.age if self.age is not None else 0
        contract_length = self.contract_length if self.contract_length is not None else 0
        if salary <= 0:
            return float("inf") if self.overall_rating > 0 else 0.0
        base = self.overall_rating / salary
        # Age factor: peak around age 27-30
        if age <= 30:
            age_factor = 1.0 + (30 - age) * 0.01
        else:
            age_factor = max(0.5, 1.0 - (age - 30) * 0.01)
        # Contract factor: longer contracts are more valuable
        contract_factor = 1.0 + (contract_length - 1) * 0.05
        return base * age_factor * contract_factor

    @classmethod
    def from_dict(cls, data: dict) -> Player:
        pos = data.get("position", "UNKNOWN")
        if isinstance(pos, str):
            pos = Position(pos)
        return cls(
            name=data.get("name", "Unknown"),
            position=pos,
            overall_rating=data.get("overall_rating", 0.0),
            age=data.get("age"),
            height=data.get("height", ""),
            weight=data.get("weight", 0),
            college=data.get("college", ""),
            state=data.get("state", ""),
            hometown=data.get("hometown", ""),
            salary=data.get("salary"),
            contract_length=data.get("contract_length"),
            stats=data.get("stats", {}),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            draft_projected_round=data.get("draft_projected_round"),
            draft_projected_pick=data.get("draft_projected_pick"),
            recruiting_rank=data.get("recruiting_rank"),
            recruiting_class_year=data.get("recruiting_class_year"),
            is_free_agent=data.get("is_free_agent", False),
            is_college_prospect=data.get("is_college_prospect", False),
            is_nfl_player=data.get("is_nfl_player", False),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "position": self.position.value,
            "overall_rating": self.overall_rating,
            "age": self.age,
            "height": self.height,
            "weight": self.weight,
            "college": self.college,
            "state": self.state,
            "hometown": self.hometown,
            "salary": self.salary,
            "contract_length": self.contract_length,
            "stats": self.stats,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "draft_projected_round": self.draft_projected_round,
            "draft_projected_pick": self.draft_projected_pick,
            "recruiting_rank": self.recruiting_rank,
            "recruiting_class_year": self.recruiting_class_year,
            "is_free_agent": self.is_free_agent,
            "is_college_prospect": self.is_college_prospect,
            "is_nfl_player": self.is_nfl_player,
        }


@dataclass
class Team:
    """Represents an NFL team."""
    name: str
    city: str
    conference: str  # "AFC" or "NFC"
    division: str  # e.g., "North", "East", "South", "West"
    salary_cap: float = 250.0  # in millions
    current_payroll: float = 0.0
    roster: list[Player] = field(default_factory=list)
    needs: dict[str, list[Position]] = field(default_factory=dict)  # priority positions
    strengths: list[Position] = field(default_factory=list)

    @property
    def remaining_cap(self) -> float:
        return self.salary_cap - self.current_payroll

    def add_player(self, player: Player) -> None:
        salary = player.salary if player.salary is not None else 0.0
        if self.current_payroll + salary > self.salary_cap:
            raise ValueError(
                f"Cannot add {player.name}: would exceed salary cap. "
                f"Remaining: {self.remaining_cap:.2f}M"
            )
        self.roster.append(player)
        self.current_payroll += salary

    def remove_player(self, player: Player) -> None:
        if player not in self.roster:
            raise ValueError(f"{player.name} is not on the roster")
        self.roster.remove(player)
        self.current_payroll -= player.salary

    def can_afford(self, player: Player) -> bool:
        salary = player.salary if player.salary is not None else 0.0
        return self.current_payroll + salary <= self.salary_cap

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "city": self.city,
            "conference": self.conference,
            "division": self.division,
            "salary_cap": self.salary_cap,
            "current_payroll": self.current_payroll,
            "remaining_cap": self.remaining_cap,
            "roster_count": len(self.roster),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Team:
        return cls(
            name=data.get("name", "Unknown"),
            city=data.get("city", ""),
            conference=data.get("conference", "AFC"),
            division=data.get("division", "North"),
            salary_cap=data.get("salary_cap", 250.0),
            current_payroll=data.get("current_payroll", 0.0),
        )


@dataclass
class DraftPick:
    """Represents a draft pick."""
    round_num: int
    overall_pick: int
    team: Team
    player: Optional[Player] = None
    pick_status: str = "available"  # "available", "selected", "traded"

    def select(self, player: Player) -> None:
        if self.pick_status != "available":
            raise ValueError(f"Pick #{self.overall_pick} has already been used")
        self.player = player
        self.pick_status = "selected"
        self.team.add_player(player)

    def to_dict(self) -> dict:
        return {
            "round": self.round_num,
            "overall_pick": self.overall_pick,
            "team": self.team.name,
            "player": self.player.name if self.player else None,
            "status": self.pick_status,
        }


@dataclass
class RecruitTarget:
    """Represents a high school recruiting target."""
    name: str
    position: Position
    height: str = ""
    weight: int = 0
    hometown: str = ""
    state: str = ""
    recruiting_rank: int = 0  # national rank
    position_rank: int = 0  # position rank
    overall_rating: float = 0.0  # 0-100 composite
    committed_to: Optional[str] = None  # school name
    interested_schools: list[str] = field(default_factory=list)
    offered_by: list[str] = field(default_factory=list)
    academics_gpa: float = 0.0
    stats: dict = field(default_factory=dict)
    commitment_status: RecruitStatus = RecruitStatus.UNCOMMITTED

    def commit_to(self, school: str) -> None:
        self.committed_to = school
        self.commitment_status = RecruitStatus.COMMITTED
        if school not in self.offered_by:
            self.offered_by.append(school)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "position": self.position.value,
            "height": self.height,
            "weight": self.weight,
            "hometown": self.hometown,
            "state": self.state,
            "recruiting_rank": self.recruiting_rank,
            "position_rank": self.position_rank,
            "overall_rating": self.overall_rating,
            "committed_to": self.committed_to,
            "interested_schools": self.interested_schools,
            "offered_by": self.offered_by,
            "academics_gpa": self.academics_gpa,
            "stats": self.stats,
            "commitment_status": self.commitment_status.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RecruitTarget:
        pos = data.get("position", "UNKNOWN")
        if isinstance(pos, str):
            pos = Position(pos)
        status = data.get("commitment_status", "uncommitted")
        if isinstance(status, str):
            status = RecruitStatus(status)
        return cls(
            name=data.get("name", "Unknown"),
            position=pos,
            height=data.get("height", ""),
            weight=data.get("weight", 0),
            hometown=data.get("hometown", ""),
            state=data.get("state", ""),
            recruiting_rank=data.get("recruiting_rank", 0),
            position_rank=data.get("position_rank", 0),
            overall_rating=data.get("overall_rating", 0.0),
            committed_to=data.get("committed_to"),
            interested_schools=data.get("interested_schools", []),
            offered_by=data.get("offered_by", []),
            academics_gpa=data.get("academics_gpa", 0.0),
            stats=data.get("stats", {}),
            commitment_status=status,
        )


@dataclass
class DraftResult:
    """Result of a draft simulation."""
    team: Team
    picks: list[DraftPick] = field(default_factory=list)
    total_spent: float = 0.0
    total_players: int = 0
    top_picks: list[Player] = field(default_factory=list)

    def add_pick(self, pick: DraftPick) -> None:
        self.picks.append(pick)
        if pick.player:
            salary = pick.player.salary if pick.player.salary is not None else 0.0
            self.total_spent += salary
            self.total_players += 1
            self.top_picks.append(pick.player)

    def to_dict(self) -> dict:
        return {
            "team": self.team.name,
            "total_picks": len(self.picks),
            "total_spent": self.total_spent,
            "total_players": self.total_players,
            "top_picks": [p.name for p in self.top_picks[:5]],
            "remaining_cap": self.team.remaining_cap,
        }
