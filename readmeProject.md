# Readme Project

## 1. Mục tiêu của file này

File này không chỉ tóm tắt project, mà còn giải thích code theo luồng chạy thật.

Mục tiêu là để khi bạn mở lại repo sau vài ngày, bạn có thể trả lời nhanh các câu hỏi:
- project chạy từ đâu
- file nào là trung tâm
- ReAct khác Reflexion ở đâu
- mock và API thật được chọn như thế nào
- report được tạo ở đâu
- nếu cần sửa hành vi thì phải sửa file nào

## 2. Bức tranh tổng thể

Project này là một scaffold cho bài lab `Reflexion Agent`.

Ý tưởng chính:
- `ReActAgent` là baseline: trả lời một lần rồi dừng.
- `ReflexionAgent` là bản nâng cấp: nếu sai thì tự đánh giá, rút kinh nghiệm, rồi thử lại.

Project hiện có hai chế độ chạy:
- `mock`: dùng dữ liệu giả lập để test flow
- `openai_compat`: gọi API tương thích OpenAI để dùng model thật

## 3. Cấu trúc quan trọng nhất của repo

### Dataset chính

- `data/hotpot_mini.json`

Ghi chú:
- tên là `mini` để giữ tương thích với scaffold cũ
- nhưng nội dung hiện đã là bộ `100` câu benchmark

### Output chính

- `outputs/run/react_runs.jsonl`
- `outputs/run/reflexion_runs.jsonl`
- `outputs/run/report.json`
- `outputs/run/report.md`

### Source code chính

- `run_benchmark.py`
- `autograde.py`
- `src/reflexion_lab/agents.py`
- `src/reflexion_lab/runtime.py`
- `src/reflexion_lab/mock_runtime.py`
- `src/reflexion_lab/reporting.py`
- `src/reflexion_lab/schemas.py`
- `src/reflexion_lab/prompts.py`
- `src/reflexion_lab/utils.py`

## 4. Cách chạy project

### Chạy benchmark mặc định

```bash
python run_benchmark.py
```

Lệnh này dùng mặc định:
- dataset: `data/hotpot_mini.json`
- output: `outputs/run`

### Chạy autograde

```bash
python autograde.py
```

Lệnh này mặc định đọc:
- `outputs/run/report.json`

### Chạy benchmark với tham số tường minh

```bash
python run_benchmark.py --dataset data/hotpot_mini.json --out-dir outputs/run
python autograde.py --report-path outputs/run/report.json
```

### Chạy test

Nếu `pytest` đã có trong `.venv`:

```bash
.venv/bin/pytest -q
```

## 5. Luồng chạy từ đầu đến cuối

```text
run_benchmark.py
  -> load_dataset() trong utils.py
  -> get_runtime() trong runtime.py
  -> tạo ReActAgent và ReflexionAgent
  -> agent.run(example) trong agents.py
       -> runtime.actor_answer(...)
       -> runtime.evaluate(...)
       -> nếu reflexion và sai:
            -> runtime.reflect(...)
            -> cập nhật reflection_memory
       -> tạo RunRecord
  -> save_jsonl()
  -> build_report() trong reporting.py
  -> save_report() trong reporting.py
  -> outputs/run/report.json + report.md

autograde.py
  -> đọc outputs/run/report.json
  -> chấm điểm theo schema và summary
```

## 6. File nào là trung tâm nhất

Nếu chỉ chọn 3 file quan trọng nhất để đọc trước, hãy đọc:

1. `run_benchmark.py`
2. `src/reflexion_lab/agents.py`
3. `src/reflexion_lab/runtime.py`

Lý do:
- `run_benchmark.py` là entry point
- `agents.py` là nơi hành vi ReAct và Reflexion thực sự diễn ra
- `runtime.py` quyết định dùng mock hay API thật

## 7. Giải thích từng file theo kiểu đọc code

### 7.1 `run_benchmark.py`

File: [run_benchmark.py](/home/hung/code/AI_CODE_VIN/lab/Day15/Day16-DongManhHung-2A202600465/run_benchmark.py)

Đây là entry point chính của benchmark.

#### Đoạn import đầu file

- `ReActAgent`, `ReflexionAgent`
  - import agent để chạy benchmark
