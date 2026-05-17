"""Tests for Domain-aware taste modeling (Task 1)."""

import pytest
from ranker_core.domains import Domain, DomainManager, DomainValidationError
from ranker_core.profile import TasteProfile, TasteProfileValidationError


# ====================================================================
# Domain tests
# ====================================================================


class TestDomain:
    """Tests for the Domain dataclass."""

    def test_create_domain(self):
        domain = Domain(name="music", description="Music preferences")
        assert domain.name == "music"
        assert domain.description == "Music preferences"
        assert domain.taste_vector == {}
        assert domain.id is not None

    def test_domain_with_taste_vector(self):
        domain = Domain(
            name="film",
            description="Film preferences",
            taste_vector={"movie1": 4.0, "movie2": 3.5},
        )
        assert domain.taste_vector["movie1"] == 4.0
        assert domain.taste_vector["movie2"] == 3.5

    def test_domain_with_parent(self):
        domain = Domain(name="rock", parent_domain="music")
        assert domain.parent_domain == "music"

    def test_domain_update_taste_vector(self):
        domain = Domain(name="music")
        domain.update_taste_vector("song1", 4.5)
        assert domain.taste_vector["song1"] == 4.5

    def test_domain_update_taste_vector_overwrites(self):
        domain = Domain(name="music", taste_vector={"song1": 3.0})
        domain.update_taste_vector("song1", 4.5)
        assert domain.taste_vector["song1"] == 4.5

    def test_domain_update_taste_vector_negative_raises(self):
        domain = Domain(name="music")
        with pytest.raises(DomainValidationError, match="value must be a non-negative number"):
            domain.update_taste_vector("song1", -1.0)

    def test_domain_update_taste_vector_empty_item_id_raises(self):
        domain = Domain(name="music")
        with pytest.raises(DomainValidationError, match="item_id must be a non-empty string"):
            domain.update_taste_vector("", 4.0)

    def test_domain_to_dict(self):
        domain = Domain(name="music", description="Music", taste_vector={"s1": 4.0})
        d = domain.to_dict()
        assert d["name"] == "music"
        assert d["description"] == "Music"
        assert d["taste_vector"]["s1"] == 4.0
        assert "id" in d
        assert "created_at" in d

    def test_domain_from_dict(self):
        data = {
            "id": "d1",
            "name": "music",
            "description": "Music",
            "taste_vector": {"s1": 4.0},
            "parent_domain": "entertainment",
            "created_at": "2024-01-01T00:00:00+00:00",
        }
        domain = Domain.from_dict(data)
        assert domain.name == "music"
        assert domain.taste_vector["s1"] == 4.0
        assert domain.parent_domain == "entertainment"
        assert domain.id == "d1"

    def test_domain_from_dict_missing_name_raises(self):
        with pytest.raises(DomainValidationError, match="Missing or empty required field: name"):
            Domain.from_dict({"id": "d1"})

    def test_domain_from_dict_missing_id_raises(self):
        with pytest.raises(DomainValidationError, match="Missing or empty required field: id"):
            Domain.from_dict({"name": "music"})

    def test_domain_invalid_taste_vector_type_raises(self):
        with pytest.raises(DomainValidationError, match="taste_vector must be a dict"):
            Domain(name="music", taste_vector="invalid")

    def test_domain_empty_name_raises(self):
        with pytest.raises(DomainValidationError, match="name is required"):
            Domain(name="")

    def test_domain_whitespace_name_raises(self):
        with pytest.raises(DomainValidationError, match="name is required"):
            Domain(name="   ")


# ====================================================================
# DomainManager tests
# ====================================================================


