import asyncio

import httpx

from backend.tagging import tagger


def _run_tag_problem(payload):
    async def handler(request):
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)

    async def run():
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            problem = {"id": "gauss-2025-g7-1", "statement": "Test", "choices": ["A", "B"]}
            return await tagger.tag_problem(client, problem)

    return asyncio.run(run())


def test_tag_problem_filters_and_parses_json():
    payload = {"response": '{"tags": ["Divisibility ", "percent"]}'}
    tags = _run_tag_problem(payload)
    assert tags == ["divisibility", "percentages"]


def test_tag_problem_fallbacks_to_reasoning_text():
    payload = {"response": "", "thinking": "This requires angles and percentages reasoning."}
    tags = _run_tag_problem(payload)
    assert set(tags) == {"angles", "percentages"}
