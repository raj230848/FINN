"""Opt-in Web Push outbox. Subscription endpoints/keys never appear in logs."""
import base64
import json
import logging
from datetime import timedelta
from urllib.parse import urlparse
from sqlalchemy import select, update
from ..config import settings
from ..database import SessionLocal
from ..models import PushRecipient, PushDelivery, SignalEvent, Company, Preference, Announcement, Alert, utcnow

log = logging.getLogger(__name__)
PUSH_HOSTS = {'fcm.googleapis.com','updates.push.services.mozilla.com','web.push.apple.com'}

def configured():
    return bool(settings.vapid_private_key and settings.vapid_public_key and settings.vapid_subject.startswith(('mailto:','https://')))

def validate_subscription(value):
    endpoint = value.get('endpoint','')
    url = urlparse(endpoint)
    host = (url.hostname or '').lower()
    if url.scheme!='https' or url.username or url.password or url.port not in (None,443) or len(endpoint)>2048 or not (host in PUSH_HOSTS or host.endswith('.notify.windows.com')):
        raise ValueError('Use a subscription from a supported browser push service.')
    keys=value.get('keys',{})
    for name,size in [('p256dh',65),('auth',16)]:
        encoded=keys.get(name,'')
        if not isinstance(encoded,str) or len(encoded)>160:
            raise ValueError('Invalid push subscription keys.')
        try: raw=base64.urlsafe_b64decode(encoded+'='*(-len(encoded)%4))
        except Exception: raise ValueError('Invalid push subscription keys.') from None
        if len(raw)!=size: raise ValueError('Invalid push subscription keys.')
    return {'endpoint':endpoint,'keys':{k:keys[k] for k in ('p256dh','auth')}}

def eligible(db,event):
    company=db.get(Company,event.ticker);pref=db.get(Preference,1)
    if event.mode!='sourced' or not company or not company.watched or (pref and pref.companies and event.ticker not in pref.companies):return False
    if event.kind in ('price','volume'):
        key=event.event_key.removeprefix('market:')
        return db.scalar(select(Alert.id).where(Alert.key==key)) is not None
    filing=db.scalar(select(Announcement).where(Announcement.fingerprint==event.event_key.split(':')[-1]))
    if filing and pref and pref.categories and filing.category not in pref.categories:return False
    return bool(filing and filing.priority!='low' and (filing.priority=='high' or filing.needs_review or (pref and filing.category in pref.categories)))

def queue_event(db,event):
    if event.mode!='sourced' or not eligible(db,event):return
    for recipient in db.scalars(select(PushRecipient).where(PushRecipient.enabled.is_(True),PushRecipient.enabled_at<=event.created_at)):
        if not db.scalar(select(PushDelivery.id).where(PushDelivery.recipient_id==recipient.id,PushDelivery.event_id==event.id)):
            db.add(PushDelivery(recipient_id=recipient.id,event_id=event.id))

def send_web_push(subscription,payload):
    from pywebpush import webpush
    return webpush(subscription_info=validate_subscription(subscription),data=json.dumps(payload),
        vapid_private_key=settings.vapid_private_key,vapid_claims={'sub':settings.vapid_subject},ttl=3600,timeout=8)

def process_pending(db,sender=None,now=None,limit=20):
    """One bounded batch; transaction claims protect against concurrent workers.

    A stable notification tag also collapses retries at the receiving browser.
    A 2xx means accepted by its push service, not confirmed display on a device.
    """
    if sender is None and not configured():return 0
    sender=sender or send_web_push;now=now or utcnow();sent=0
    # Recover an interrupted send. Service-worker tags provide recipient dedup.
    db.execute(update(PushDelivery).where(PushDelivery.state=='sending',PushDelivery.next_attempt_at<=now).values(state='retry'))
    db.commit()
    ids=list(db.scalars(select(PushDelivery.id).where(PushDelivery.state.in_(['pending','retry']),PushDelivery.next_attempt_at<=now).order_by(PushDelivery.id).limit(limit)))
    for id in ids:
        claimed=db.execute(update(PushDelivery).where(PushDelivery.id==id,PushDelivery.state.in_(['pending','retry'])).values(state='sending',next_attempt_at=now+timedelta(minutes=2),attempts=PushDelivery.attempts+1))
        db.commit()
        if not claimed.rowcount:continue
        delivery=db.get(PushDelivery,id);db.refresh(delivery)
        recipient=db.get(PushRecipient,delivery.recipient_id);event=db.get(SignalEvent,delivery.event_id)
        if not recipient or not event or not recipient.enabled or event.created_at<recipient.enabled_at or not eligible(db,event):
            delivery.state='cancelled';db.commit();continue
        try:
            sender(recipient.subscription,{'event_id':event.id,'title':event.title,'body':event.explanation[:290]+f' | Event date: {event.occurred_at.date()}','ticker':event.ticker,'url':'/'})
            delivery.state='sent';delivery.delivered_at=now;delivery.error_code=None;sent+=1
        except Exception as error:
            response=getattr(error,'response',None);code=getattr(response,'status_code',None)
            delivery.error_code=f'HTTP_{code}' if code else 'TRANSPORT_ERROR'
            if code in (404,410):recipient.enabled=False
            retry=(code is None or code==429 or code>=500)
            delivery.state='retry' if retry and delivery.attempts<3 else 'failed'
            delivery.next_attempt_at=now+timedelta(seconds=min(600,30*2**delivery.attempts))
            log.warning('push_delivery event=%s status=%s attempts=%s',event.id,delivery.error_code,delivery.attempts)
        db.commit()
    return sent

def deliver_pending():
    try:
        with SessionLocal() as db:process_pending(db)
    except Exception:
        log.warning('push_delivery_batch_failed')
