from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sys
import time
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chat_logic import SYSTEM_PROMPT
from config import AppConfig


PROMPTS = (
    (
        "cpu",
        "CPU কি? সহজ অসমীয়াত বুজাই দিয়ক।",
    ),
    (
        "photosynthesis",
        "অষ্টম শ্ৰেণীৰ ছাত্ৰ-ছাত্ৰীৰ বাবে সালোক-সংশ্লেষণ অসমীয়াত বুজাই দিয়ক।",
    ),
    (
        "assam_sentences",
        "অসমৰ বিষয়ে পাঁচটা স্বাভাৱিক অসমীয়া বাক্য লিখক।",
    ),
    (
        "artificial_intelligence",
        "কৃত্ৰিম বুদ্ধিমত্তা কি? সহজ অসমীয়াত বুজাই দিয়ক।",
    ),
    (
        "short_story",
        "আৰম্ভণি, মাজভাগ আৰু শেষ স্পষ্টকৈ থকা এখন চুটি অসমীয়া সাধুকথা লিখক।",
    ),
    (
        "hardware_software",
        "হাৰ্ডৱেৰ আৰু ছফ্টৱেৰৰ মাজৰ পাৰ্থক্য অসমীয়াত বুজাই দিয়ক।",
    ),
)

# Only the explicitly listed options differ from the production-like baseline.
CONFIGURATIONS = (
    {
        "id": "production_baseline",
        "label": "Production-like baseline",
        "options": {},
    },
    {
        "id": "lower_temperature",
        "label": "Temperature 0.3",
        "options": {"temperature": 0.3},
    },
    {
        "id": "lower_top_p",
        "label": "top_p 0.75",
        "options": {"top_p": 0.75},
    },
    {
        "id": "higher_repeat_penalty",
        "label": "repeat_penalty 1.2",
        "options": {"repeat_penalty": 1.2},
    },
    {
        "id": "larger_output_limit",
        "label": "num_predict 1536",
        "options": {"num_predict": 1536},
    },
)

# Qualitative ratings are a manual review of this run's exact responses.
# Fluency, grammar, facts, and instruction: 1 (poor) to 5 (strong).
# Repetition: 1 (none/minimal) to 5 (severe).
ASSESSMENTS = {
    ("cpu", "production_baseline"): (1, 1, 1, 1, 2, "Awkward terminology and inaccurate CPU description; think text leaked."),
    ("cpu", "lower_temperature"): (3, 3, 4, 1, 4, "Most understandable CPU explanation in this set; still has awkward wording and think text."),
    ("cpu", "lower_top_p"): (1, 1, 1, 2, 2, "Invented/incorrect terminology and repeated definition; think text leaked."),
    ("cpu", "higher_repeat_penalty"): (1, 1, 1, 1, 1, "Final answer is largely Odia/English-script text, not usable Assamese."),
    ("cpu", "larger_output_limit"): (1, 1, 1, 1, 2, "Several technical claims/phrases are confused; think text leaked."),
    ("photosynthesis", "production_baseline"): (2, 2, 1, 1, 1, "Explains sunlight/heat, not photosynthesis; key request misunderstood."),
    ("photosynthesis", "lower_temperature"): (2, 2, 1, 1, 1, "Defines a grammatical concept instead of photosynthesis."),
    ("photosynthesis", "lower_top_p"): (1, 1, 1, 5, 1, "Repeats uncertainty about the term until num_predict truncation."),
    ("photosynthesis", "higher_repeat_penalty"): (2, 2, 1, 1, 1, "Switches to light interactions/reflection/refraction rather than photosynthesis."),
    ("photosynthesis", "larger_output_limit"): (1, 1, 1, 1, 1, "Answers about the solar system; the topic is wrong despite normal stop."),
    ("assam_sentences", "production_baseline"): (2, 2, 2, 1, 3, "Produces five numbered lines, but several are unnatural or semantically odd."),
    ("assam_sentences", "lower_temperature"): (2, 2, 2, 5, 2, "Repeats near-identical claims about a rich language/culture."),
    ("assam_sentences", "lower_top_p"): (1, 1, 1, 1, 3, "Five lines are present but largely nonsensical."),
    ("assam_sentences", "higher_repeat_penalty"): (1, 1, 1, 1, 1, "Long English planning text and English final sentences; severe instruction failure."),
    ("assam_sentences", "larger_output_limit"): (2, 2, 2, 1, 3, "Five lines are present; wording and some claims are unnatural/questionable."),
    ("artificial_intelligence", "production_baseline"): (2, 2, 3, 1, 3, "Broad idea is recognizable, but wording is awkward and anthropomorphic."),
    ("artificial_intelligence", "lower_temperature"): (3, 3, 3, 1, 3, "Understandable broad definition; English think text remains exposed."),
    ("artificial_intelligence", "lower_top_p"): (3, 3, 3, 1, 3, "Broadly relevant definition; awkward terminology and visible English think text."),
    ("artificial_intelligence", "higher_repeat_penalty"): (1, 1, 1, 2, 1, "Mixed-language, malformed response with unclear claims."),
    ("artificial_intelligence", "larger_output_limit"): (3, 3, 3, 1, 3, "Relevant short explanation, though it overstates human-like thinking."),
    ("short_story", "production_baseline"): (1, 1, 1, 5, 1, "Gibberish/repeated phrase; hits the 1024-token limit."),
    ("short_story", "lower_temperature"): (1, 1, 1, 5, 1, "Planning text loops on a proverb idea; hits the token limit without a story."),
    ("short_story", "lower_top_p"): (1, 1, 1, 5, 1, "Loops on what a proverb means and is truncated; no story."),
    ("short_story", "higher_repeat_penalty"): (1, 1, 1, 2, 1, "Three-part labels appear, but the story text is mostly incoherent."),
    ("short_story", "larger_output_limit"): (1, 1, 1, 1, 1, "Ends normally but gives only the words beginning/middle/end, not a story."),
    ("hardware_software", "production_baseline"): (2, 2, 2, 1, 3, "Core distinction is partly right; examples and some phrasing are confused."),
    ("hardware_software", "lower_temperature"): (2, 2, 2, 1, 3, "Definitions are partly recognizable; software/hardware relationship is misstated."),
    ("hardware_software", "lower_top_p"): (3, 3, 3, 1, 4, "Most relevant comparison here, but claims hardware works independently of software."),
    ("hardware_software", "higher_repeat_penalty"): (1, 1, 2, 1, 1, "Final answer is mostly English/mixed language, contrary to instruction."),
    ("hardware_software", "larger_output_limit"): (2, 2, 2, 1, 3, "Basic distinction is present, but examples and conclusion are inaccurate/unclear."),
}

