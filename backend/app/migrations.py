"""Additive SQLite transition; preserves existing rows and unknown ingest dates."""
from sqlalchemy import inspect, text
from .services.materiality import fingerprint, description_checksum

VERSION = 1

def migrate_schema(engine):
    if engine.dialect.name != 'sqlite':
        raise RuntimeError('This prototype migration supports SQLite only.')
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)'))
        if conn.execute(text('SELECT version FROM schema_migrations WHERE version=:v'), {'v':VERSION}).first():
            return
        columns = {c['name'] for c in inspect(conn).get_columns('announcements')}
        for name, declaration in {
            'source_filing_id':'VARCHAR(160)', 'content_checksum':'VARCHAR(64)',
            'ingested_at':'DATETIME', 'needs_review':'BOOLEAN NOT NULL DEFAULT 0',
        }.items():
            if name not in columns:
                conn.execute(text(f'ALTER TABLE announcements ADD COLUMN {name} {declaration}'))
        rows = conn.execute(text('SELECT id,ticker,title,published_at,mode,source_url,text FROM announcements ORDER BY id')).mappings().all()
        from datetime import datetime
        used = set()
        for row in rows:
            checksum = description_checksum(row['text'] or '')
            key = fingerprint(row['ticker'], row['title'], datetime.fromisoformat(str(row['published_at'])),
                              row['mode'], source_url=row['source_url'], content_checksum=checksum)
            if key in used:
                conn.execute(text('UPDATE announcements SET content_checksum=:c,needs_review=1 WHERE id=:id'), {'c':checksum,'id':row['id']})
                continue
            used.add(key)
            conn.execute(text('UPDATE announcements SET fingerprint=:key,content_checksum=:c WHERE id=:id'),
                         {'key':key,'c':checksum,'id':row['id']})
        conn.execute(text('INSERT INTO schema_migrations(version) VALUES (:v)'), {'v':VERSION})
