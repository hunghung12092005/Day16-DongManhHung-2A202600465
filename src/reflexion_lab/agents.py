from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
from .mock_runtime import FAILURE_MODE_BY_QID
from .runtime import get_runtime
from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord

@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    max_attempts: int = 1
    adaptive_max_attempts: bool = True
    memory_compression: bool = True
    memory_window: int = 2
    plan_then_execute: bool = True

    def _resolve_max_attempts(self, example: QAExample) -> int:
        if self.agent_type != "reflexion" or not self.adaptive_max_attempts:
            return self.max_attempts
        difficulty_budget = {"easy": 2, "medium": 3, "hard": 4}
        return max(1, max(self.max_attempts, difficulty_budget[example.difficulty]))

    def _build_plan(self, example: QAExample) -> str | None:
        if not self.plan_then_execute:
            return None
        titles = ", ".join(chunk.title for chunk in example.context)
        return (
            "1. Find the bridge entity named in the question.\n"
            f"2. Ground the reasoning in these context nodes: {titles}.\n"
            "3. Verify the second-hop fact before committing to the final answer."
        )

    def _memory_text(self, reflection: ReflectionEntry) -> str:
        focus = "; ".join(reflection.focus_points) if reflection.focus_points else "verify the missing hop"
        return f"Lesson: {reflection.lesson} Strategy: {reflection.next_strategy} Focus: {focus}"

    def _compress_memory(self, reflection_memory: list[str]) -> list[str]:
        if not self.memory_compression or len(reflection_memory) <= self.memory_window:
            return reflection_memory
        retained = reflection_memory[-(self.memory_window - 1) :] if self.memory_window > 1 else []
        older = reflection_memory[: len(reflection_memory) - len(retained)]
        compressed = "Compressed memory: " + " | ".join(older)
        return [compressed, *retained]

    def _infer_failure_mode(self, example: QAExample, traces: list[AttemptTrace], final_score: int) -> str:
        if final_score == 1:
            return "none"
        answers = [trace.answer for trace in traces]
        if len(answers) >= 2 and answers[-1] == answers[-2]:
            return "looping"
        if self.agent_type == "reflexion" and len(traces) >= 2 and answers[-1] != answers[0]:
            return "reflection_overfit"
        return FAILURE_MODE_BY_QID.get(example.qid, "wrong_final_answer")

    def run(self, example: QAExample) -> RunRecord:
        runtime = get_runtime()
        reflection_memory: list[str] = []
        reflections: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0
        effective_max_attempts = self._resolve_max_attempts(example)
        plan = self._build_plan(example)

        for attempt_id in range(1, effective_max_attempts + 1):
            actor_call = runtime.actor_answer(example, attempt_id, self.agent_type, reflection_memory, plan)
            judge_call = runtime.evaluate(example, actor_call.answer)
            token_estimate = actor_call.metrics.tokens + judge_call.metrics.tokens
            latency_ms = actor_call.metrics.latency_ms + judge_call.metrics.latency_ms
            trace = AttemptTrace(
                attempt_id=attempt_id,
                answer=actor_call.answer,
                score=judge_call.judge.score,
                reason=judge_call.judge.reason,
                plan=plan,
                reflection_memory_snapshot=list(reflection_memory),
                token_estimate=token_estimate,
                latency_ms=latency_ms,
            )
            final_answer = actor_call.answer
            final_score = judge_call.judge.score
            if judge_call.judge.score == 1:
                traces.append(trace)
                break

            if self.agent_type == "reflexion" and attempt_id < effective_max_attempts:
                reflection_call = runtime.reflect(example, attempt_id, judge_call.judge, reflection_memory)
                reflection = reflection_call.reflection
                reflections.append(reflection)
                trace.reflection = reflection
                token_estimate += reflection_call.metrics.tokens
                latency_ms += reflection_call.metrics.latency_ms
                trace.token_estimate = token_estimate
                trace.latency_ms = latency_ms
                reflection_memory.append(reflection_call.memory_text or self._memory_text(reflection))
                reflection_memory = self._compress_memory(reflection_memory)
                if reflection_memory and reflection_memory[0].startswith("Compressed memory:"):
                    reflection.compressed_memory = reflection_memory[0]

            traces.append(trace)

        total_tokens = sum(t.token_estimate for t in traces)
        total_latency = sum(t.latency_ms for t in traces)
        failure_mode = self._infer_failure_mode(example, traces, final_score)
        return RunRecord(
            qid=example.qid,
            question=example.question,
            gold_answer=example.gold_answer,
            agent_type=self.agent_type,
            predicted_answer=final_answer,
            is_correct=bool(final_score),
            attempts=len(traces),
            token_estimate=total_tokens,
            latency_ms=total_latency,
            failure_mode=failure_mode,
            reflections=reflections,
            traces=traces,
        )

class ReActAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_type="react",
            max_attempts=1,
            adaptive_max_attempts=False,
            memory_compression=False,
        )

class ReflexionAgent(BaseAgent):
    def __init__(self, max_attempts: int = 3) -> None:
        super().__init__(agent_type="reflexion", max_attempts=max_attempts)
