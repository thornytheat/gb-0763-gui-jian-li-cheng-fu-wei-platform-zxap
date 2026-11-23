import json

from app.config import SAMPLES


def survey_book():
    survey = json.loads((SAMPLES / 'survey.json').read_text(encoding='utf-8'))
    return {item['ref']: item for item in survey['marks']}, survey['plan']
