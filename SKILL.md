---
name: reflexion-lab-project-guide
description: Use when working inside this Lab 16 Reflexion Agent project and you need a fast re-onboarding summary of the cleaned project structure, execution flow, runtime modes, implemented bonus features, and the role of each source file.
---

# Reflexion Lab Project Guide

## Mục đích

Đây là project lab xây dựng `Reflexion Agent` cho QA nhiều bước.

Project đã được dọn lại theo cấu trúc nộp bài gọn:
- `1` dataset chính: `data/hotpot_mini.json`
- `1` output chuẩn: `outputs/run`
- benchmark mock chạy end-to-end
- có sẵn runtime `openai_compat` cho API thật

## Đọc nhanh

Nếu cần nắm lại project nhanh, đọc theo thứ tự này:
1. `README.md`
2. `readmeProject.md`
3. `run_benchmark.py`
4. `src/reflexion_lab/agents.py`
5. `src/reflexion_lab/runtime.py`
6. `src/reflexion_lab/reporting.py`
7. `autograde.py`

## Cấu trúc chuẩn

Dataset chính:
- `data/hotpot_mini.json`

Output chuẩn:
- `outputs/run/react_runs.jsonl`
- `outputs/run/reflexion_runs.jsonl`
- `outputs/run/report.json`
- `outputs/run/report.md`

## Cách chạy chuẩn

```bash
python run_benchmark.py --dataset data/hotpot_mini.json --out-dir outputs/run
python autograde.py --report-path outputs/run/report.json
```

## Runtime modes

### `mock`
- Mặc định
- Không cần API key
- Dùng để debug flow và benchmark scaffold

### `openai_compat`
- Bật bằng `REFLEXION_RUNTIME=openai_compat`
- Gọi endpoint `/chat/completions`
- Dùng được với OpenAI-compatible API hoặc local server

## Bonus features đã cài

- `structured_evaluator`
- `reflection_memory`
- `benchmark_report_json`
- `mock_mode_for_autograding`
- `adaptive_max_attempts`
- `memory_compression`
- `plan_then_execute`

## Trạng thái hiện tại

Đã xác minh local:
- `python run_benchmark.py --dataset data/hotpot_mini.json --out-dir outputs/run` -> pass
- `python autograde.py --report-path outputs/run/report.json` -> `100/100`

## Vai trò file quan trọng

### `run_benchmark.py`
- Entry point benchmark

### `autograde.py`
- Chấm report JSON

### `src/reflexion_lab/agents.py`
- Logic ReAct và Reflexion

### `src/reflexion_lab/runtime.py`
- Runtime abstraction cho mock và API thật

### `src/reflexion_lab/mock_runtime.py`
- Runtime giả lập để test flow

### `src/reflexion_lab/reporting.py`
- Tạo summary và report JSON/Markdown

### `readmeProject.md`
- Tài liệu đọc hiểu chi tiết sau refactor
