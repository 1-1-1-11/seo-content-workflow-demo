from seo_demo.dotenv import load_dotenv, parse_dotenv


def test_parse_dotenv_ignores_comments_and_strips_quotes():
    parsed = parse_dotenv(
        """
        # comment
        SEO_DEMO_KEYWORD="gear motor"
        export SEO_DEMO_MODE=mock
        not a pair
        1BAD=skip
        """
    )
    assert parsed == {"SEO_DEMO_KEYWORD": "gear motor", "SEO_DEMO_MODE": "mock"}


def test_load_dotenv_does_not_override_existing(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text('SEO_DEMO_KEYWORD=from-file\nSEO_DEMO_MODE=preview\n', encoding="utf-8")
    environ = {"SEO_DEMO_MODE": "mock"}
    applied = load_dotenv(env_file, environ)
    assert environ["SEO_DEMO_KEYWORD"] == "from-file"
    assert environ["SEO_DEMO_MODE"] == "mock"
    assert applied == {"SEO_DEMO_KEYWORD": "from-file"}
    assert load_dotenv(tmp_path / "missing.env", environ) == {}
