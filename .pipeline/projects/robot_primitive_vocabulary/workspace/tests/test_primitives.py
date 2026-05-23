"""Test suite for RobotPrimitives library."""

import pytest
from shared_libs.RobotPrimitives.primitive import Primitive, VALID_CATEGORIES


class TestPrimitiveBase:
    """Tests for the Primitive base class."""

    def test_primitive_has_name(self):
        """Every primitive must have a name."""
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        m = MoveTo()
        assert m.name == "move_to"

    def test_primitive_has_category(self):
        """Every primitive must have a valid category."""
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        m = MoveTo()
        assert m.category in VALID_CATEGORIES

    def test_primitive_has_parameters(self):
        """Every primitive must have a parameters dict."""
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        m = MoveTo()
        assert isinstance(m.parameters, dict)

    def test_primitive_has_description(self):
        """Every primitive must have a description."""
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        m = MoveTo()
        assert isinstance(m.description, str)
        assert len(m.description) > 0

    def test_primitive_execute_exists(self):
        """Every primitive must have an execute method."""
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        m = MoveTo()
        assert hasattr(m, "execute")
        assert callable(m.execute)

    def test_primitive_execute_returns_dict(self):
        """execute() should return a dict."""
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        m = MoveTo()
        result = m.execute()
        assert isinstance(result, dict)

    def test_primitive_execute_returns_status(self):
        """execute() result must contain 'status' key."""
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        m = MoveTo()
        result = m.execute()
        assert "status" in result


class TestLocomotionPrimitives:
    """Tests for locomotion primitives."""

    def test_move_to_default_params(self):
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        m = MoveTo()
        assert m.target_x == 0.0
        assert m.target_y == 0.0
        assert m.target_z == 0.0

    def test_move_to_custom_params(self):
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        m = MoveTo(target_x=1.0, target_y=2.0, target_z=3.0)
        assert m.target_x == 1.0
        assert m.target_y == 2.0
        assert m.target_z == 3.0

    def test_move_to_execute(self):
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        m = MoveTo(target_x=1.0, target_y=1.0)
        result = m.execute()
        assert result["status"] == "success"

    def test_rotate_to_default_params(self):
        from shared_libs.RobotPrimitives.locomotion import RotateTo
        r = RotateTo()
        assert r.target_angle == 0.0

    def test_rotate_to_custom_params(self):
        from shared_libs.RobotPrimitives.locomotion import RotateTo
        r = RotateTo(target_angle=90.0)
        assert r.target_angle == 90.0

    def test_rotate_to_execute(self):
        from shared_libs.RobotPrimitives.locomotion import RotateTo
        r = RotateTo(target_angle=45.0)
        result = r.execute()
        assert result["status"] == "success"

    def test_approach_default_params(self):
        from shared_libs.RobotPrimitives.locomotion import Approach
        a = Approach(target_id="obj1")
        assert a.target_id == "obj1"
        assert a.distance == 1.0

    def test_approach_execute(self):
        from shared_libs.RobotPrimitives.locomotion import Approach
        a = Approach(target_id="obj1", distance=0.5)
        result = a.execute()
        assert result["status"] == "success"

    def test_retreat_default_params(self):
        from shared_libs.RobotPrimitives.locomotion import Retreat
        r = Retreat(target_id="obj1")
        assert r.target_id == "obj1"
        assert r.distance == 1.0

    def test_retreat_execute(self):
        from shared_libs.RobotPrimitives.locomotion import Retreat
        r = Retreat(target_id="obj1", distance=0.5)
        result = r.execute()
        assert result["status"] == "success"


class TestManipulationPrimitives:
    """Tests for manipulation primitives."""

    def test_grasp_default_params(self):
        from shared_libs.RobotPrimitives.manipulation import Grasp
        g = Grasp(object_id="obj1")
        assert g.object_id == "obj1"
        assert g.grasp_type == "power"

    def test_grasp_custom_params(self):
        from shared_libs.RobotPrimitives.manipulation import Grasp
        g = Grasp(object_id="cup1", grasp_type="precision")
        assert g.object_id == "cup1"
        assert g.grasp_type == "precision"

    def test_grasp_execute(self):
        from shared_libs.RobotPrimitives.manipulation import Grasp
        g = Grasp(object_id="cup1")
        result = g.execute()
        assert result["status"] == "success"

    def test_grasp_invalid_object_id(self):
        from shared_libs.RobotPrimitives.manipulation import Grasp
        with pytest.raises(ValueError):
            Grasp(object_id="  ")

    def test_release_execute(self):
        from shared_libs.RobotPrimitives.manipulation import Release
        r = Release(object_id="obj1")
        result = r.execute()
        assert result["status"] == "success"

    def test_push_execute(self):
        from shared_libs.RobotPrimitives.manipulation import Push
        p = Push(object_id="box1", direction_x=1.0)
        result = p.execute()
        assert result["status"] == "success"

    def test_pull_execute(self):
        from shared_libs.RobotPrimitives.manipulation import Pull
        p = Pull(object_id="box1", direction_x=-1.0)
        result = p.execute()
        assert result["status"] == "success"

    def test_lift_execute(self):
        from shared_libs.RobotPrimitives.manipulation import Lift
        l = Lift(object_id="box1", height=0.5)
        result = l.execute()
        assert result["status"] == "success"

    def test_place_execute(self):
        from shared_libs.RobotPrimitives.manipulation import Place
        p = Place(object_id="obj1", target_x=0.0, target_y=0.0, target_z=0.0)
        result = p.execute()
        assert result["status"] == "success"

    def test_insert_execute(self):
        from shared_libs.RobotPrimitives.manipulation import Insert
        i = Insert(object_id="obj1", target_id="slot1")
        result = i.execute()
        assert result["status"] == "success"

    def test_rotate_object_execute(self):
        from shared_libs.RobotPrimitives.manipulation import RotateObject
        r = RotateObject(object_id="knob1", angle=90.0)
        result = r.execute()
        assert result["status"] == "success"


