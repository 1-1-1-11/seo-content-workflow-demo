from pathlib import Path

import pytest

from seo_demo.profile import ProfileError, load_profile


def test_example_profile_loads():
    profile = load_profile(Path("config/prompt_profile.example.yaml"))
    assert "guaranteed" in profile.forbidden_claims
    assert profile.differentiators


def test_missing_empty_and_invalid_profiles(tmp_path):
    with pytest.raises(ProfileError):
        load_profile(tmp_path / "missing.yaml")

    empty = tmp_path / "empty.yaml"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ProfileError):
        load_profile(empty)

    listing = tmp_path / "list.yaml"
    listing.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ProfileError):
        load_profile(listing)

    bad = tmp_path / "bad.yaml"
    bad.write_text("company_kb:\n  differentiators: one string\n", encoding="utf-8")
    with pytest.raises(ProfileError):
        load_profile(bad)
