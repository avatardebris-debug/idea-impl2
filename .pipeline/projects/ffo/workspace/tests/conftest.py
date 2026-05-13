"""Shared fixtures for FFO tests."""

import pytest
from ffo.models.player import Player, FreeAgent
from ffo.models.salary_cap import SalaryCap
from ffo.models.free_agent_pool import FreeAgentPool


@pytest.fixture
def sample_player():
    """A basic player for testing."""
    return Player(
        name="Test Player",
        position="FWD",
        overall_rating=80.0,
        age=28,
        contract_length=3,
        salary=10000000,
        value=50000000,
    )


@pytest.fixture
def sample_free_agent():
    """A basic free agent for testing."""
    return FreeAgent(
        name="Test Agent",
        position="MID",
        overall_rating=85.0,
        age=25,
        contract_length=4,
        salary=12000000,
        value=60000000,
        available=True,
        agent_name="SuperAgent",
        preferred_positions=["MID", "FWD"],
    )


@pytest.fixture
def sample_roster(sample_player):
    """A roster with multiple players."""
    return [
        Player(name="P1", position="GK", overall_rating=75.0, age=30,
               contract_length=2, salary=5000000, value=30000000),
        Player(name="P2", position="DEF", overall_rating=80.0, age=27,
               contract_length=3, salary=8000000, value=40000000),
        Player(name="P3", position="MID", overall_rating=85.0, age=29,
               contract_length=4, salary=12000000, value=55000000),
        Player(name="P4", position="FWD", overall_rating=90.0, age=26,
               contract_length=5, salary=15000000, value=70000000),
    ]


@pytest.fixture
def sample_pool(sample_free_agent):
    """A pool of free agents."""
    return FreeAgentPool([
        FreeAgent(name="FA1", position="FWD", overall_rating=88.0, age=24,
                  contract_length=5, salary=14000000, value=65000000,
                  available=True, agent_name="Agent1", preferred_positions=["FWD"]),
        FreeAgent(name="FA2", position="MID", overall_rating=82.0, age=31,
                  contract_length=2, salary=9000000, value=45000000,
                  available=True, agent_name="Agent2", preferred_positions=["MID"]),
        FreeAgent(name="FA3", position="DEF", overall_rating=78.0, age=33,
                  contract_length=1, salary=6000000, value=30000000,
                  available=False, agent_name="Agent3", preferred_positions=["DEF"]),
        FreeAgent(name="FA4", position="GK", overall_rating=70.0, age=36,
                  contract_length=1, salary=3000000, value=15000000,
                  available=True, agent_name="Agent4", preferred_positions=["GK"]),
    ])


@pytest.fixture
def sample_cap():
    """A salary cap with a reasonable limit."""
    return SalaryCap(cap_limit=100000000)


@pytest.fixture
def large_cap():
    """A very large salary cap (effectively unlimited)."""
    return SalaryCap(cap_limit=1000000000)
