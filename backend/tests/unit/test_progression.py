from decimal import Decimal

from app.plans.models import Pattern
from app.plans.progression import LoggedSet, suggest


def sets(*pairs: tuple[str, int]) -> list[LoggedSet]:
    return [LoggedSet(Decimal(w), r) for w, r in pairs]


def test_first_time():
    s = suggest([], 12, Pattern.SQUAT, True)
    assert s.kind == "first_time" and s.weight_kg is None


def test_add_weight_when_all_sets_hit_top_of_range_lower_body():
    s = suggest(sets(("60", 12), ("60", 12), ("60", 12)), 12, Pattern.SQUAT, True)
    assert s.kind == "add_weight" and s.weight_kg == Decimal("65.0")


def test_add_weight_upper_body_smaller_increment():
    s = suggest(sets(("40", 10), ("40", 10)), 10, Pattern.HORIZONTAL_PUSH, True)
    assert s.weight_kg == Decimal("42.5")


def test_isolation_lower_body_uses_small_increment():
    s = suggest(
        sets(
            ("30", 15),
        ),
        15,
        Pattern.QUAD_ISOLATION,
        False,
    )
    assert s.weight_kg == Decimal("32.5")


def test_add_reps_when_range_not_completed():
    s = suggest(sets(("60", 12), ("60", 10), ("60", 9)), 12, Pattern.SQUAT, True)
    assert s.kind == "add_reps" and s.weight_kg == Decimal("60")


def test_only_heaviest_sets_count():
    # Lighter warm-up sets with fewer reps do not block progression.
    s = suggest(sets(("40", 5), ("60", 12), ("60", 12)), 12, Pattern.HINGE, True)
    assert s.kind == "add_weight"