class TestDomainManager:
    """Tests for the DomainManager class."""

    def test_create_empty_manager(self):
        manager = DomainManager()
        assert manager.domains == {}
        assert manager.transfer_ratios == {}
        assert manager.default_transfer_ratio == 0.1

    def test_register_domain(self):
        manager = DomainManager()
        domain = Domain(name="music")
        manager.register_domain(domain)
        assert "music" in manager.list_domains()

    def test_register_duplicate_domain_raises(self):
        manager = DomainManager()
        manager.register_domain(Domain(name="music"))
        with pytest.raises(DomainValidationError, match="Domain already registered"):
            manager.register_domain(Domain(name="music"))

    def test_get_domain(self):
        manager = DomainManager()
        domain = Domain(name="music")
        manager.register_domain(domain)
        retrieved = manager.get_domain("music")
        assert retrieved.name == "music"

    def test_get_domain_not_found_raises(self):
        manager = DomainManager()
        with pytest.raises(KeyError, match="Domain not found: music"):
            manager.get_domain("music")

    def test_list_domains(self):
        manager = DomainManager()
        manager.register_domain(Domain(name="music"))
        manager.register_domain(Domain(name="film"))
        assert set(manager.list_domains()) == {"music", "film"}

    def test_remove_domain(self):
        manager = DomainManager()
        manager.register_domain(Domain(name="music"))
        manager.remove_domain("music")
        assert "music" not in manager.list_domains()

    def test_remove_domain_not_found_raises(self):
        manager = DomainManager()
        with pytest.raises(KeyError, match="Domain not found: music"):
            manager.remove_domain("music")

    def test_remove_domain_cleans_transfer_ratios(self):
        manager = DomainManager()
        music = Domain(name="music")
        film = Domain(name="film")
        manager.register_domain(music)
        manager.register_domain(film)
        manager.set_transfer_ratio("music", "film", 0.5)
        manager.remove_domain("music")
        assert ("music", "film") not in manager.transfer_ratios

    def test_set_transfer_ratio(self):
        manager = DomainManager()
        manager.register_domain(Domain(name="music"))
        manager.register_domain(Domain(name="film"))
        manager.set_transfer_ratio("music", "film", 0.5)
        assert manager.get_transfer_ratio("music", "film") == 0.5

    def test_set_transfer_ratio_invalid_source_raises(self):
        manager = DomainManager()
        manager.register_domain(Domain(name="music"))
        with pytest.raises(DomainValidationError, match="Target domain not registered"):
            manager.set_transfer_ratio("music", "unknown", 0.5)

    def test_set_transfer_ratio_invalid_ratio_raises(self):
        manager = DomainManager()
        manager.register_domain(Domain(name="music"))
        manager.register_domain(Domain(name="film"))
        with pytest.raises(DomainValidationError, match="Transfer ratio must be between"):
            manager.set_transfer_ratio("music", "film", 1.5)

    def test_get_transfer_ratio_uses_default(self):
        manager = DomainManager()
        manager.register_domain(Domain(name="music"))
        manager.register_domain(Domain(name="film"))
        assert manager.get_transfer_ratio("music", "film") == 0.1

    def test_get_transfer_ratio_uses_configured(self):
        manager = DomainManager()
        manager.register_domain(Domain(name="music"))
        manager.register_domain(Domain(name="film"))
        manager.set_transfer_ratio("music", "film", 0.75)
        assert manager.get_transfer_ratio("music", "film") == 0.75

    def test_transfer_weights(self):
        manager = DomainManager()
        music = Domain(name="music", taste_vector={"song1": 10.0})
        film = Domain(name="film", taste_vector={"movie1": 5.0})
        manager.register_domain(music)
        manager.register_domain(film)
        manager.set_transfer_ratio("music", "film", 0.5)

        transferred = manager.transfer_weights("music", "film", "song1", 4.0)

        assert transferred == pytest.approx(2.0)  # 4.0 * 0.5
        assert music.taste_vector["song1"] == pytest.approx(6.0)  # 10.0 - 4.0
        assert film.taste_vector.get("song1", 0.0) == pytest.approx(2.0)

    def test_transfer_weights_negative_amount_raises(self):
        manager = DomainManager()
        manager.register_domain(Domain(name="music"))
        manager.register_domain(Domain(name="film"))
        with pytest.raises(DomainValidationError, match="amount must be a non-negative number"):
            manager.transfer_weights("music", "film", "song1", -1.0)

    def test_transfer_weights_empty_item_id_raises(self):
        manager = DomainManager()
        manager.register_domain(Domain(name="music"))
        manager.register_domain(Domain(name="film"))
        with pytest.raises(DomainValidationError, match="item_id must be a non-empty string"):
            manager.transfer_weights("music", "film", "", 1.0)

    def test_transfer_weights_to_profile(self):
        manager = DomainManager()
        music = Domain(name="music", taste_vector={"song1": 4.0, "song2": 3.0})
        manager.register_domain(music)

        profile = TasteProfile(user_id="u1")
        manager.transfer_weights_to_profile("music", profile)

        assert profile.taste_vector["song1"] == 4.0
        assert profile.taste_vector["song2"] == 3.0

    def test_transfer_weights_to_profile_accumulates(self):
        manager = DomainManager()
        music = Domain(name="music", taste_vector={"song1": 4.0})
        manager.register_domain(music)

        profile = TasteProfile(user_id="u1", taste_vector={"song1": 1.0})
        manager.transfer_weights_to_profile("music", profile)

        assert profile.taste_vector["song1"] == pytest.approx(5.0)

    def test_to_dict_and_from_dict(self):
        manager = DomainManager()
        music = Domain(name="music", taste_vector={"s1": 4.0})
        film = Domain(name="film", taste_vector={"m1": 3.0})
        manager.register_domain(music)
        manager.register_domain(film)
        manager.set_transfer_ratio("music", "film", 0.5)
        manager.default_transfer_ratio = 0.2

        data = manager.to_dict()
        restored = DomainManager.from_dict(data)

        assert "music" in restored.list_domains()
        assert "film" in restored.list_domains()
        assert restored.get_transfer_ratio("music", "film") == 0.5
        assert restored.default_transfer_ratio == 0.2

    def test_validate_invalid_transfer_ratio_source_raises(self):
        manager = DomainManager()
        manager.register_domain(Domain(name="film"))
        # Manually set an invalid ratio and trigger validation
        manager.transfer_ratios[("music", "film")] = 0.5
        with pytest.raises(DomainValidationError, match="Transfer ratio source domain"):
            manager._validate()

    def test_validate_invalid_transfer_ratio_target_raises(self):
        manager = DomainManager()
        manager.register_domain(Domain(name="music"))
        # Manually set an invalid ratio and trigger validation
        manager.transfer_ratios[("music", "film")] = 0.5
        with pytest.raises(DomainValidationError, match="Transfer ratio target domain"):
            manager._validate()


