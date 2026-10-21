from seo_demo.textutil import article_intro, find_forbidden_claims, slugify


def test_slugify_keeps_the_demo_keyword_shape():
    assert slugify("industrial gearbox motor", sep="_", max_len=24) == "industrial_gearbox_motor"
    title = "Industrial Gearbox Motor: Specifications, Selection & Buying Guide"
    assert slugify(title) == "industrial-gearbox-motor-specifications-selection-buying-guide"


def test_slugify_non_ascii_is_stable():
    first = slugify("工业减速电机")
    assert first == slugify("工业减速电机")
    assert first.startswith("kw-")
    assert slugify("工业减速电机", sep="_").startswith("kw_")


def test_forbidden_claims_do_not_match_inside_longer_tokens():
    assert find_forbidden_claims("Model No.10 is unguaranteed.", ["No.1", "guaranteed"]) == []
    assert find_forbidden_claims("We are No.1 and guaranteed.", ["No.1", "guaranteed"]) == [
        "No.1",
        "guaranteed",
    ]
    assert find_forbidden_claims("anything", ["", "  "]) == []


def test_article_intro_skips_brand_blockquote():
    text = """# Title

> **Why buyers work with us**: Example Manufacturer.

- IE3/IE4 full range

Selecting the right equipment starts with understanding your load profile.

## Specifications
"""
    intro = article_intro(text)
    assert intro.startswith("Selecting the right equipment")
    assert "Why buyers" not in intro
    assert "**" not in intro
