from __future__ import annotations
from .schemas import QAExample, JudgeResult, ReflectionEntry
from .utils import normalize_answer

FIRST_ATTEMPT_WRONG = {
    "hp2": "London",
    "hp4": "Atlantic Ocean",
    "hp6": "Red Sea",
    "hp8": "Andes",
    "hp100_035": "Rome",
    "hp100_036": "Pacific Ocean",
    "hp100_039": "Red Sea",
    "hp100_045": "Indian Ocean",
    "hp100_051": "Giza",
    "hp100_059": "London",
    "hp100_068": "Red Sea",
    "hp100_070": "Spanish",
    "hp100_073": "Lima",
    "hp100_077": "Madrid",
    "hp100_081": "Mexico City",
    "hp100_089": "Tonle Sap",
    "hp100_093": "Ankara",
}
FAILURE_MODE_BY_QID = {
    "hp2": "incomplete_multi_hop",
    "hp4": "wrong_final_answer",
    "hp6": "entity_drift",
    "hp8": "entity_drift",
    "hp100_035": "incomplete_multi_hop",
    "hp100_036": "wrong_final_answer",
    "hp100_039": "entity_drift",
    "hp100_045": "wrong_final_answer",
    "hp100_051": "incomplete_multi_hop",
    "hp100_059": "incomplete_multi_hop",
    "hp100_068": "entity_drift",
    "hp100_070": "incomplete_multi_hop",
    "hp100_073": "incomplete_multi_hop",
    "hp100_077": "incomplete_multi_hop",
    "hp100_081": "incomplete_multi_hop",
    "hp100_089": "wrong_final_answer",
    "hp100_093": "incomplete_multi_hop",
}

def actor_answer(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> str:
    if example.qid not in FIRST_ATTEMPT_WRONG:
        return example.gold_answer
    if agent_type == "react":
        return FIRST_ATTEMPT_WRONG[example.qid]
    if attempt_id == 1 and not reflection_memory:
        return FIRST_ATTEMPT_WRONG[example.qid]
    return example.gold_answer

def evaluator(example: QAExample, answer: str) -> JudgeResult:
    if normalize_answer(example.gold_answer) == normalize_answer(answer):
        return JudgeResult(score=1, reason="Final answer matches the gold answer after normalization.")
    if normalize_answer(answer) == "london":
        return JudgeResult(score=0, reason="The answer stopped at the birthplace city and never completed the second hop to the river.", missing_evidence=["Need to identify the river that flows through London."], spurious_claims=[])
    return JudgeResult(score=0, reason="The final answer selected the wrong second-hop entity.", missing_evidence=["Need to ground the answer in the second paragraph."], spurious_claims=[answer])

def reflector(example: QAExample, attempt_id: int, judge: JudgeResult) -> ReflectionEntry:
    strategy = "Do the second hop explicitly: intermediate entity -> supporting evidence -> final answer." if "hop" in judge.reason.lower() else "Verify the final entity against the supporting context before answering."
    focus_points = judge.missing_evidence or ["Check the second supporting fact before giving the final answer."]
    return ReflectionEntry(
        attempt_id=attempt_id,
        failure_reason=judge.reason,
        lesson="A partial first-hop answer is not enough; the final answer must complete all required hops and stay grounded in context.",
        next_strategy=strategy,
        focus_points=focus_points,
    )
