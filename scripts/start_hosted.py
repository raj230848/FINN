"""Supervise the full FINN stack on one public origin; backend stays loopback-only."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def deployment_environment(source):
    env = dict(source)
    for key, minimum in [('FINN_API_TOKEN', 32), ('FINN_ACCESS_TOKEN', 16), ('FINN_SESSION_SECRET', 32)]:
        if len(env.get(key, '')) < minimum:
            raise ValueError(f'{key} is missing or too short. Set a server-only hosting secret.')
    from sqlalchemy.engine import make_url
    url = make_url(env.get('DATABASE_URL', ''))
    if url.drivername != 'sqlite' or not url.database or not Path(url.database).is_absolute():
        raise ValueError('Set DATABASE_URL to an absolute SQLite file on the persistent disk.')
    backend_port = int(env.get('FINN_INTERNAL_PORT', '8000'))
    public_port = int(env.get('PORT', '8080'))
    if not 1024 <= backend_port <= 65535 or not 1024 <= public_port <= 65535 or backend_port == public_port:
        raise ValueError('Use separate valid public/internal ports.')
    env.update(PUBLIC_DEPLOYMENT='true', FINN_PUBLIC_MODE='true', BACKEND_URL=f'http://127.0.0.1:{backend_port}', HOSTNAME='0.0.0.0', PORT=str(public_port), NODE_ENV='production', NEXT_TELEMETRY_DISABLED='1', PYTHONUNBUFFERED='1')
    return env, backend_port


def service_environments(env):
    # Keep provider credentials and storage configuration out of the Node process.
    backend_only = {'DATABASE_URL', 'GEMINI_API_KEY', 'VAPID_PRIVATE_KEY'}
    frontend_only = {'FINN_ACCESS_TOKEN', 'FINN_SESSION_SECRET'}
    return (
        {name: value for name, value in env.items() if name not in frontend_only},
        {name: value for name, value in env.items() if name not in backend_only},
    )


def main():
    env, backend_port = deployment_environment(os.environ)
    backend_env, frontend_env = service_environments(env)
    if hasattr(os, 'geteuid') and os.geteuid()==0:
        # A freshly mounted host disk can be root-owned. Prepare only our exact
        # database files, then drop privileges before either service is launched.
        from sqlalchemy.engine import make_url
        import pwd
        database=Path(make_url(env['DATABASE_URL']).database).resolve()
        disk=Path('/var/lib/finn').resolve()
        if not database.is_relative_to(disk):
            raise ValueError('Root bootstrap is restricted to /var/lib/finn.')
        account=pwd.getpwnam('finn')
        database.parent.mkdir(parents=True,exist_ok=True)
        os.chown(database.parent,account.pw_uid,account.pw_gid)
        for path in [database,Path(str(database)+'-wal'),Path(str(database)+'-shm')]:
            if path.exists():
                if not path.resolve().is_relative_to(disk):raise ValueError('Database files must remain on the FINN disk.')
                os.chown(path,account.pw_uid,account.pw_gid)
        os.setgroups([]);os.setgid(account.pw_gid);os.setuid(account.pw_uid)
    server = ROOT / 'frontend/.next/standalone/server.js'
    if not server.exists():
        raise RuntimeError('Build the standalone frontend before starting the hosted stack.')
    children = []
    stopping = False
    def stop(_signal, _frame):
        nonlocal stopping
        stopping = True
    for name in ('SIGTERM', 'SIGINT'):
        signal.signal(getattr(signal, name), stop)
    try:
        children.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', str(backend_port), '--workers', '1'], cwd=ROOT / 'backend', env=backend_env))
        deadline = time.monotonic() + 120
        while not stopping and time.monotonic() < deadline:
            if children[0].poll() is not None:
                raise RuntimeError('The backend exited during startup. Inspect sanitized application logs.')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{backend_port}/api/health', timeout=2) as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            time.sleep(.25)
        else:
            if not stopping:
                raise RuntimeError('Backend startup did not complete within 120 seconds.')
        if stopping:
            return 0
        children.append(subprocess.Popen([frontend_env.get('NODE_BINARY', 'node'), str(server)], cwd=server.parent, env=frontend_env))
        while not stopping:
            if any(child.poll() is not None for child in children):
                raise RuntimeError('A FINN service exited; shutting down both services for host recovery.')
            time.sleep(.5)
        return 0
    finally:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
        for child in reversed(children):
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
