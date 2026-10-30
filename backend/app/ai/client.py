"""Small structured-output calls, always bounded to supplied evidence."""
import json
import httpx
from pydantic import BaseModel
from ..config import settings

def structured_call(system: str, payload: dict, schema: type[BaseModel]) -> BaseModel:
    if not settings.openai_api_key:
        raise ValueError('No model key configured')
    with httpx.Client(timeout=40) as client:
        response = client.post('https://api.openai.com/v1/chat/completions', headers={'Authorization': f'Bearer {settings.openai_api_key}'}, json={
            'model': settings.openai_model,
            'messages': [{'role':'system','content':system}, {'role':'user','content':json.dumps(payload)}],
            'response_format': {'type':'json_schema','json_schema': {'name':schema.__name__,'strict':False,'schema':schema.model_json_schema()}},
            'max_completion_tokens': 1600,
        })
        response.raise_for_status()
        return schema.model_validate_json(response.json()['choices'][0]['message']['content'])
