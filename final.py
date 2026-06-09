import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK] Connected')

def run(cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    return ec, out

# Check current state
ec, out = run("export PATH=/usr/local/bin:$PATH && node --version", 5)
print('Node:', out)

ec, out = run("ls /root/ai-meeting-backend/node_modules/.package-lock.json 2>/dev/null && echo 'EXISTS' || echo 'MISSING'", 5)
print('Modules:', out)

ec, out = run("pg_isready && echo 'OK' || echo 'DOWN'", 5)
print('PG:', out)

# 1. npm install if needed
if 'MISSING' in out:
    print('\n[1] npm install (background)...')
    stdin, stdout, stderr = ssh.exec_command("""
    cd /root/ai-meeting-backend
    export PATH=/usr/local/bin:$PATH
    nohup bash -c 'rm -rf node_modules package-lock.json 2>/dev/null; npm install > /tmp/npm.log 2>&1; echo DONE >> /tmp/npm.log' &
    """, timeout=10)
    print('  Started...')
    # Poll
    for i in range(20):
        time.sleep(30)
        ec, status = run("tail -1 /tmp/npm.log 2>/dev/null", 5)
        ts = time.strftime('%H:%M:%S')
        print(f'  [{ts}] {status[:80]}' if status else f'  [{ts}] ...')
        if 'DONE' in status:
            print('  npm install complete!')
            break
else:
    print('\n[1] Modules exist, skipping npm install')

# 2. Prisma generate
print('\n[2] Prisma generate...')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend && npx prisma generate 2>&1
""", 60)
print(' ', out[-200:])

# 3. DB push
print('\n[3] Prisma db push...')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend && npx prisma db push 2>&1
""", 60)
print(' ', out[-300:])

# 4. Build
print('\n[4] Nest build...')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend && npm run build 2>&1
""", 60)
print(' ', out[-200:])

# 5. PM2
print('\n[5] PM2 restart...')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1
pm2 save
sleep 2
curl -s http://localhost:3000/api/meetings
""", 20)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[:200])

# 6. Verify
time.sleep(2)
print('\n[6] Verify...')
ec, out = run("curl -s http://localhost/api/meetings", 10)
print('  Nginx:', out[:100])
ec, out = run("pg_isready && echo 'DB:OK' || echo 'DB:DOWN'", 5)
print('  DB:', out)
ec, out = run("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"admin@meeting.com\",\"password\":\"admin123\",\"name\":\"Admin\"}'", 10)
print('  Register:', out[:200])

print('\n[Done] http://118.31.249.156/api')
ssh.close()
