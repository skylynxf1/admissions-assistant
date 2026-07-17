from __future__ import annotations

import pytest
from app.models import (
    ConditionType,
    Confidence,
    Course,
    GroupType,
    PrerequisiteCondition,
    PrerequisiteGroup,
)
from app.sample_data import sample_dataset


@pytest.fixture
def dataset():
    return sample_dataset()


@pytest.fixture
def chain_courses():
    return [
        Course(
            id="calc1",
            institution_id="college",
            course_code="MATH 124",
            title="Calculus I",
            credits_min=5,
        ),
        Course(
            id="calc2",
            institution_id="college",
            course_code="MATH 125",
            title="Calculus II",
            credits_min=5,
        ),
        Course(
            id="linear",
            institution_id="college",
            course_code="MATH 208",
            title="Linear Algebra",
            credits_min=5,
        ),
        Course(
            id="physics1",
            institution_id="college",
            course_code="PHYS 121",
            title="Physics I",
            credits_min=5,
        ),
        Course(
            id="physics2",
            institution_id="college",
            course_code="PHYS 122",
            title="Physics II",
            credits_min=5,
        ),
    ]


def course_group(group_id: str, target: str, prerequisite: str, **condition_updates):
    return PrerequisiteGroup(
        id=group_id,
        target_course_id=target,
        group_type=GroupType.ALL,
        conditions=[
            PrerequisiteCondition(
                id=f"condition-{group_id}",
                prerequisite_group_id=group_id,
                condition_type=ConditionType.COURSE,
                prerequisite_course_id=prerequisite,
                confidence=Confidence.HIGH,
                **condition_updates,
            )
        ],
    )
