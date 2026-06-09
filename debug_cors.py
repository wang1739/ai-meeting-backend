import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# Get full error log
stdin, stdout, stderr = ssh.exec_command('cat /root/.pm2/logs/ai-meeting-backend-error*.log 2>/dev/null | tail -50', timeout=10)
out = stdout.read().decode(errors='replace').strip()
print('Error log:', out[:1200])

# Check NestJS versions
stdin, stdout, stderr = ssh.exec_command('export PATH=/usr/local/bin:$PATH && cd /root/ai-meeting-backend && cat node_modules/@nestjs/core/package.json | grep version | head -1', timeout=5)
ver = stdout.read().decode(errors='replace').strip()
print('NestJS core:', ver)

ssh.close()
