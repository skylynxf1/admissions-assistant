"""Tests for pathway registry."""

import pytest

from academic_ingest.pathways.registry import (
    UnknownPathwayError,
    get_pathway,
    load_pathways,
)


def test_load_pathways_returns_both_keys() -> None:
    """Test that load_pathways() returns both pathway keys."""
    pathways = load_pathways()
    assert "bellevue-college:uw-seattle" in pathways
    assert "seattle-university:uw-seattle" in pathways


def test_get_bellevue_to_uw_pathway() -> None:
    """Test bellevue-college:uw-seattle pathway."""
    pathways = load_pathways()
    pathway = get_pathway("bellevue-college:uw-seattle", pathways)
    assert pathway.destination_campus == "Seattle"
    assert pathway.source_institution_id == "bellevue-college"
    assert "transfer_outcomes" in pathway.capabilities


def test_get_seattle_university_to_uw_pathway() -> None:
    """Test seattle-university:uw-seattle pathway."""
    pathways = load_pathways()
    pathway = get_pathway("seattle-university:uw-seattle", pathways)
    assert pathway.source_institution_id == "seattle-university"


def test_get_pathway_unknown_raises_error() -> None:
    """Test that get_pathway raises UnknownPathwayError for unknown pathway."""
    pathways = load_pathways()
    with pytest.raises(UnknownPathwayError):
        get_pathway("nope:uw-seattle", pathways)


def test_get_pathway_auto_loads_when_no_dict_passed() -> None:
    """Test that get_pathway auto-loads pathways when no dict is passed."""
    pathway = get_pathway("bellevue-college:uw-seattle")
    assert pathway.destination_campus == "Seattle"
    assert pathway.source_institution_id == "bellevue-college"
