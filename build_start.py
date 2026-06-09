import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

def run(cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    return ec, out

# 1. Build
print('\n[1] Building...')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
npm run build 2>&1
""", 120)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[-400:])

# 2. Verify dist exists
ec, out = run("ls /root/ai-meeting-backend/dist/src/main.js && echo 'OK' || echo 'MISSING'", 5)
print('\n[2] dist/main.js:', out)

# 3. Start PM2
print('\n[3] Starting PM2...')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1 2>&1
pm2 save 2>&1
sleep 3
curl -s http://localhost:3000/api/meetings
""", 30)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[:300])

# 4. Verify
time.sleep(2)
print('\n[4] Verify...')
ec, out = run("curl -s http://localhost/api/meetings", 10)
print('  Nginx:', out[:100])
ec, out = run("pg_isready && echo 'DB:OK' || echo 'DB:DOWN'", 5)
print('  DB:', out)
ec, out = run("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"admin@meeting.com\",\"password\":\"admin123\",\"name\":\"Admin\"}'", 10)
print('  Register:', out[:200])

print('\n[Done] http://118.31.249.156/api')
ssh.close()
