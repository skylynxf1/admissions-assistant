def test_package_exposes_version() -> None:
    import academic_ingest

    assert academic_ingest.__version__ == "0.1.0"
