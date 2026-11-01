"""Bounded, schema-validated Gemini calls. Never log provider bodies or secrets."""
import json
import logging
import time
import httpx
from pydantic import BaseModel, ValidationError
from ..config import settings

GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions'
log = logging.getLogger('uvicorn.error.finn.ai')

class ProviderError(RuntimeError):
    pass

def structured_call(system: str, payload: dict, schema: type[BaseModel], *, attempts: int=3, timeout_seconds: float=12) -> BaseModel:
    if not settings.gemini_api_key:
        raise ProviderError('Gemini is not configured.')
    content = json.dumps(payload, ensure_ascii=False)
    if len(content) > 48000:
        raise ProviderError('The evidence exceeds the model request limit.')
    body = {'model':settings.gemini_model,
            'messages':[{'role':'system','content':system},{'role':'user','content':content}],
            'response_format':{'type':'json_schema','json_schema':{
                'name':schema.__name__,'strict':False,'schema':schema.model_json_schema()}},
            'max_tokens':1600}
    attempts = max(1,min(3,attempts))
    with httpx.Client(timeout=max(1,min(12,timeout_seconds))) as client:
        for attempt in range(attempts):
            try:
                response = client.post(GEMINI_URL, headers={
                    'Authorization':f'Bearer {settings.gemini_api_key}',
                    'Content-Type':'application/json'}, json=body)
            except (httpx.TimeoutException, httpx.TransportError):
                if attempt == attempts-1:
                    raise ProviderError('Gemini could not be reached.') from None
                time.sleep(0.5 * (attempt + 1))
                continue
            if response.status_code == 429 or 500 <= response.status_code < 600:
                if attempt == attempts-1:
                    raise ProviderError('Gemini is temporarily unavailable or rate limited.')
                try:
                    delay = min(2, max(0, float(response.headers.get('Retry-After', '0.5'))))
                except ValueError:
                    delay = 0.5
                time.sleep(delay)
                continue
            if response.status_code != 200:
                raise ProviderError('Gemini rejected the request. Check backend configuration.')
            try:
                result = response.json()
                choice = result['choices'][0]
                if choice.get('finish_reason') not in (None, 'stop'):
                    raise ValueError('Incomplete response')
                answer = choice['message']['content']
                if not isinstance(answer,str) or not answer.strip() or len(answer)>18000:
                    raise ValueError('Invalid content')
                parsed = schema.model_validate_json(answer)
            except (ValueError, TypeError, KeyError, IndexError, ValidationError):
                raise ProviderError('Gemini returned an invalid structured response.') from None
            usage = result.get('usage') or {}
            log.info('gemini_call model=%s attempts=%d tokens=%s', settings.gemini_model,
                     attempt+1, usage.get('total_tokens','unknown'))
            return parsed
    raise ProviderError('Gemini could not complete the request.')