- `build_report`, `save_report`
  - import logic tạo báo cáo
- `get_runtime`
  - đọc mode hiện tại là mock hay API thật
- `load_dataset`, `save_jsonl`
  - đọc dataset và ghi file log kết quả

#### `app = typer.Typer(...)`

Mục đích:
- tạo CLI command bằng `typer`
- nên bạn mới có thể chạy `python run_benchmark.py --dataset ...`

#### `main(...)`

Đây là hàm benchmark thật sự.

Các tham số:
- `dataset`
  - file JSON dataset
- `out_dir`
  - thư mục chứa output
- `reflexion_attempts`
  - số lần tối đa Reflexion được thử

#### `examples = load_dataset(dataset)`

Đoạn này đọc toàn bộ dataset vào memory và ép từng dòng thành `QAExample`.

#### `runtime = get_runtime()`

Đoạn này chỉ lấy mode đang chạy để sau đó ghi vào report.

Lưu ý:
- `run_benchmark.py` không trực tiếp gọi API
- agent bên trong sẽ tự gọi `get_runtime()` lại khi chạy từng example

#### `react = ReActAgent()` và `reflexion = ReflexionAgent(...)`

Đây là chỗ tạo 2 hệ benchmark:
- baseline `react`
- bản nâng cấp `reflexion`

#### `react_records = [react.run(...)]`

Đoạn này chạy toàn bộ dataset với ReAct.

#### `reflexion_records = [reflexion.run(...)]`

Đoạn này chạy toàn bộ dataset với Reflexion.

#### `save_jsonl(...)`

Mục đích:
- ghi log thô của từng câu hỏi ra file
- sau này dễ debug hơn nếu report tổng hợp có vấn đề

#### `build_report(...)`

Mục đích:
- gộp toàn bộ run records thành report cuối cùng
- summary trong terminal cũng được lấy từ đây

#### `save_report(...)`

Mục đích:
- ghi `report.json`
- ghi `report.md`

#### Kết luận về file này

Đây là file orchestration:
- nó điều phối luồng
- nhưng không chứa logic reasoning sâu

Nếu muốn đổi thuật toán agent, đừng sửa ở đây trước.

### 7.2 `src/reflexion_lab/agents.py`

File: [agents.py](/home/hung/code/AI_CODE_VIN/lab/Day15/Day16-DongManhHung-2A202600465/src/reflexion_lab/agents.py)

Đây là file trung tâm nhất của project.

Nó chứa:
- lớp nền `BaseAgent`
- lớp con `ReActAgent`
- lớp con `ReflexionAgent`

#### `BaseAgent` là gì

`BaseAgent` là nơi gom toàn bộ logic chung:
- số lần thử
- plan
- reflection memory
- loop attempt
- trace
- tổng hợp kết quả cuối

#### `agent_type`

Giá trị có thể là:
- `react`
- `reflexion`

Nó là công tắc để một số nhánh logic biết đang ở chế độ nào.

#### `max_attempts`

Ý nghĩa:
- số lần thử tối đa

Với `react`:
- gần như luôn là `1`

Với `reflexion`:
- có thể lớn hơn `1`

#### `adaptive_max_attempts`

Ý nghĩa:
- nếu bật, số lần thử tối đa sẽ tăng theo độ khó câu hỏi

Đoạn code `_resolve_max_attempts(...)`:
- nếu không phải reflexion -> trả về `max_attempts`
- nếu là reflexion -> map:
  - `easy -> 2`
  - `medium -> 3`
  - `hard -> 4`

Mục đích:
- câu khó được phép thử nhiều hơn

#### `plan_then_execute`

Đoạn `_build_plan(...)`:
- nhìn vào `example.context`
- dựng một plan ngắn 3 bước

Plan này không trực tiếp trả lời câu hỏi.
Nó chỉ đóng vai trò:
- nhắc actor suy luận theo từng bước
- tăng tính có cấu trúc trước khi trả lời

#### `reflection_memory`

Đoạn `_memory_text(...)`:
- biến `ReflectionEntry` thành một dòng memory text ngắn

Mục đích:
- actor lần sau không cần nuốt cả object
- chỉ cần lesson/strategy/focus dạng gọn

