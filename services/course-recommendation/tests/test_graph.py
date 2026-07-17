from __future__ import annotations

import pytest
from app.graph import PrerequisiteCycleError, build_prerequisite_graph
from conftest import course_group


def ids(results):
    return [item.course_id for item in results]


def test_simple_prerequisite_chain(chain_courses):
    graph = build_prerequisite_graph(
        chain_courses,
        [course_group("g1", "calc2", "calc1"), course_group("g2", "linear", "calc2")],
    )
    assert ids(graph.get_direct_prerequisites("linear")) == ["calc2"]
    assert ids(graph.get_all_prerequisite_ancestors("linear")) == ["calc1", "calc2"]
    assert graph.get_dependency_depth("linear") == 2
    assert ids(graph.get_critical_prerequisite_chain("linear")) == ["calc1", "calc2", "linear"]


def test_branching_graph_unlocks_direct_and_transitive_courses(chain_courses):
    graph = build_prerequisite_graph(
        chain_courses,
        [
            course_group("g1", "calc2", "calc1"),
            course_group("g2", "linear", "calc2"),
            course_group("g3", "physics1", "calc1"),
            course_group("g4", "physics2", "physics1"),
        ],
    )
    assert ids(graph.get_directly_unlocked_courses("calc1")) == ["calc2", "physics1"]
    assert ids(graph.get_all_unlocked_descendants("calc1")) == [
        "calc2",
        "linear",
        "physics1",
        "physics2",
    ]


def test_graph_nodes_and_edges_retain_structured_metadata(chain_courses):
    graph = build_prerequisite_graph(chain_courses, [course_group("g1", "calc2", "calc1")])
    assert graph.graph.nodes["calc1"]["course_code"] == "MATH 124"
    assert graph.graph.edges["calc1", "calc2"]["group_id"] == "g1"
    assert graph.graph.edges["calc1", "calc2"]["condition_type"] == "COURSE"


def test_cycle_detection_rejects_invalid_prerequisite_data(chain_courses):
    with pytest.raises(PrerequisiteCycleError) as caught:
        build_prerequisite_graph(
            chain_courses,
            [course_group("g1", "calc2", "calc1"), course_group("g2", "calc1", "calc2")],
        )
    assert caught.value.cycles == [["calc1", "calc2", "calc1"]]