REPORT_DIR = Path(__file__).resolve().parents[1] / "reports"


def _request_options(config: AppConfig, overrides: dict[str, int | float]) -> dict[str, int | float]:
    options: dict[str, int | float] = {
        "temperature": config.temperature,
        "num_predict": config.num_predict,
    }
    options.update(overrides)
    return options


def _run_trial(
    session: requests.Session,
    config: AppConfig,
    prompt_id: str,
    prompt: str,
    experiment: dict[str, Any],
) -> dict[str, Any]:
    options = _request_options(config, experiment["options"])
    payload = {
        "model": config.model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "think": False,
        "options": options,
    }
    started = time.perf_counter()
    trial: dict[str, Any] = {
        "prompt_id": prompt_id,
        "prompt": prompt,
        "configuration_id": experiment["id"],
        "configuration_label": experiment["label"],
        "options": options,
        "request_messages": payload["messages"],
    }
    try:
        response = session.post(
            f"{config.base_url}/api/chat",
            json=payload,
            timeout=(5, config.request_timeout),
            allow_redirects=False,
        )
        trial["latency_seconds"] = round(time.perf_counter() - started, 3)
        if 300 <= response.status_code < 400:
            trial["error"] = f"Unexpected redirect (HTTP {response.status_code})."
            return trial
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            trial["error"] = "Ollama returned an unexpected response format."
            return trial
        if isinstance(data.get("error"), str):
            trial["error"] = data["error"]
            return trial

        message = data.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            trial["error"] = "Ollama response did not contain string message content."
            return trial
        trial.update(
            {
                "response": content,
                "done": data.get("done"),
                "done_reason": data.get("done_reason"),
                "total_duration_ns": data.get("total_duration"),
                "load_duration_ns": data.get("load_duration"),
                "prompt_eval_count": data.get("prompt_eval_count"),
                "prompt_eval_duration_ns": data.get("prompt_eval_duration"),
                "eval_count": data.get("eval_count"),
                "eval_duration_ns": data.get("eval_duration"),
            }
        )
    except requests.Timeout as error:
        trial["latency_seconds"] = round(time.perf_counter() - started, 3)
        trial["error"] = f"Request timed out: {error}"
    except requests.ConnectionError as error:
        trial["latency_seconds"] = round(time.perf_counter() - started, 3)
        trial["error"] = f"Could not connect to local Ollama: {error}"
    except requests.HTTPError as error:
        trial["latency_seconds"] = round(time.perf_counter() - started, 3)
        trial["error"] = f"HTTP request failed: {error}"
    except requests.exceptions.JSONDecodeError as error:
        trial["latency_seconds"] = round(time.perf_counter() - started, 3)
        trial["error"] = f"Ollama returned invalid JSON: {error}"
    return trial


