SYSTEM_PROMPT = """You are a special-education instructional designer. Write Social Stories that follow the standard criteria:
- Descriptive and perspective sentences greatly outnumber directive sentences.
- Answer who/what/where/when/why/how concretely; nonjudgmental tone.
- Short sentences at early-reader level; avoid sarcasm and idioms.
- End with an encouraging affirmation.
Output ONLY valid JSON matching the provided schema. Avoid names; use “I” or “the student”."""


STORY_SCHEMA = r"""{
  "meta": {
    "language": "en-US",
    "age": <number>,
    "reading_level": "<string>",
    "perspective": "first_person",
    "visual_guidelines": {
      "palette": "soft_high_contrast",
      "avoid": ["flashing", "crowded backgrounds"]
    },
    "title": "<short title>"
  },
  "scenes": [
    {
      "id": <int>,
      "goal": "<short goal>",
      "script": "<1–2 short sentences at early-reader level>",
      "on_screen_text": "<<= 10 words>",
      "image_prompt": "<flat, classroom-friendly illustration; simple shapes; soft colors; clean background; no text on walls>",
      "duration_sec": <6–9>,
      "audio_ssml": "<speak><prosody rate='-10%'>...</prosody></speak>"
    }
  ],
  "closing_affirmation": "<gentle encouragement>",
  "srt": "<valid SRT covering all scenes with timestamps>"
}"""


USER_PROMPT_TEMPLATE = """Inputs:
- Age: {age}, Reading level: {reading_level}, Language: en-US
- Diagnosis summary (high-level only): {diagnosis_summary}
- Situation: {situation}
- Setting: {setting}
- Words to avoid: {words_to_avoid}
- Perspective: first_person

Schema:
{schema}

Constraints:
- 6–8 scenes.
- Descriptive/perspective sentences greatly outnumber directive ones.
- Avoid negative/judgmental language and idioms.
- Match reading level to age.
- Include SRT for all scenes; timestamps must align with durations.
Return ONLY valid JSON for the schema above."""
