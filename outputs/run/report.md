# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_mini.json
- Mode: mock
- Records: 200
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.87 | 1.0 | 0.13 |
| Avg attempts | 1 | 1.13 | 0.13 |
| Avg token estimate | 390.69 | 472.33 | 81.64 |
| Avg latency (ms) | 178 | 237.13 | 59.13 |

## Failure modes
```json
{
  "react": {
    "none": 87,
    "incomplete_multi_hop": 8,
    "wrong_final_answer": 3,
    "entity_drift": 2
  },
  "reflexion": {
    "none": 100
  },
  "overall": {
    "none": 187,
    "incomplete_multi_hop": 8,
    "wrong_final_answer": 3,
    "entity_drift": 2
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding
- adaptive_max_attempts
- memory_compression
- plan_then_execute

## Discussion
Reflexion outperforms a single-pass ReAct baseline when the first attempt fails because it stops one hop too early or commits to the wrong entity after an incomplete chain of evidence. The implemented scaffold now makes that loop explicit through a structured evaluator, persistent reflection memory, adaptive attempt budgets by difficulty, compressed memory to avoid unbounded context growth, and a plan-then-execute step that nudges the actor to verify the second hop before answering. These gains come with a predictable tradeoff: more total calls, higher token usage, and higher latency. In a real benchmark, the most useful follow-up analysis would compare which failure modes remain after reflection, whether compressed memory preserves the right lessons, and whether evaluator quality becomes the bottleneck once the actor improves.