def _md_cell(value: object) -> str:
    return str(value).replace("|", r"\|").replace("\r", " ").replace("\n", " ")


def _render_report(run: dict[str, Any]) -> str:
    think_tag_trials = sum(
        "<think" in trial.get("response", "").casefold()
        for trial in run["trials"]
    )
    length_limited_trials = sum(
        trial.get("done_reason") == "length"
        for trial in run["trials"]
    )
    lines = [
        "# Assamese Generation Quality Experiment",
        "",
        f"- Run time: {run['started_at']}",
        f"- Model: `{run['model']}`",
        f"- Ollama version: `{run.get('ollama_version') or 'not available'}`",
        "- Production files/settings changed: **No**",
        "- Requests: direct, local `/api/chat`; each trial starts with the same system prompt and one user prompt.",
        "- `think: false`; responses are recorded verbatim, including any visible thinking tags.",
        "",
        "## Model and request inspection",
        "",
        f"- Installed model template: {run['model_template']}",
        f"- Installed model parameters: {run['model_parameters']}",
        "- The installed model template is `{{ .Prompt }}` with the stop tokens listed above; `/api/chat` receives structured role/content messages and Ollama formats them for the model.",
        "- The installed Modelfile did not declare `temperature`, `top_p`, `repeat_penalty`, or `num_predict`; baseline values come from the production request and the rest use Ollama defaults.",
        "- Ollama's API spelling for repetition penalty is `repeat_penalty`.",
        f"- `think: false` did not prevent visible `<think>` blocks in {think_tag_trials}/{len(run['trials'])} raw responses.",
        f"- Ollama reported `done_reason='length'` for {length_limited_trials}/{len(run['trials'])} responses; `done=True` can still accompany this limit reason.",
        "",
        "## Configuration comparison",
        "",
        "| ID | Options changed from baseline | Exact request options |",
        "|---|---|---|",
    ]
    for experiment in run["configurations"]:
        overrides = experiment["options"] or {"(none)": "(baseline)"}
        effective = run["effective_options"][experiment["id"]]
        lines.append(
            f"| `{experiment['id']}` | `{_md_cell(json.dumps(overrides, ensure_ascii=False))}` "
            f"| `{_md_cell(json.dumps(effective, ensure_ascii=False))}` |"
        )

    lines.extend(
        [
            "",
            "## Results and qualitative comparison",
            "",
            "Ratings below are manual observational judgments of these individual generations, not benchmark scores. "
            "Fluency, grammar, factual correctness, and instruction following use 1 (poor) to 5 (strong); "
            "repetition uses 1 (little/no repetition) to 5 (severe repetition). The factual ratings are a practical "
            "review, not subject-matter expert certification. They do not establish that one setting is generally better.",
            "",
        ]
    )
    by_key = {
        (trial["prompt_id"], trial["configuration_id"]): trial
        for trial in run["trials"]
    }
    for prompt_id, prompt in run["prompts"]:
        lines.extend(
            [
                f"### {prompt_id}",
                "",
                f"Prompt: {prompt}",
                "",
                "| Configuration | Fluency | Grammar | Factual correctness | Repetition | Instruction following | Latency (s) | Completion | Notes |",
                "|---|---:|---:|---:|---:|---:|---:|---|---|",
            ]
        )
        for experiment in run["configurations"]:
            trial = by_key[(prompt_id, experiment["id"])]
            fluency, grammar, factual, repetition, instruction, note = ASSESSMENTS[
                (prompt_id, experiment["id"])
            ]
            completion = (
                f"done={trial.get('done')!r}, reason={trial.get('done_reason')!r}"
                if "error" not in trial
                else f"ERROR: {trial['error']}"
            )
            lines.append(
                f"| {experiment['label']} | {fluency}/5 | {grammar}/5 | {factual}/5 | {repetition}/5 | "
                f"{instruction}/5 | {trial.get('latency_seconds', 'n/a')} | {_md_cell(completion)} | {_md_cell(note)} |"
            )
        for experiment in run["configurations"]:
            trial = by_key[(prompt_id, experiment["id"])]
            lines.extend(
                [
                    "",
                    f"#### {experiment['label']}",
                    "",
                    f"- Request options: `{json.dumps(trial['options'], ensure_ascii=False)}`",
                    f"- Response time: {trial.get('latency_seconds', 'n/a')} seconds",
                    f"- Completion: `done={trial.get('done')!r}`, `done_reason={trial.get('done_reason')!r}`",
                    f"- Token/timing metadata: `{_md_cell(json.dumps({key: trial.get(key) for key in ('prompt_eval_count', 'eval_count', 'total_duration_ns', 'load_duration_ns', 'prompt_eval_duration_ns', 'eval_duration_ns')}, ensure_ascii=False))}`",
                    "",
                    "Exact model response:",
                    "",
                    "````text",
                    trial.get("response", f"ERROR: {trial.get('error', 'No response recorded')}"),
                    "````",
                ]
            )
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "No configuration was consistently better across all six prompts. Lower temperature produced the clearest CPU explanation in this small sample, but it did not repair the photosynthesis misunderstanding or repeated Assam sentences. Increasing `num_predict` let the story request stop normally, but the result still was not a story. A `repeat_penalty` of 1.2 did not prevent repeated text or English thinking text. The 27/30 visible `<think>` result shows that the `think: false` API field did not reliably suppress those tags for this model/runtime.",
            "",
            "This experiment uses one generation per prompt and configuration. Stochastic variation, subject knowledge, and prompt sensitivity are not controlled by one sample. Do not treat these observations as a quality benchmark or change production settings based only on this run. Compare the exact responses above; no application or model configuration was modified.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config = AppConfig.from_env()
    session = requests.Session()
    session.trust_env = False

    try:
        version_response = session.get(
            f"{config.base_url}/api/version",
            timeout=(3, 5),
            allow_redirects=False,
        )
        version_response.raise_for_status()
        version_data = version_response.json()
        ollama_version = version_data.get("version") if isinstance(version_data, dict) else None
    except requests.RequestException as error:
        print(f"Cannot query local Ollama version: {error}", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"Local Ollama returned invalid version JSON: {error}", file=sys.stderr)
        return 1

    model_template = (
        "TEMPLATE {{ .Prompt }}; stop tokens: <|start_of_role|>, "
        "<|end_of_role|>, <|end_of_text|> (from `ollama show --modelfile`)"
    )
    model_parameters = (
        "No temperature/top_p/repeat_penalty/num_predict declarations "
        "(from `ollama show --parameters`)"
    )
    effective_options = {
        experiment["id"]: _request_options(config, experiment["options"])
        for experiment in CONFIGURATIONS
    }
    run: dict[str, Any] = {
        "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "model": config.model_name,
        "ollama_version": ollama_version,
        "model_template": model_template,
        "model_parameters": model_parameters,
        "production_defaults": {
            "temperature": config.temperature,
            "num_predict": config.num_predict,
            "top_p": "Ollama default (omitted)",
            "repeat_penalty": "Ollama default (omitted)",
            "think": False,
            "stream": False,
        },
        "prompts": PROMPTS,
        "configurations": CONFIGURATIONS,
        "effective_options": effective_options,
        "trials": [],
    }

    trial_count = len(PROMPTS) * len(CONFIGURATIONS)
    for experiment_index, experiment in enumerate(CONFIGURATIONS, start=1):
        for prompt_index, (prompt_id, prompt) in enumerate(PROMPTS, start=1):
            print(
                f"[{(experiment_index - 1) * len(PROMPTS) + prompt_index}/{trial_count}] "
                f"{experiment['id']} / {prompt_id}",
                flush=True,
            )
            trial = _run_trial(session, config, prompt_id, prompt, experiment)
            run["trials"].append(trial)
            if "error" in trial:
                print(f"  ERROR: {trial['error']}", file=sys.stderr, flush=True)
            else:
                print(
                    f"  {trial['latency_seconds']}s; done={trial.get('done')!r}; "
                    f"reason={trial.get('done_reason')!r}",
                    flush=True,
                )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    json_path = REPORT_DIR / f"assamese-generation-{timestamp}.json"
    markdown_path = REPORT_DIR / f"assamese-generation-{timestamp}.md"
    json_path.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_report(run), encoding="utf-8")

    print(f"\nRAW_RESULTS={json_path}")
    print(f"COMPARISON_REPORT={markdown_path}")
    errors = sum("error" in trial for trial in run["trials"])
    print(f"COMPLETED={len(run['trials']) - errors}/{len(run['trials'])}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
