import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from unittest.mock import patch

import classifier

# --- Helper for color output ---
def color_text(text, color):
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "red": "\033[91m",
        "reset": "\033[0m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

# --- Test classify_question ---
@patch("classifier.query_gemini_llm")
def test_classify_question_club(mock_llm):
    mock_llm.return_value = "Club"
    result = classifier.classify_question("What does the club do?")
    print(color_text("test_classify_question_club passed", "green"))
    assert result == "Club"

@patch("classifier.query_gemini_llm")
def test_classify_question_website(mock_llm):
    mock_llm.return_value = "Website"
    result = classifier.classify_question("How do I reset my password?")
    print(color_text("test_classify_question_website passed", "yellow"))
    assert result == "Website"

@patch("classifier.query_gemini_llm")
def test_classify_question_unexpected(mock_llm):
    mock_llm.return_value = "This is about the club"
    result = classifier.classify_question("Tell me more")
    print(color_text("test_classify_question_unexpected passed", "blue"))
    assert result == "Club"

# --- Test classify_question_noid ---
@patch("classifier.query_gemini_llm")
def test_classify_question_noid_single(mock_llm):
    mock_llm.return_value = "single"
    result = classifier.classify_question_noid("Tell me about the Chess Club")
    print(color_text("test_classify_question_noid_single passed", "green"))
    assert result == "single"

@patch("classifier.query_gemini_llm")
def test_classify_question_noid_clublist(mock_llm):
    mock_llm.return_value = "clublist"
    result = classifier.classify_question_noid("What clubs are there?")
    print(color_text("test_classify_question_noid_clublist passed", "yellow"))
    assert result == "clublist"

@patch("classifier.query_gemini_llm")
def test_classify_question_noid_recommendation(mock_llm):
    mock_llm.return_value = "recommendation"
    result = classifier.classify_question_noid("What clubs would you recommend?")
    print(color_text("test_classify_question_noid_recommendation passed", "blue"))
    assert result == "recommendation"

@patch("classifier.query_gemini_llm")
def test_classify_question_noid_general(mock_llm):
    mock_llm.return_value = "general"
    result = classifier.classify_question_noid("Where is the library?")
    print(color_text("test_classify_question_noid_general passed", "red"))
    assert result == "general"

# --- Test classify_return_recommendation ---
def test_classify_return_recommendation_true():
    history = "User: What clubs do you recommend?\nAssistant: Could you tell me about your hobbies or interests so I can recommend clubs for you?"
    assert classifier.classify_return_recommendation(history) is True
    print(color_text("test_classify_return_recommendation_true passed", "green"))

def test_classify_return_recommendation_false():
    history = "User: Hello\nAssistant: Hi!"
    assert classifier.classify_return_recommendation(history) is False
    print(color_text("test_classify_return_recommendation_false passed", "yellow"))

# --- Test classify_return_all_clubs ---
def test_classify_return_all_clubs_true():
    history = "Assistant: Would you like to see all available clubs"
    assert classifier.classify_return_all_clubs(history) is True
    print(color_text("test_classify_return_all_clubs_true passed", "blue"))

def test_classify_return_all_clubs_false():
    history = "Assistant: Here are some clubs"
    assert classifier.classify_return_all_clubs(history) is False
    print(color_text("test_classify_return_all_clubs_false passed", "red"))

# --- Flow test: history contexted ---
def test_flow_history_contexted():
    history = (
        "User: What clubs do you recommend?\n"
        "Assistant: Could you tell me about your hobbies or interests so I can recommend clubs for you?\n"
        "User: I like music.\n"
        "Assistant: Based on your interests music, I recommend these clubs: Music Club."
    )
    assert classifier.classify_return_recommendation(history) is True
    assert classifier.classify_return_all_clubs(history) is False
    print(color_text("test_flow_history_contexted passed", "green"))