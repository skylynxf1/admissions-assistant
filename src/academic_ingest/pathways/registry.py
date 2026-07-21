"""Pathway registry for managing transfer pathways."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


class UnknownPathwayError(KeyError):
    """Raised when a pathway key is not found in the registry."""


@dataclass(frozen=True)
class Pathway:
    """A transfer pathway between institutions."""

    key: str
    source_institution_id: str
    destination_institution_id: str
    destination_campus: str
    capabilities: frozenset[str]


def load_pathways(path: Path | str = Path("config/pathways/pathways.yaml")) -> dict[str, Pathway]:
    """Load pathways from a YAML file.

    Args:
        path: Path to the pathways YAML file. Defaults to config/pathways/pathways.yaml.

    Returns:
        A dictionary mapping pathway keys to Pathway objects.

    Raises:
        ValueError: If the YAML is invalid or missing required fields.
    """
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise ValueError(f"pathway configuration must be a mapping: {config_path}")

    pathways_list = raw.get("pathways", [])
    if not isinstance(pathways_list, list):
        raise ValueError("'pathways' must be a list")

    pathways: dict[str, Pathway] = {}
    for pathway_data in pathways_list:
        if not isinstance(pathway_data, dict):
            raise ValueError("each pathway must be a mapping")

        pathway = Pathway(
            key=pathway_data["key"],
            source_institution_id=pathway_data["source_institution_id"],
            destination_institution_id=pathway_data["destination_institution_id"],
            destination_campus=pathway_data["destination_campus"],
            capabilities=frozenset(pathway_data.get("capabilities", [])),
        )
        pathways[pathway.key] = pathway

    return pathways


def get_pathway(key: str, pathways: dict[str, Pathway] | None = None) -> Pathway:
    """Get a pathway by key.

    Args:
        key: The pathway key to look up.
        pathways: Optional pre-loaded pathways dictionary. If None, load_pathways() is called.

    Returns:
        The Pathway object for the given key.

    Raises:
        UnknownPathwayError: If the pathway key is not found.
    """
    if pathways is None:
        pathways = load_pathways()

    if key not in pathways:
        raise UnknownPathwayError(key)

    return pathways[key]