#### `memory_compression`

Đoạn `_compress_memory(...)`:
- nếu memory quá dài
- giữ lại các memory gần nhất
- gộp phần cũ thành một dòng `Compressed memory: ...`

Mục đích:
- tránh memory phình ra mãi
- mô phỏng cách nén bộ nhớ cho context window

#### `_infer_failure_mode(...)`

Đoạn này gắn nhãn lỗi cuối cùng cho `RunRecord`.

Logic:
- nếu đúng -> `none`
- nếu hai câu trả lời cuối giống nhau -> `looping`
- nếu Reflexion đổi câu trả lời nhưng vẫn sai -> `reflection_overfit`
- nếu không thì fallback sang `FAILURE_MODE_BY_QID` hoặc `wrong_final_answer`

Mục đích:
- report có breakdown failure modes

#### `run(example)` là phần quan trọng nhất

Đây là “trái tim” của project.

Luồng:

1. `runtime = get_runtime()`
   - chọn backend hiện tại

2. tạo các biến rỗng:
   - `reflection_memory`
   - `reflections`
   - `traces`

3. tính:
   - `effective_max_attempts`
   - `plan`

4. bắt đầu vòng `for attempt_id ...`

5. `runtime.actor_answer(...)`
   - sinh câu trả lời

6. `runtime.evaluate(...)`
   - chấm câu trả lời

7. tạo `AttemptTrace`
   - ghi câu trả lời
   - score
   - reason
   - plan
   - snapshot của reflection memory
   - token
   - latency

8. nếu score = 1
   - append trace
   - break

9. nếu là Reflexion và còn lượt
   - `runtime.reflect(...)`
   - append `reflection`
   - gắn reflection vào trace
   - cộng token/latency của bước reflect
   - append memory
   - nén memory nếu cần

10. hết loop
   - sum token
   - sum latency
   - suy ra failure mode
   - trả về `RunRecord`

#### ReAct khác Reflexion ở đâu trong file này

`ReActAgent`:
- `max_attempts=1`
- `adaptive_max_attempts=False`
- `memory_compression=False`

=> nghĩa là ReAct không thực sự tận dụng reflection loop.

`ReflexionAgent`:
- `agent_type="reflexion"`
- `max_attempts` mặc định là `3`

=> nghĩa là Reflexion sẽ đi qua nhánh:
- evaluate
- reflect
- retry

Nói ngắn:
- khác biệt không phải ở `run_benchmark.py`
- mà nằm trong nhánh `if self.agent_type == "reflexion"...` của `BaseAgent.run()`

### 7.3 `src/reflexion_lab/runtime.py`

File: [runtime.py](/home/hung/code/AI_CODE_VIN/lab/Day15/Day16-DongManhHung-2A202600465/src/reflexion_lab/runtime.py)

Đây là file quyết định:
- dùng mock hay API thật
- cách gọi actor/evaluator/reflector
- cách đo token và latency

#### `CallMetrics`, `ActorCall`, `EvaluatorCall`, `ReflectorCall`

Mục đích:
- thống nhất dữ liệu trả về từ runtime

Thay vì chỉ trả text, runtime trả cả:
- nội dung
- token
- latency

#### `_context_to_text(...)`

Mục đích:
- convert `example.context` thành một chuỗi dễ nhét vào prompt

#### `_estimate_text_tokens(...)`

Mục đích:
- nếu không có token thật, dùng heuristic char/4

#### `_extract_json_object(...)`

Mục đích:
- khi model trả về text lẫn JSON
- hàm này bóc phần JSON ra

Đây là chỗ rất hữu ích cho evaluator và reflector khi chạy API thật.

#### `BaseRuntime`

Đây là interface chung.

Nó định nghĩa 3 việc mọi runtime phải có:
- `actor_answer`
- `evaluate`
- `reflect`

#### `MockRuntime`

Đây là backend mặc định.

Mỗi hàm ở đây chỉ bọc lại `mock_runtime.py`.

Ví dụ:
- `actor_answer(...)`
  - gọi `mock_actor_answer(...)`
  - tự tính token/latency giả lập

- `evaluate(...)`
  - gọi `mock_evaluator(...)`