# ====================================================================
# TasteProfile per-domain tests
# ====================================================================


class TestTasteProfilePerDomain:
    """Tests for per-domain taste vector support in TasteProfile."""

    def test_create_profile_with_domain_vectors(self):
        profile = TasteProfile(
            user_id="u1",
            domain_taste_vectors={"music": {"s1": 4.0}, "film": {"m1": 3.0}},
        )
        assert "music" in profile.get_all_domains()
        assert "film" in profile.get_all_domains()

    def test_update_domain_taste_vector(self):
        profile = TasteProfile(user_id="u1")
        profile.update_domain_taste_vector("music", "s1", 4.0)
        assert profile.get_domain_item_taste("music", "s1") == 4.0

    def test_update_domain_taste_vector_creates_domain(self):
        profile = TasteProfile(user_id="u1")
        profile.update_domain_taste_vector("music", "s1", 4.0)
        assert "music" in profile.get_all_domains()

    def test_update_domain_taste_vector_overwrites(self):
        profile = TasteProfile(user_id="u1", domain_taste_vectors={"music": {"s1": 3.0}})
        profile.update_domain_taste_vector("music", "s1", 4.0)
        assert profile.get_domain_item_taste("music", "s1") == 4.0

    def test_update_domain_taste_vector_negative_raises(self):
        profile = TasteProfile(user_id="u1")
        with pytest.raises(TasteProfileValidationError, match="non-negative"):
            profile.update_domain_taste_vector("music", "s1", -1.0)

    def test_update_domain_taste_vector_empty_domain_raises(self):
        profile = TasteProfile(user_id="u1")
        with pytest.raises(TasteProfileValidationError, match="domain_name must be a non-empty string"):
            profile.update_domain_taste_vector("", "s1", 4.0)

    def test_get_domain_taste_vector(self):
        profile = TasteProfile(user_id="u1", domain_taste_vectors={"music": {"s1": 4.0}})
        vec = profile.get_domain_taste_vector("music")
        assert vec == {"s1": 4.0}
        # Verify it's a copy
        vec["s1"] = 999
        assert profile.get_domain_taste_vector("music")["s1"] == 4.0

    def test_get_domain_taste_vector_missing_domain(self):
        profile = TasteProfile(user_id="u1")
        assert profile.get_domain_taste_vector("music") == {}

    def test_get_domain_taste_values(self):
        profile = TasteProfile(user_id="u1", domain_taste_vectors={"music": {"s1": 4.0, "s2": 3.0}})
        values = profile.get_domain_taste_values("music")
        assert set(values) == {4.0, 3.0}

    def test_get_domain_taste_values_missing_domain(self):
        profile = TasteProfile(user_id="u1")
        assert profile.get_domain_taste_values("music") == []

    def test_get_domain_item_taste_missing(self):
        profile = TasteProfile(user_id="u1")
        assert profile.get_domain_item_taste("music", "s1") == 0.0

    def test_get_all_domains(self):
        profile = TasteProfile(user_id="u1", domain_taste_vectors={"music": {}, "film": {}})
        assert set(profile.get_all_domains()) == {"music", "film"}

    def test_merge_with_domain_vectors(self):
        profile1 = TasteProfile(user_id="u1", domain_taste_vectors={"music": {"s1": 4.0}})
        profile2 = TasteProfile(user_id="u1", domain_taste_vectors={"film": {"m1": 3.0}})
        profile1.merge(profile2)
        assert profile1.get_domain_item_taste("music", "s1") == 4.0
        assert profile1.get_domain_item_taste("film", "m1") == 3.0

    def test_merge_accumulates_domain_vectors(self):
        profile1 = TasteProfile(user_id="u1", domain_taste_vectors={"music": {"s1": 4.0}})
        profile2 = TasteProfile(user_id="u1", domain_taste_vectors={"music": {"s1": 1.0}})
        profile1.merge(profile2)
        assert profile1.get_domain_item_taste("music", "s1") == 1.0  # other takes precedence

    def test_to_dict_includes_domain_vectors(self):
        profile = TasteProfile(user_id="u1", domain_taste_vectors={"music": {"s1": 4.0}})
        d = profile.to_dict()
        assert "domain_taste_vectors" in d
        assert d["domain_taste_vectors"]["music"]["s1"] == 4.0

    def test_from_dict_restores_domain_vectors(self):
        data = {
            "user_id": "u1",
            "domain_taste_vectors": {"music": {"s1": 4.0}},
            "taste_vector": {},
            "metadata": {},
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        profile = TasteProfile.from_dict(data)
        assert profile.get_domain_item_taste("music", "s1") == 4.0

    def test_equality_considers_domain_vectors(self):
        p1 = TasteProfile(user_id="u1", domain_taste_vectors={"music": {"s1": 4.0}})
        p2 = TasteProfile(user_id="u1", domain_taste_vectors={"music": {"s1": 4.0}})
        p3 = TasteProfile(user_id="u1", domain_taste_vectors={"music": {"s1": 3.0}})
        assert p1 == p2
        assert p1 != p3

    def test_hash_considers_domain_vectors(self):
        p1 = TasteProfile(user_id="u1", domain_taste_vectors={"music": {"s1": 4.0}})
        p2 = TasteProfile(user_id="u1", domain_taste_vectors={"music": {"s1": 4.0}})
        assert hash(p1) == hash(p2)

    def test_domain_taste_vector_invalid_key_raises(self):
        with pytest.raises(TasteProfileValidationError, match="domain_taste_vectors key must be"):
            TasteProfile(user_id="u1", domain_taste_vectors={"": {"s1": 4.0}})

    def test_domain_taste_vector_invalid_value_raises(self):
        with pytest.raises(TasteProfileValidationError, match="must be numeric"):
            TasteProfile(user_id="u1", domain_taste_vectors={"music": {"s1": "invalid"}})
