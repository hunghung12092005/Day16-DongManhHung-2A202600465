from src.reflexion_lab.agents import ReActAgent, ReflexionAgent
from src.reflexion_lab.reporting import build_report
from src.reflexion_lab.schemas import QAExample
from src.reflexion_lab.utils import normalize_answer


def test_normalize_answer():
    assert normalize_answer("Oxford University!") == "oxford university"


def test_reflexion_agent_generates_reflection_and_recovers():
    example = QAExample.model_validate(
        {
            "qid": "hp2",
            "difficulty": "medium",
            "question": "What river flows through the city where Ada Lovelace was born?",
            "gold_answer": "River Thames",
            "context": [
                {"title": "Ada Lovelace", "text": "Ada Lovelace was born in London, England."},
                {"title": "London", "text": "London is crossed by the River Thames."},
            ],
        }
    )

    record = ReflexionAgent(max_attempts=3).run(example)

    assert record.is_correct is True
    assert record.attempts == 2
    assert len(record.reflections) == 1
    assert record.traces[0].reflection is not None
    assert record.traces[1].reflection_memory_snapshot


def test_react_agent_stops_after_single_attempt():
    example = QAExample.model_validate(
        {
            "qid": "hp2",
            "difficulty": "medium",
            "question": "What river flows through the city where Ada Lovelace was born?",
            "gold_answer": "River Thames",
            "context": [
                {"title": "Ada Lovelace", "text": "Ada Lovelace was born in London, England."},
                {"title": "London", "text": "London is crossed by the River Thames."},
            ],
        }
    )

    record = ReActAgent().run(example)

    assert record.is_correct is False
    assert record.attempts == 1
    assert record.failure_mode == "incomplete_multi_hop"


def test_build_report_includes_bonus_extensions():
    example = QAExample.model_validate(
        {
            "qid": "hp1",
            "difficulty": "easy",
            "question": "Which university did the author of The Hobbit teach at?",
            "gold_answer": "Oxford University",
            "context": [
                {
                    "title": "J. R. R. Tolkien",
                    "text": "J. R. R. Tolkien wrote The Hobbit and was a professor at Oxford University.",
                },
                {
                    "title": "Oxford University",
                    "text": "Oxford University is a collegiate research university in Oxford, England.",
                },
            ],
        }
    )

    records = [ReActAgent().run(example), ReflexionAgent(max_attempts=3).run(example)]
    report = build_report(records, dataset_name="mini.json", mode="mock")

    assert "adaptive_max_attempts" in report.extensions
    assert "memory_compression" in report.extensions
    assert "plan_then_execute" in report.extensions