- `reflect(...)`
  - gọi `mock_reflector(...)`

Mục đích:
- chạy benchmark mà không cần mạng hay API key

#### `OpenAICompatRuntime`

Đây là backend dùng API thật.

##### `__init__`

Đọc cấu hình từ env:
- `REFLEXION_API_BASE_URL`
- `REFLEXION_API_KEY` hoặc `OPENAI_API_KEY`
- `REFLEXION_MODEL`
- `REFLEXION_API_TIMEOUT`

##### `_chat(...)`

Đây là chỗ gọi HTTP thật.

Nó làm:
1. dựng payload JSON
2. thêm header Authorization nếu có key
3. gửi POST tới `/chat/completions`
4. đo latency
5. parse response
6. lấy token usage nếu API trả về

Nếu lỗi:
- `HTTPError` -> raise `RuntimeError` có status code
- `URLError` -> raise `RuntimeError` nói không reach được endpoint

##### `actor_answer(...)`

Đây là chỗ dựng prompt cho Actor.

Nó ghép:
- question
- context
- attempt id
- agent type
- plan
- reflection memory

Rồi gọi `_chat(...)`.

##### `evaluate(...)`

Đây là chỗ dựng prompt cho Evaluator.

Nó gửi:
- question
- gold answer
- candidate answer
- context

Rồi yêu cầu model trả JSON với:
- `score`
- `reason`
- `missing_evidence`
- `spurious_claims`

##### `reflect(...)`

Đây là chỗ dựng prompt cho Reflector.

Nó gửi:
- question
- context
- failure reason
- missing evidence
- spurious claims
- prior reflection memory

Rồi yêu cầu model trả JSON cho `ReflectionEntry`.

#### `get_runtime()`

Đây là công tắc mode quan trọng nhất.

Nó đọc:
- `REFLEXION_RUNTIME`

Logic:
- nếu env = `openai_compat` -> dùng `OpenAICompatRuntime`
- nếu không -> dùng `MockRuntime`

Nói ngắn:
- muốn đổi mock/API thật, bạn không sửa code
- bạn đổi env này

### 7.4 `src/reflexion_lab/mock_runtime.py`

File: [mock_runtime.py](/home/hung/code/AI_CODE_VIN/lab/Day15/Day16-DongManhHung-2A202600465/src/reflexion_lab/mock_runtime.py)

Đây là file giả lập hành vi của mô hình.

#### `FIRST_ATTEMPT_WRONG`

Là bảng các câu hỏi cố tình trả sai ở attempt đầu.

Mục đích:
- làm cho Reflexion có “đất diễn”
- benchmark mới thể hiện được improvement so với ReAct

#### `FAILURE_MODE_BY_QID`

Là bảng ánh xạ `qid -> loại lỗi`.

Mục đích:
- giúp report có failure mode rõ ràng hơn

#### `actor_answer(...)`

Logic:
- nếu câu không nằm trong danh sách cố tình sai -> trả đúng luôn
- nếu là `react` -> giữ câu trả lời sai
- nếu là `reflexion`:
  - attempt đầu chưa có memory -> trả sai
  - attempt sau có memory -> trả đúng

Đây chính là cách mock mô phỏng “reflection giúp sửa sai”.

#### `evaluator(...)`

Logic:
- so sánh `gold_answer` với `answer` sau khi normalize
- nếu đúng -> score = 1
- nếu sai kiểu dừng ở first hop -> reason cụ thể hơn
- nếu sai kiểu chọn nhầm entity -> reason chung

Điểm quan trọng:
- evaluator không chỉ trả đúng/sai
- nó còn trả dữ liệu để reflector dùng tiếp

#### `reflector(...)`

Logic:
- nhìn vào lỗi từ evaluator
- sinh ra:
  - `lesson`
  - `next_strategy`
  - `focus_points`

Vai trò:
- làm nguyên liệu cho `reflection_memory`

### 7.5 `src/reflexion_lab/schemas.py`

File: [schemas.py](/home/hung/code/AI_CODE_VIN/lab/Day15/Day16-DongManhHung-2A202600465/src/reflexion_lab/schemas.py)

Đây là contract dữ liệu của cả project.

