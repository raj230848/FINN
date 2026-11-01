"""Export actual saved user/assistant messages; omit internal/tool content.

This creates a private submission attachment, never a public Git artifact.
"""
import argparse
import json
import re
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--session',required=True,type=Path)
parser.add_argument('--out',type=Path,default=Path('artifacts/submission/AI_BUILD_HISTORY_REDACTED.md'))
args=parser.parse_args()
redactions=0
def clean(text):
    global redactions
    for tag in ('environment_context','in-app-browser-context','external_codex_apps_open_page'):
        text=re.sub(r'<'+tag+r'\b[^>]*>[\s\S]*?</'+tag+r'>','',text)
    patterns=[r'AIza[0-9A-Za-z_-]{20,}',r'gh[pousr]_[A-Za-z0-9_]{20,}',r'sk-[A-Za-z0-9_-]{20,}',r'(?i)(?:Bearer\s+)[A-Za-z0-9_.-]{24,}',r'(?im)(?:GEMINI_API_KEY|OPENAI_API_KEY|FINN_API_TOKEN|FINN_ACCESS_TOKEN|FINN_SESSION_SECRET|VAPID_PRIVATE_KEY)\s*[:=]\s*[\"\']?[^\s\"\']{16,}']
    for pattern in patterns:
        text,n=re.subn(pattern,'[REDACTED CREDENTIAL]',text);redactions+=n
    text,n=re.subn(r'(?i)(?<=code )(?=[A-Z0-9-]*[A-Z])[A-Z0-9]{4}-[A-Z0-9]{4}','[REDACTED DEVICE CODE]',text);redactions+=n
    return text.strip()

messages=[]
with args.session.open(encoding='utf-8') as stream:
    for line in stream:
        item=json.loads(line);payload=item.get('payload',{})
        if item.get('type')!='response_item' or payload.get('type')!='message' or payload.get('role') not in ('user','assistant'):continue
        if payload.get('channel') not in (None,'final','commentary'):continue
        text='\n'.join(part.get('text','') for part in payload.get('content',[]) if part.get('type') in ('input_text','output_text'))
        text=clean(text)
        if text:messages.append((item.get('timestamp',''),payload['role'],text))
if not messages:raise SystemExit('No saved visible messages found; no history was invented.')
header='# FINN — actual build conversation export\n\nExported from the saved Codex session. User and assistant text only; internal instructions, reasoning, tool calls and tool outputs are omitted. Credential-shaped text is redacted. Attachments and screenshots are referenced, not embedded. This is a redacted text export, not a complete raw session trace.\n\n'
body='\n\n'.join(f'## {i}. {role.title()} — {timestamp}\n\n{text}' for i,(timestamp,role,text) in enumerate(messages,1))
args.out.parent.mkdir(parents=True,exist_ok=True)
args.out.write_text(header+body+f'\n\nExport summary: {len(messages)} messages; {redactions} credential-pattern redactions.\n',encoding='utf-8')
print(f'Private redacted history saved: {len(messages)} messages; {redactions} redactions.')
