import paramiko, os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)

sftp = ssh.open_sftp()

# Files we modified on the server
files = [
    'src/main.ts',
    'src/auth/auth.module.ts',
]

for f in files:
    remote = f'/root/ai-meeting-backend/{f}'
    local = os.path.join(r'd:\Trae\ai-meeting-backend', f)
    os.makedirs(os.path.dirname(local), exist_ok=True)
    try:
        sftp.get(remote, local)
        print(f'Downloaded: {f}')
    except Exception as e:
        print(f'Failed {f}: {e}')

sftp.close()
ssh.close()
print('[Done]')
