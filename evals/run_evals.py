#!/usr/bin/env python3
"""Run and check behavioral evaluations for friendly-tech-writing."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".agents" / "skills" / "friendly-tech-writing"
CASES_PATH = ROOT / "evals" / "cases.json"
TRIGGER_CASES_PATH = ROOT / "evals" / "trigger-cases.json"
OUTPUT_DIR = ROOT / "evals" / "output"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: корневое значение должно быть объектом")
    return value


def load_cases() -> list[dict[str, Any]]:
    payload = load_json(CASES_PATH)
    cases = payload.get("cases")
    if payload.get("version") != 1 or not isinstance(cases, list):
        raise ValueError(f"{CASES_PATH}: ожидается version=1 и массив cases")
    return cases


def extract_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", text, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md: отсутствует корректный frontmatter")

    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, raw_value = line.partition(":")
        if separator and not line.startswith((" ", "\t")):
            values[key.strip()] = raw_value.strip().strip("\"'")
    return values


def validate_repository() -> list[str]:
    errors: list[str] = []
    skill_file = SKILL_DIR / "SKILL.md"
    if not skill_file.is_file():
        return [f"Не найден {skill_file.relative_to(ROOT)}"]

    skill_text = skill_file.read_text(encoding="utf-8")
    try:
        frontmatter = extract_frontmatter(skill_text)
    except ValueError as error:
        errors.append(str(error))
        frontmatter = {}

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")
    if name != SKILL_DIR.name:
        errors.append(f"Имя skill {name!r} не совпадает с каталогом {SKILL_DIR.name!r}")
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        errors.append("Поле name должно быть kebab-case длиной до 64 символов")
    if not description or len(description) > 1024:
        errors.append("Поле description отсутствует или длиннее 1024 символов")
    if "[TODO:" in skill_text:
        errors.append("В SKILL.md остался шаблон TODO")

    for relative in re.findall(r"\]\((references/[^)]+)\)", skill_text):
        if not (SKILL_DIR / relative).is_file():
            errors.append(f"Не найдена ссылка из SKILL.md: {relative}")

    try:
        cases = load_cases()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        errors.append(str(error))
        cases = []

    seen_ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("Каждый элемент cases должен быть объектом")
            continue
        case_id = case.get("id", "")
        if not re.fullmatch(r"[a-z0-9-]+", case_id):
            errors.append(f"Некорректный id сценария: {case_id!r}")
        if case_id in seen_ids:
            errors.append(f"Повторяющийся id сценария: {case_id}")
        seen_ids.add(case_id)

        fixture_name = case.get("fixture", "")
        fixture = (ROOT / fixture_name).resolve()
        if not fixture.is_relative_to(ROOT) or not fixture.is_file():
            errors.append(f"{case_id}: не найден fixture {fixture_name!r}")
        prompt = case.get("prompt", "")
        if "$friendly-tech-writing" not in prompt:
            errors.append(f"{case_id}: prompt не вызывает $friendly-tech-writing")
        if fixture_name and fixture_name not in prompt:
            errors.append(f"{case_id}: prompt не ссылается на свой fixture")
        if not isinstance(case.get("rubric"), list) or not case["rubric"]:
            errors.append(f"{case_id}: отсутствует содержательная rubric")

    try:
        trigger_cases = load_json(TRIGGER_CASES_PATH)
        for group in ("positive", "negative"):
            prompts = trigger_cases.get(group)
            if not isinstance(prompts, list) or len(prompts) < 3:
                errors.append(f"trigger-cases.json: нужно не меньше трёх {group} случаев")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        errors.append(str(error))

    return errors


def count_bold_spans(text: str) -> int:
    return len(re.findall(r"\*\*[^*\n]+\*\*|__[^_\n]+__", text))


def count_list_blocks(text: str) -> int:
    blocks = 0
    in_list = False
    for line in text.splitlines():
        is_item = bool(re.match(r"^\s*(?:[-+*]|\d+[.)])\s+\S", line))
        if is_item and not in_list:
            blocks += 1
        if is_item:
            in_list = True
        elif line.strip() and not line.startswith((" ", "\t")):
            in_list = False
    return blocks


def check_output(case: dict[str, Any], text: str) -> list[str]:
    failures: list[str] = []
    folded = text.casefold()
    if not text.strip():
        return ["ответ пуст"]

    for expected in case.get("must_contain", []):
        if expected not in text:
            failures.append(f"нет обязательного фрагмента {expected!r}")

    for forbidden in case.get("must_not_contain", []):
        if forbidden.casefold() in folded:
            failures.append(f"найден запрещённый фрагмент {forbidden!r}")

    for pattern in case.get("must_match", []):
        if not re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            failures.append(f"не найден обязательный шаблон /{pattern}/")

    for pattern in case.get("must_not_match", []):
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            failures.append(f"найден запрещённый шаблон /{pattern}/")

    for heading in case.get("required_headings", []):
        pattern = rf"^#{{1,6}}\s+.*{re.escape(heading)}"
        if not re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            failures.append(f"нет заголовка, содержащего {heading!r}")

    for sequence in case.get("ordered_substrings", []):
        position = -1
        for fragment in sequence:
            next_position = folded.find(fragment.casefold(), position + 1)
            if next_position < 0:
                failures.append(
                    "не соблюдён порядок: " + " → ".join(repr(item) for item in sequence)
                )
                break
            position = next_position

    max_bold = case.get("max_bold_spans")
    if isinstance(max_bold, int) and count_bold_spans(text) > max_bold:
        failures.append(f"слишком много жирных выделений: больше {max_bold}")

    max_lists = case.get("max_list_blocks")
    if isinstance(max_lists, int) and count_list_blocks(text) > max_lists:
        failures.append(f"слишком много отдельных списков: больше {max_lists}")

    return failures


def select_cases(all_cases: list[dict[str, Any]], requested: list[str]) -> list[dict[str, Any]]:
    if not requested:
        return all_cases
    by_id = {case["id"]: case for case in all_cases}
    unknown = [case_id for case_id in requested if case_id not in by_id]
    if unknown:
        raise ValueError("Неизвестные сценарии: " + ", ".join(unknown))
    return [by_id[case_id] for case_id in requested]


def print_failures(label: str, failures: list[str]) -> None:
    print(f"FAIL {label}")
    for failure in failures:
        print(f"  - {failure}")


def run_case(case: dict[str, Any], run_number: int, model: str | None) -> int:
    executable = shutil.which("codex")
    if not executable:
        print("Не найден codex CLI", file=sys.stderr)
        return 2

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{case['id']}-{run_number}.md"
    command = [
        executable,
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--output-last-message",
        str(output_path),
    ]
    if model:
        command.extend(["--model", model])
    command.append(case["prompt"])

    print(f"RUN  {case['id']} #{run_number}")
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        print(f"Codex завершился с кодом {completed.returncode}", file=sys.stderr)
        return completed.returncode

    failures = check_output(case, output_path.read_text(encoding="utf-8"))
    if failures:
        print_failures(output_path.relative_to(ROOT).as_posix(), failures)
        return 1
    print(f"PASS {output_path.relative_to(ROOT)}")
    return 0


def check_saved_outputs(cases: list[dict[str, Any]]) -> int:
    status = 0
    for case in cases:
        outputs = sorted(OUTPUT_DIR.glob(f"{case['id']}-*.md"))
        if not outputs:
            print_failures(case["id"], ["нет сохранённых прогонов"])
            status = 1
            continue
        for output in outputs:
            failures = check_output(case, output.read_text(encoding="utf-8"))
            if failures:
                print_failures(output.relative_to(ROOT).as_posix(), failures)
                status = 1
            else:
                print(f"PASS {output.relative_to(ROOT)}")
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "run", "check", "list"))
    parser.add_argument("--case", action="append", default=[], dest="case_ids")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--model")
    args = parser.parse_args()

    validation_errors = validate_repository()
    if validation_errors:
        print_failures("repository", validation_errors)
        return 1
    if args.command == "validate":
        print("PASS структура skill и eval-набора корректна")
        return 0

    cases = select_cases(load_cases(), args.case_ids)
    if args.command == "list":
        for case in cases:
            print(f"{case['id']}: {case['description']}")
        return 0
    if args.command == "check":
        return check_saved_outputs(cases)
    if args.runs < 1:
        parser.error("--runs должен быть положительным")

    status = 0
    for case in cases:
        for run_number in range(1, args.runs + 1):
            status = max(status, run_case(case, run_number, args.model))
    return status


if __name__ == "__main__":
    raise SystemExit(main())

