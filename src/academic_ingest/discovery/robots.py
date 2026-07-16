from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from academic_ingest.discovery.source_map import AccessDecision


@dataclass(frozen=True)
class RobotsRule:
    allowed: bool
    pattern: str

    def matches(self, path: str) -> bool:
        escaped = re.escape(self.pattern).replace(r"\*", ".*")
        expression = f"^{escaped[:-2]}$" if escaped.endswith(r"\$") else f"^{escaped}"
        return re.match(expression, path) is not None

    @property
    def specificity(self) -> int:
        return len(self.pattern.replace("*", "").removesuffix("$"))


@dataclass(frozen=True)
class RobotsPolicy:
    robots_url: str
    user_agent: str
    rules: tuple[RobotsRule, ...]

    @classmethod
    def from_text(cls, robots_url: str, text: str, *, user_agent: str) -> RobotsPolicy:
        groups: list[tuple[list[str], list[RobotsRule]]] = []
        agents: list[str] = []
        rules: list[RobotsRule] = []
        for raw_line in [*text.splitlines(), ""]:
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                if agents:
                    groups.append((agents, rules))
                agents, rules = [], []
                continue
            key, separator, value = line.partition(":")
            if not separator:
                continue
            key = key.strip().lower()
            value = value.strip()
            if key == "user-agent":
                if rules:
                    groups.append((agents, rules))
                    agents, rules = [], []
                agents.append(value.lower())
            elif key in {"allow", "disallow"} and agents and value:
                rules.append(RobotsRule(allowed=key == "allow", pattern=value))

        product = user_agent.lower()
        matching_groups: list[tuple[int, list[RobotsRule]]] = []
        for group_agents, group_rules in groups:
            matches = [
                len(agent) for agent in group_agents if agent == "*" or product.startswith(agent)
            ]
            if matches:
                matching_groups.append((max(matches), group_rules))
        if not matching_groups:
            selected_rules: tuple[RobotsRule, ...] = ()
        else:
            highest_specificity = max(item[0] for item in matching_groups)
            selected_rules = tuple(
                rule
                for specificity, group_rules in matching_groups
                if specificity == highest_specificity
                for rule in group_rules
            )
        return cls(robots_url=robots_url, user_agent=user_agent, rules=selected_rules)

    def evaluate(self, url: str) -> AccessDecision:
        robots = urlsplit(self.robots_url)
        candidate = urlsplit(url)
        if (candidate.scheme.lower(), candidate.hostname, candidate.port) != (
            robots.scheme.lower(),
            robots.hostname,
            robots.port,
        ):
            return AccessDecision(False, "Robots policy may only evaluate its own origin")
        path = candidate.path or "/"
        if candidate.query:
            path = f"{path}?{candidate.query}"
        matching_rules = [rule for rule in self.rules if rule.matches(path)]
        if not matching_rules:
            return AccessDecision(True, "robots.txt has no matching disallow rule")
        highest_specificity = max(rule.specificity for rule in matching_rules)
        allowed = any(
            rule.allowed for rule in matching_rules if rule.specificity == highest_specificity
        )
        if allowed:
            return AccessDecision(True, "robots.txt explicitly allows this URL")
        return AccessDecision(False, "robots.txt disallows this URL")
