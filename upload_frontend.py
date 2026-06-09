import paramiko
import os
import stat

LOCAL_DIST = r'd:\Trae\AI smart\dist'
REMOTE_DIR = '/usr/share/nginx/html/ai-meeting'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK] Connected')

sftp = ssh.open_sftp()

# Create remote directory
def ensure_dir(remote_path):
    try:
        sftp.stat(remote_path)
    except FileNotFoundError:
        prev = ''
        parts = remote_path.split('/')
        for i in range(2, len(parts) + 1):
            p = '/'.join(parts[:i])
            if p == '':
                continue
            try:
                sftp.stat(p)
            except FileNotFoundError:
                sftp.mkdir(p)
                print(f'  mkdir: {p}')

# Remove old files and recreate
stdin, stdout, stderr = ssh.exec_command(f'rm -rf {REMOTE_DIR} && mkdir -p {REMOTE_DIR}', timeout=10)
stdout.read()
print(f'Cleaned {REMOTE_DIR}')

# Walk local dist and upload
uploaded = 0
for root, dirs, files in os.walk(LOCAL_DIST):
    rel_path = os.path.relpath(root, LOCAL_DIST)
    remote_path = os.path.join(REMOTE_DIR, rel_path).replace('\\', '/')
    if rel_path != '.':
        ensure_dir(remote_path)
    for f in files:
        local_file = os.path.join(root, f)
        remote_file = os.path.join(remote_path, f).replace('\\', '/')
        try:
            sftp.put(local_file, remote_file)
            uploaded += 1
            if uploaded % 10 == 0:
                print(f'  Uploaded {uploaded} files...')
        except Exception as e:
            print(f'  Error uploading {f}: {e}')

print(f'[Done] Uploaded {uploaded} files to {REMOTE_DIR}')

# Verify
stdin, stdout, stderr = ssh.exec_command(f'ls -la {REMOTE_DIR}/index.html 2>/dev/null || echo MISSING', timeout=5)
out = stdout.read().decode(errors='replace').strip()
print(f'index.html: {out[:80]}')

sftp.close()
ssh.close()
