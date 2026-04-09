import pytest
import json
from bibliocli.infrastructure.services.heuristic_formatter import HeuristicTextFormatter

@pytest.fixture
def formatter():
    return HeuristicTextFormatter()

def test_heuristic_formatter_identifies_toc(formatter):
    raw_text = """
    ALICE'S ADVENTURES IN WONDERLAND
    
    CONTENTS
    
    CHAPTER I. DOWN THE RABBIT-HOLE
    CHAPTER II. THE POOL OF TEARS
    CHAPTER III. A CAUCUS-RACE AND A LONG TALE
    
    CHAPTER I.
    DOWN THE RABBIT-HOLE
    Alice was beginning to get very tired...
    """
    
    res_json = formatter.format_text(raw_text, "test", title="Alice", author="Lewis", only_toc=True)
    data = json.loads(res_json)
    
    assert "detected_toc" in data
    assert len(data["detected_toc"]) >= 3
    assert data["detected_toc"][0]["title"] == "DOWN THE RABBIT-HOLE"

def test_heuristic_formatter_removes_scene_separators(formatter):
    raw_text = "CHAPTER I\n\nSome text.\n\n* * * * *\n\nMore text."
    res_json = formatter.format_text(raw_text, "test")
    data = json.loads(res_json)
    
    combined = " ".join(data["chapters"][0]["paragraphs"])
    assert "***" in combined
    assert "* * * * *" not in combined