Nếu file này sai, gần như toàn bộ project sẽ lệch.

#### `ContextChunk`

Một mẩu context gồm:
- `title`
- `text`

#### `QAExample`

Một câu hỏi benchmark.

Gồm:
- `qid`
- `difficulty`
- `question`
- `gold_answer`
- `context`

#### `JudgeResult`

Kết quả chấm của evaluator.

Gồm:
- `score`
- `reason`
- `missing_evidence`
- `spurious_claims`

#### `ReflectionEntry`

Bản reflection sau một lần fail.

Gồm:
- `attempt_id`
- `failure_reason`
- `lesson`
- `next_strategy`
- `focus_points`
- `compressed_memory`

#### `AttemptTrace`

Log của một lượt thử.

Gồm:
- câu trả lời
- score
- reason
- reflection của lượt đó
- plan
- snapshot memory
- token
- latency

#### `RunRecord`

Log tổng của một câu hỏi sau khi agent chạy xong.

Nó là object quan trọng nhất cho benchmark/report.

#### `ReportPayload`

Schema của report cuối cùng.

Autograde sẽ nhìn nhiều vào object này.

### 7.6 `src/reflexion_lab/reporting.py`

File: [reporting.py](/home/hung/code/AI_CODE_VIN/lab/Day15/Day16-DongManhHung-2A202600465/src/reflexion_lab/reporting.py)

Đây là file biến log thô thành báo cáo.

#### `IMPLEMENTED_EXTENSIONS`

Danh sách bonus feature đã cài.

Autograde nhìn vào đây gián tiếp qua `report.extensions`.

#### `summarize(records)`

Mục đích:
- group theo `agent_type`
- tính:
  - số record
  - EM
  - average attempts
  - average token
  - average latency

Nếu có cả `react` và `reflexion`, nó tính thêm delta.

#### `failure_breakdown(records)`

Mục đích:
- đếm failure mode theo từng agent
- và cả `overall`

#### `build_report(...)`

Mục đích:
- tạo `ReportPayload`

Đáng chú ý:
- `examples` không chỉ có run-level
- còn có trace-level

Nghĩa là report cuối có thể nhìn sâu vào từng attempt.

#### `discussion`

Là đoạn phân tích mặc định.

Nó giúp autograde có đủ độ dài và có phần explanation.

#### `save_report(...)`

Mục đích:
- ghi `report.json`
- dựng một markdown report đơn giản cho người đọc

### 7.7 `src/reflexion_lab/utils.py`

File: [utils.py](/home/hung/code/AI_CODE_VIN/lab/Day15/Day16-DongManhHung-2A202600465/src/reflexion_lab/utils.py)

File này nhỏ nhưng rất thường dùng.

#### `normalize_answer(...)`

Mục đích:
- lower-case
- bỏ dấu câu/ký tự thừa
- chuẩn hóa khoảng trắng

Đây là nền để evaluator so sánh đáp án ổn định hơn.

#### `load_dataset(...)`

Mục đích:
- đọc JSON
- parse thành list `QAExample`

#### `save_jsonl(...)`

Mục đích:
- ghi từng `RunRecord` ra một dòng JSON

### 7.8 `src/reflexion_lab/prompts.py`

File: [prompts.py](/home/hung/code/AI_CODE_VIN/lab/Day15/Day16-DongManhHung-2A202600465/src/reflexion_lab/prompts.py)

File này chỉ thực sự có tác dụng khi chạy `openai_compat`.

#### `ACTOR_SYSTEM`

Vai trò:
- buộc actor dùng context
- làm theo plan
- tham khảo reflection memory
- chỉ trả final answer

#### `EVALUATOR_SYSTEM`

Vai trò:
- chấm đúng/sai
- trả JSON có cấu trúc

#### `REFLECTOR_SYSTEM`

Vai trò:
- phân tích lỗi
- biến lỗi thành lesson và strategy

### 7.9 `autograde.py`

File: [autograde.py](/home/hung/code/AI_CODE_VIN/lab/Day15/Day16-DongManhHung-2A202600465/autograde.py)

Đây là script chấm nhanh đầu ra.

#### `REQUIRED_KEYS`

