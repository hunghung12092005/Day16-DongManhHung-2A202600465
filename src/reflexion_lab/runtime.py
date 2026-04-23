from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from .mock_runtime import actor_answer as mock_actor_answer
from .mock_runtime import evaluator as mock_evaluator
from .mock_runtime import reflector as mock_reflector
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM
from .schemas import JudgeResult, QAExample, ReflectionEntry


@dataclass
class CallMetrics:
    tokens: int
    latency_ms: int


@dataclass
class ActorCall:
    answer: str
    metrics: CallMetrics


@dataclass
class EvaluatorCall:
    judge: JudgeResult
    metrics: CallMetrics


@dataclass
class ReflectorCall:
    reflection: ReflectionEntry
    memory_text: str
    metrics: CallMetrics


def _context_to_text(example: QAExample) -> str:
    return "\n".join(
        f"[{idx}] {chunk.title}: {chunk.text}" for idx, chunk in enumerate(example.context, start=1)
    )


def _estimate_text_tokens(*parts: str) -> int:
    total_chars = sum(len(part) for part in parts if part)
    return max(1, total_chars // 4)


def _extract_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"Model response does not contain a JSON object: {text}")
    return json.loads(text[start : end + 1])


class BaseRuntime:
    mode = "mock"

    def actor_answer(
        self,
        example: QAExample,
        attempt_id: int,
        agent_type: str,
        reflection_memory: list[str],
        plan: str | None,
    ) -> ActorCall:
        raise NotImplementedError

    def evaluate(self, example: QAExample, answer: str) -> EvaluatorCall:
        raise NotImplementedError

    def reflect(
        self,
        example: QAExample,
        attempt_id: int,
        judge: JudgeResult,
        reflection_memory: list[str],
    ) -> ReflectorCall:
        raise NotImplementedError


class MockRuntime(BaseRuntime):
    mode = "mock"

    def actor_answer(
        self,
        example: QAExample,
        attempt_id: int,
        agent_type: str,
        reflection_memory: list[str],
        plan: str | None,
    ) -> ActorCall:
        answer = mock_actor_answer(example, attempt_id, agent_type, reflection_memory)
        tokens = 160 + (attempt_id * 28) + (18 * len(reflection_memory)) + _estimate_text_tokens(answer, plan or "")
        latency_ms = 90 + (attempt_id * 18) + (20 if agent_type == "reflexion" else 0)
        return ActorCall(answer=answer, metrics=CallMetrics(tokens=tokens, latency_ms=latency_ms))

    def evaluate(self, example: QAExample, answer: str) -> EvaluatorCall:
        judge = mock_evaluator(example, answer)
        tokens = 120 + _estimate_text_tokens(example.question, answer, judge.reason)
        latency_ms = 70
        return EvaluatorCall(judge=judge, metrics=CallMetrics(tokens=tokens, latency_ms=latency_ms))

    def reflect(
        self,
        example: QAExample,
        attempt_id: int,
        judge: JudgeResult,
        reflection_memory: list[str],
    ) -> ReflectorCall:
        reflection = mock_reflector(example, attempt_id, judge)
        memory_text = f"Lesson: {reflection.lesson} Strategy: {reflection.next_strategy}"
        tokens = 130 + (15 * len(reflection_memory)) + _estimate_text_tokens(memory_text)
        latency_ms = 85
        return ReflectorCall(
            reflection=reflection,
            memory_text=memory_text,
            metrics=CallMetrics(tokens=tokens, latency_ms=latency_ms),
        )


class OpenAICompatRuntime(BaseRuntime):
    mode = "openai_compat"

    def __init__(self) -> None:
        self.base_url = os.getenv("REFLEXION_API_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.api_key = os.getenv("REFLEXION_API_KEY") or os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("REFLEXION_MODEL", "gpt-4o-mini")
        self.timeout = float(os.getenv("REFLEXION_API_TIMEOUT", "60"))

    def _chat(self, messages: list[dict[str, str]], temperature: float = 0.0) -> tuple[str, CallMetrics]:
        payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": messages,
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            data=body,
            headers=headers,
            method="POST",
        )

        started = time.perf_counter()
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                response_body = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM request failed with status {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Unable to reach LLM endpoint at {self.base_url}: {exc}") from exc
        latency_ms = int((time.perf_counter() - started) * 1000)

        payload = json.loads(response_body)
        choice = payload["choices"][0]["message"]
        content = choice.get("content", "")
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))

        usage = payload.get("usage", {})
        total_tokens = (
            usage.get("total_tokens")
            or usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
            or _estimate_text_tokens(json.dumps(messages), content)
        )
        return content.strip(), CallMetrics(tokens=total_tokens, latency_ms=latency_ms)

    def actor_answer(
        self,
        example: QAExample,
        attempt_id: int,
        agent_type: str,
        reflection_memory: list[str],
        plan: str | None,
    ) -> ActorCall:
        reflection_block = "\n".join(f"- {item}" for item in reflection_memory) or "- None"
        plan_block = plan or "No explicit plan."
        user_prompt = f"""Question: {example.question}

Context:
{_context_to_text(example)}

Attempt: {attempt_id}
Agent type: {agent_type}
Plan:
{plan_block}

Reflection memory:
{reflection_block}

Return only the final answer text with no extra commentary."""
        content, metrics = self._chat(
            [
                {"role": "system", "content": ACTOR_SYSTEM},
                {"role": "user", "content": user_prompt},
            ]
        )
        return ActorCall(answer=content.strip(), metrics=metrics)

    def evaluate(self, example: QAExample, answer: str) -> EvaluatorCall:
        user_prompt = f"""Question: {example.question}
Gold answer: {example.gold_answer}
Candidate answer: {answer}
Context:
{_context_to_text(example)}

Return JSON with keys: score, reason, missing_evidence, spurious_claims."""
        content, metrics = self._chat(
            [
                {"role": "system", "content": EVALUATOR_SYSTEM},
                {"role": "user", "content": user_prompt},
            ]
        )
        judge = JudgeResult.model_validate(_extract_json_object(content))
        return EvaluatorCall(judge=judge, metrics=metrics)

    def reflect(
        self,
        example: QAExample,
        attempt_id: int,
        judge: JudgeResult,
        reflection_memory: list[str],
    ) -> ReflectorCall:
        prior_memory = "\n".join(f"- {item}" for item in reflection_memory) or "- None"
        user_prompt = f"""Question: {example.question}
Context:
{_context_to_text(example)}
Attempt id: {attempt_id}
Failure reason: {judge.reason}
Missing evidence: {judge.missing_evidence}
Spurious claims: {judge.spurious_claims}
Prior reflection memory:
{prior_memory}

Return JSON with keys: attempt_id, failure_reason, lesson, next_strategy, focus_points."""
        content, metrics = self._chat(
            [
                {"role": "system", "content": REFLECTOR_SYSTEM},
                {"role": "user", "content": user_prompt},
            ]
        )
        reflection = ReflectionEntry.model_validate(_extract_json_object(content))
        memory_text = f"Lesson: {reflection.lesson} Strategy: {reflection.next_strategy}"
        return ReflectorCall(reflection=reflection, memory_text=memory_text, metrics=metrics)


def get_runtime() -> BaseRuntime:
    mode = os.getenv("REFLEXION_RUNTIME", "mock").strip().lower()
    if mode == "openai_compat":
        return OpenAICompatRuntime()
    return MockRuntime()
