import json
from openai import OpenAI
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, STORY_SCHEMA

_client = OpenAI()

def _redact(text: str) -> str:
    # MVP: no-op; expand to replace names with "the student" if needed.
    return text

def build_user_prompt(req) -> str:
    return USER_PROMPT_TEMPLATE.format(
        age=req.age,
        reading_level=req.reading_level,
        diagnosis_summary=_redact(req.diagnosis_summary),
        situation=_redact(req.situation),
        setting=_redact(req.setting),
        words_to_avoid=json.dumps(req.words_to_avoid),
        schema=STORY_SCHEMA
    )

def get_story_spec(req) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(req)},
    ]
    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.4,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    return json.loads(content)
