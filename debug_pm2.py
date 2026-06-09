import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# 1. Check if dist/main.js is there
stdin, stdout, stderr = ssh.exec_command("ls -la /root/ai-meeting-backend/dist/src/main.js 2>/dev/null || echo 'MISSING'", timeout=5)
print('main.js:', stdout.read().decode(errors='replace').strip()[:100])

# 2. Check what PM2 says
stdin, stdout, stderr = ssh.exec_command("export PATH=/usr/local/bin:$PATH && pm2 list 2>&1", timeout=10)
out = stdout.read().decode(errors='replace').strip()
print('PM2:', ''.join(c if c.isascii() else '?' for c in out[:300]))

# 3. Try starting directly to see error
script = """
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
timeout 10 node dist/src/main.js 2>&1
"""
stdin, stdout, stderr = ssh.exec_command('bash -s', timeout=15)
stdin.write(script)
stdin.close()
out = stdout.read().decode(errors='replace').strip()
print('\nDirect start output:\n', out[:800])

# 4. Check if port 3000 is in use
stdin, stdout, stderr = ssh.exec_command("ss -tlnp | grep 3000", timeout=5)
print('\nPort 3000:', stdout.read().decode(errors='replace').strip()[:200])

ssh.close()
