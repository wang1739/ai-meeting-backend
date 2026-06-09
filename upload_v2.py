import paramiko
import os

LOCAL_DIST = r'd:\Trae\AI smart\dist'
REMOTE_DIR = '/usr/share/nginx/html/ai-meeting'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
sftp = ssh.open_sftp()

# Clean and recreate
stdin, stdout, stderr = ssh.exec_command(f'rm -rf {REMOTE_DIR} && mkdir -p {REMOTE_DIR}', timeout=10)
stdout.read()
print('Cleaned')

def ensure_dir(path):
    """create dir on remote"""
    ssh.exec_command(f'mkdir -p {path}', timeout=5)

uploaded = 0
for root, dirs, files in os.walk(LOCAL_DIST):
    rel = os.path.relpath(root, LOCAL_DIST)
    remote = os.path.join(REMOTE_DIR, rel).replace('\\', '/')
    if rel != '.':
        ensure_dir(remote)
    for f in files:
        local = os.path.join(root, f)
        rem = os.path.join(remote, f).replace('\\', '/')
        sftp.put(local, rem)
        uploaded += 1

print(f'Uploaded {uploaded} files')

# Restart nginx
stdin, stdout, stderr = ssh.exec_command('nginx -s reload 2>/dev/null || nginx 2>/dev/null || systemctl reload nginx 2>/dev/null', timeout=10)
stdout.read()
print('Nginx reloaded')

sftp.close()
ssh.close()
print('[Done]')
