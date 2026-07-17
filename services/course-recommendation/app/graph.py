from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import networkx as nx

from app.models import ConditionType, Course, CourseOffering, PrerequisiteGroup


class PrerequisiteCycleError(ValueError):
    def __init__(self, cycles: list[list[str]]) -> None:
        self.cycles = cycles
        super().__init__(f"Prerequisite data contains {len(cycles)} cycle(s): {cycles}")


@dataclass(frozen=True)
class GraphCourseResult:
    course_id: str
    metadata: dict[str, object]


class PrerequisiteGraph:
    def __init__(self, graph: nx.DiGraph) -> None:
        self.graph = graph

    def _result(self, course_id: str) -> GraphCourseResult:
        return GraphCourseResult(course_id=course_id, metadata=dict(self.graph.nodes[course_id]))

    def get_direct_prerequisites(self, course_id: str) -> list[GraphCourseResult]:
        if course_id not in self.graph:
            return []
        return [self._result(value) for value in sorted(self.graph.predecessors(course_id))]

    def get_all_prerequisite_ancestors(self, course_id: str) -> list[GraphCourseResult]:
        if course_id not in self.graph:
            return []
        return [self._result(value) for value in sorted(nx.ancestors(self.graph, course_id))]

    def get_directly_unlocked_courses(self, course_id: str) -> list[GraphCourseResult]:
        if course_id not in self.graph:
            return []
        return [self._result(value) for value in sorted(self.graph.successors(course_id))]

    def get_all_unlocked_descendants(self, course_id: str) -> list[GraphCourseResult]:
        if course_id not in self.graph:
            return []
        return [self._result(value) for value in sorted(nx.descendants(self.graph, course_id))]

    def get_dependency_depth(self, course_id: str) -> int:
        """Return the longest prerequisite chain ending at the course, in edges."""
        if course_id not in self.graph:
            return 0
        ancestors = nx.ancestors(self.graph, course_id)
        subgraph = self.graph.subgraph(ancestors | {course_id})
        if not nx.is_directed_acyclic_graph(subgraph):
            return 0
        distances = nx.single_target_shortest_path_length(subgraph, course_id)
        return max(distances.values(), default=0)

    def get_critical_prerequisite_chain(self, course_id: str) -> list[GraphCourseResult]:
        if course_id not in self.graph:
            return []
        ancestors = nx.ancestors(self.graph, course_id)
        subgraph = self.graph.subgraph(ancestors | {course_id})
        if not nx.is_directed_acyclic_graph(subgraph):
            return []
        best: list[str] = []
        for source in sorted(node for node in subgraph if subgraph.in_degree(node) == 0):
            for path in nx.all_simple_paths(subgraph, source, course_id):
                if len(path) > len(best) or (len(path) == len(best) and path < best):
                    best = path
        return [self._result(value) for value in (best or [course_id])]

    def detect_cycles(self) -> list[list[str]]:
        canonical: list[list[str]] = []
        for cycle in nx.simple_cycles(self.graph):
            rotations = [cycle[index:] + cycle[:index] for index in range(len(cycle))]
            normalized = min(rotations)
            canonical.append([*normalized, normalized[0]])
        return sorted(canonical, key=lambda value: tuple(value))

    def has_path(self, source_course_id: str, target_course_id: str) -> bool:
        return (
            source_course_id in self.graph
            and target_course_id in self.graph
            and nx.has_path(self.graph, source_course_id, target_course_id)
        )


def build_prerequisite_graph(
    courses: list[Course],
    prerequisite_groups: list[PrerequisiteGroup],
    offerings: list[CourseOffering] | None = None,
    *,
    reject_cycles: bool = True,
) -> PrerequisiteGraph:
    graph = nx.DiGraph()
    offered_terms: dict[str, set[str]] = defaultdict(set)
    for offering in offerings or []:
        offered_terms[offering.course_id].add(offering.term_name.lower())

    for course in courses:
        graph.add_node(
            course.id,
            course_id=course.id,
            institution_id=course.institution_id,
            course_code=course.course_code,
            credits=course.credits,
            offered_terms=sorted(offered_terms[course.id]),
            source_ids=course.source_ids,
        )

    for group in prerequisite_groups:
        for condition in group.conditions:
            if (
                condition.condition_type != ConditionType.COURSE
                or not condition.prerequisite_course_id
            ):
                continue
            if condition.prerequisite_course_id not in graph or group.target_course_id not in graph:
                continue
            graph.add_edge(
                condition.prerequisite_course_id,
                group.target_course_id,
                group_id=group.id,
                group_type=group.group_type.value,
                minimum_grade_points=condition.minimum_grade_points,
                may_be_concurrent=condition.may_be_concurrent,
                condition_type=condition.condition_type.value,
                source_ids=sorted(set(group.source_ids + condition.source_ids)),
            )

    result = PrerequisiteGraph(graph)
    cycles = result.detect_cycles()
    if cycles and reject_cycles:
        raise PrerequisiteCycleError(cycles)
    return result


def get_direct_prerequisites(graph: PrerequisiteGraph, course_id: str) -> list[GraphCourseResult]:
    return graph.get_direct_prerequisites(course_id)


def get_all_prerequisite_ancestors(
    graph: PrerequisiteGraph, course_id: str
) -> list[GraphCourseResult]:
    return graph.get_all_prerequisite_ancestors(course_id)


def get_directly_unlocked_courses(
    graph: PrerequisiteGraph, course_id: str
) -> list[GraphCourseResult]:
    return graph.get_directly_unlocked_courses(course_id)


def get_all_unlocked_descendants(
    graph: PrerequisiteGraph, course_id: str
) -> list[GraphCourseResult]:
    return graph.get_all_unlocked_descendants(course_id)


def get_dependency_depth(graph: PrerequisiteGraph, course_id: str) -> int:
    return graph.get_dependency_depth(course_id)


def get_critical_prerequisite_chain(
    graph: PrerequisiteGraph, course_id: str
) -> list[GraphCourseResult]:
    return graph.get_critical_prerequisite_chain(course_id)


def detect_cycles(graph: PrerequisiteGraph) -> list[list[str]]:
    return graph.detect_cycles()