class TestObservationPrimitives:
    """Tests for observation primitives."""

    def test_look_at_execute(self):
        from shared_libs.RobotPrimitives.observation import LookAt
        l = LookAt(target_id="obj1", frame="head")
        result = l.execute()
        assert result["status"] == "success"

    def test_scan_execute(self):
        from shared_libs.RobotPrimitives.observation import Scan
        s = Scan(frame="head")
        result = s.execute()
        assert result["status"] == "success"

    def test_measure_distance_execute(self):
        from shared_libs.RobotPrimitives.observation import MeasureDistance
        m = MeasureDistance(target_id="obj1")
        result = m.execute()
        assert result["status"] == "success"

    def test_detect_object_execute(self):
        from shared_libs.RobotPrimitives.observation import DetectObject
        d = DetectObject()
        result = d.execute()
        assert result["status"] == "success"


class TestForcePrimitives:
    """Tests for force primitives."""

    def test_apply_force_execute(self):
        from shared_libs.RobotPrimitives.force import ApplyForce
        f = ApplyForce(target_id="obj1", force_x=10.0, force_y=0.0, force_z=0.0)
        result = f.execute()
        assert result["status"] == "success"

    def test_apply_torque_execute(self):
        from shared_libs.RobotPrimitives.force import ApplyTorque
        t = ApplyTorque(target_id="knob1", torque_magnitude=5.0, axis="z")
        result = t.execute()
        assert result["status"] == "success"

    def test_maintain_contact_execute(self):
        from shared_libs.RobotPrimitives.force import MaintainContact
        c = MaintainContact(target_id="obj1", force_magnitude=1.0)
        result = c.execute()
        assert result["status"] == "success"


class TestControlFlowPrimitives:
    """Tests for control flow primitives."""

    def test_sequence_execute(self):
        from shared_libs.RobotPrimitives.control_flow import Sequence
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        s = Sequence(primitives=[MoveTo(target_x=1.0)])
        result = s.execute()
        assert result["status"] == "success"
        assert len(result["results"]) == 1

    def test_parallel_execute(self):
        from shared_libs.RobotPrimitives.control_flow import Parallel
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        p = Parallel(primitives=[MoveTo(target_x=1.0), MoveTo(target_y=1.0)])
        result = p.execute()
        assert result["status"] == "success"
        assert len(result["results"]) == 2

    def test_repeat_until_execute(self):
        from shared_libs.RobotPrimitives.control_flow import RepeatUntil
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        r = RepeatUntil(primitive=MoveTo(target_x=1.0), condition="object_detected")
        result = r.execute()
        assert result["status"] == "success"

    def test_conditional_execute(self):
        from shared_libs.RobotPrimitives.control_flow import Conditional
        from shared_libs.RobotPrimitives.locomotion import MoveTo
        c = Conditional(condition="object_detected", primitive=MoveTo(target_x=1.0))
        result = c.execute()
        assert result["status"] == "success"
        assert result["executed"] is True

    def test_conditional_no_primitive(self):
        from shared_libs.RobotPrimitives.control_flow import Conditional
        c = Conditional(condition="object_detected")
        result = c.execute()
        assert result["status"] == "success"
        assert result["executed"] is False

    def test_wait_execute(self):
        from shared_libs.RobotPrimitives.control_flow import Wait
        w = Wait(duration=0.1)
        result = w.execute()
        assert result["status"] == "success"
        assert result["waited_for"] == 0.1

    def test_signal_done_execute(self):
        from shared_libs.RobotPrimitives.control_flow import SignalDone
        s = SignalDone(task_id="task1")
        result = s.execute()
        assert result["status"] == "success"
        assert result["signal"] == "done"

    def test_request_human_execute(self):
        from shared_libs.RobotPrimitives.control_flow import RequestHuman
        r = RequestHuman(task_id="task1", reason="object_not_found")
        result = r.execute()
        assert result["status"] == "success"


class TestPackageMetadata:
    """Tests for package-level metadata."""

    def test_package_version(self):
        import shared_libs.RobotPrimitives as pkg
        assert hasattr(pkg, "__version__")
        assert isinstance(pkg.__version__, str)

    def test_package_docstring(self):
        import shared_libs.RobotPrimitives as pkg
        assert pkg.__doc__ is not None
        assert len(pkg.__doc__) > 0
