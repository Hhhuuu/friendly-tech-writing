import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_evals  # noqa: E402


class RepositoryValidationTests(unittest.TestCase):
    def test_repository_is_valid(self):
        self.assertEqual(run_evals.validate_repository(), [])

    def test_all_cases_have_unique_ids(self):
        case_ids = [case["id"] for case in run_evals.load_cases()]
        self.assertEqual(len(case_ids), len(set(case_ids)))


class OutputChecksTests(unittest.TestCase):
    def case(self, case_id):
        return next(case for case in run_evals.load_cases() if case["id"] == case_id)

    def test_rewrite_readme_accepts_minimum_valid_output(self):
        text = """# Super Config Service

Сервис запускается локально на `http://localhost:8080`.

Для работы нужны Docker 27.1, `SERVICE_ACCOUNT_ID` и доступ к реестру.
Запустите сервис командой `docker compose up`.
"""
        self.assertEqual(run_evals.check_output(self.case("rewrite-readme"), text), [])

    def test_rewrite_readme_rejects_missing_fact_and_ai_cliche(self):
        text = "В современном мире сервис удобно запускается локально."
        failures = run_evals.check_output(self.case("rewrite-readme"), text)
        self.assertTrue(any("Docker 27.1" in failure for failure in failures))
        self.assertTrue(any("в современном мире" in failure for failure in failures))

    def test_runbook_requires_warning_before_command(self):
        case = self.case("safe-runbook")
        valid = """# Runbook payments-api

Если проверки не проходят, незавершённые запросы потеряются.
Выполните `kubectl delete pod payments-7d9f -n prod`.
Проверьте payments-api через 5 минут и обратитесь в oncall-platform.
"""
        self.assertEqual(run_evals.check_output(case, valid), [])

        invalid = valid.replace(
            "Если проверки не проходят, незавершённые запросы потеряются.\n"
            "Выполните `kubectl delete pod payments-7d9f -n prod`.",
            "Выполните `kubectl delete pod payments-7d9f -n prod`.\n"
            "Незавершённые запросы потеряются.",
        )
        failures = run_evals.check_output(case, invalid)
        self.assertTrue(any("порядок" in failure for failure in failures))

    def test_useful_table_must_remain_a_table(self):
        case = self.case("preserve-useful-table")
        text = """# Выбор хранилища

| Вариант | Чтение p95 | RPO |
| --- | ---: | ---: |
| PostgreSQL | 45 мс | 5 минут |
| Redis | 8 мс | Данные теряются при сбое |
| S3 | 180 мс | 24 часа |

Команда склоняется к PostgreSQL. Нагрузочный профиль ещё не измеряли.
"""
        self.assertEqual(run_evals.check_output(case, text), [])

        prose = text.replace("| Вариант | Чтение p95 | RPO |", "Сравнение вариантов:")
        failures = run_evals.check_output(case, prose)
        self.assertTrue(any("обязательный шаблон" in failure for failure in failures))

    def test_ambiguous_relationships_require_a_question(self):
        case = self.case("clarify-ambiguous-relationships")
        question = (
            "Правильно ли я понимаю поток: Gateway вызывает Risk Engine, затем Ledger, "
            "а Notifications получает событие асинхронно?"
        )
        self.assertEqual(run_evals.check_output(case, question), [])

        invented_flow = question.replace("?", ".").replace(
            "Правильно ли я понимаю поток: ", "Gateway последовательно вызывает "
        )
        failures = run_evals.check_output(case, invented_flow)
        self.assertTrue(any("'?'" in failure for failure in failures))

        two_questions = question + " Это синхронный вызов?"
        failures = run_evals.check_output(case, two_questions)
        self.assertTrue(any("слишком много вопросов" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()