Các key bắt buộc trong `report.json`:
- `meta`
- `summary`
- `failure_modes`
- `examples`
- `extensions`
- `discussion`

#### Cách chấm

`autograde.py` chia điểm thành:
- schema completeness
- experiment completeness
- analysis depth
- bonus extensions

#### Điều kiện quan trọng

Để đạt đủ phần experiment:
- `summary` phải có cả `react` và `reflexion`
- `meta.num_records >= 100`
- `len(examples) >= 20`

### 7.10 `tests/test_utils.py`

File: [tests/test_utils.py](/home/hung/code/AI_CODE_VIN/lab/Day15/Day16-DongManhHung-2A202600465/tests/test_utils.py)

Đây là test cơ bản của project.

Có 3 nhóm ý chính:

#### test normalize

Kiểm tra `normalize_answer(...)` có hoạt động đúng không.

#### test Reflexion recovery

Kiểm tra:
- Reflexion thật sự tạo reflection
- attempt sau dùng memory
- và sửa được câu trả lời

#### test ReAct baseline

Kiểm tra:
- ReAct chỉ chạy một attempt
- fail đúng kiểu expected

#### test report extensions

Kiểm tra:
- report có các bonus extensions đã khai báo

## 8. ReAct khác Reflexion trong project này ở đâu

Đây là ý rất hay bị hỏi.

### ReAct trong project này

- chỉ chạy 1 attempt
- không đi vào nhánh reflect/retry
- dùng làm baseline để so sánh

### Reflexion trong project này

- có thể chạy nhiều attempt
- nếu sai, gọi evaluator rồi reflector
- sinh lesson/strategy
- lưu vào reflection memory
- dùng memory đó cho attempt sau

Nói ngắn gọn:

```text
ReAct:
Answer -> Evaluate -> End

Reflexion:
Answer -> Evaluate -> Reflect -> Retry -> Evaluate -> ...
```

## 9. Chỗ nào dùng API thật

Nằm trong:
- `src/reflexion_lab/runtime.py`
- class `OpenAICompatRuntime`

Điều kiện để dùng:
- `REFLEXION_RUNTIME=openai_compat`

Nếu không set env này:
- project mặc định dùng `MockRuntime`

## 10. Env nào điều khiển mode chạy

Biến quan trọng nhất:
- `REFLEXION_RUNTIME`

Giá trị:
- `mock`
- `openai_compat`

Ví dụ chạy mock:

```bash
export REFLEXION_RUNTIME=mock
python run_benchmark.py
```

Ví dụ chạy API thật:

```bash
export REFLEXION_RUNTIME=openai_compat
export REFLEXION_API_BASE_URL=https://api.openai.com/v1
export OPENAI_API_KEY=your_key
export REFLEXION_MODEL=gpt-4o-mini
python run_benchmark.py
```

## 11. Nếu muốn sửa hành vi thì sửa ở đâu

### Muốn đổi số lần thử / logic retry
- sửa `src/reflexion_lab/agents.py`

### Muốn đổi cách gọi API / backend
- sửa `src/reflexion_lab/runtime.py`

### Muốn đổi mock behavior
- sửa `src/reflexion_lab/mock_runtime.py`

### Muốn đổi schema report hoặc thống kê
- sửa `src/reflexion_lab/reporting.py`

### Muốn đổi structure dữ liệu
- sửa `src/reflexion_lab/schemas.py`

### Muốn đổi prompt của Actor/Evaluator/Reflector
- sửa `src/reflexion_lab/prompts.py`

## 12. Cách đọc code nhanh nhất nếu quay lại sau này

Thứ tự đọc khuyên dùng:

1. `run_benchmark.py`
2. `src/reflexion_lab/agents.py`
3. `src/reflexion_lab/runtime.py`
4. `src/reflexion_lab/mock_runtime.py`
5. `src/reflexion_lab/reporting.py`
6. `autograde.py`

## 13. Kết luận ngắn

Nếu chỉ nhớ một câu:

`run_benchmark.py` điều phối benchmark, `agents.py` thực hiện ReAct/Reflexion loop, `runtime.py` chọn mock hay API thật, `reporting.py` tạo report, còn `autograde.py` chấm report đó.
