import os, json, logging
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, STORY_SCHEMA

logger = logging.getLogger(__name__)

_client = None

def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set; please configure your .env")
        _client = OpenAI(api_key=api_key)
    return _client

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
    logger.info("Calling OpenAI API to generate story spec")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(req)},
    ]
    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.4,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        logger.info("Successfully received response from OpenAI")
        return json.loads(content)
    except Exception as e:
        logger.error(f"OpenAI API call failed: {str(e)}")
        raise
