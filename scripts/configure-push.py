"""Generate server-side VAPID keys without printing or committing secrets."""
import argparse
import base64
import re
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

parser=argparse.ArgumentParser()
parser.add_argument('--subject',required=True,help='Owner contact, e.g. mailto:you@example.com')
args=parser.parse_args()
if not args.subject.startswith(('mailto:','https://')):parser.error('Use a mailto or HTTPS contact.')
root=Path(__file__).resolve().parents[1];env=root/'.env'
text=env.read_text(encoding='utf-8') if env.exists() else (root/'.env.example').read_text(encoding='utf-8')
if re.search(r'^VAPID_PRIVATE_KEY=\S+',text,re.M):raise SystemExit('Existing keys preserved. Rotate deliberately; existing subscriptions depend on them.')
key=ec.generate_private_key(ec.SECP256R1())
private=base64.urlsafe_b64encode(key.private_bytes(serialization.Encoding.DER,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())).decode().rstrip('=')
public=base64.urlsafe_b64encode(key.public_key().public_bytes(serialization.Encoding.X962,serialization.PublicFormat.UncompressedPoint)).decode().rstrip('=')
for name,value in [('VAPID_PRIVATE_KEY',private),('VAPID_PUBLIC_KEY',public),('VAPID_SUBJECT',args.subject)]:
    if re.search(r'^'+name+'=',text,re.M):text=re.sub(r'^'+name+r'=.*$',lambda _:name+'='+value,text,flags=re.M)
    else:text+='\n'+name+'='+value+'\n'
env.write_text(text,encoding='utf-8')
print('VAPID keys saved only in the private root .env. Restart the backend, then opt in from the notification sheet.')
