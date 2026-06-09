import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK] Connected')

def run(cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    return ec, out, err

# Check current state
ec, out, err = run("export PATH=/usr/local/bin:$PATH && node --version", 10)
print('Node:', out)

ec, out, err = run("ls /root/ai-meeting-backend/node_modules/.package-lock.json 2>/dev/null && echo 'EXISTS' || echo 'MISSING'", 10)
print('node_modules:', out)

if 'MISSING' in out:
    print('\n[1] Running npm install (background, may take 5+ min)...')
    # Run in background
    run("cd /root/ai-meeting-backend && nohup bash -c 'export PATH=/usr/local/bin:$PATH && rm -rf node_modules package-lock.json && npm install > /tmp/npm_install.log 2>&1 && echo INSTALL_OK >> /tmp/npm_install.log' &", 10)
    print('  Started background npm install...')
    
    # Wait for npm install to finish
    for i in range(30):
        time.sleep(20)
        ec, out, err = run("tail -3 /tmp/npm_install.log 2>/dev/null", 5)
        print(f'  [{i*20}s]', out[-80:] if out else 'waiting...')
        if 'INSTALL_OK' in out:
            break
else:
    print('\n[1] node_modules already exists')

# Prisma generate
print('\n[2] Prisma generate...')
ec, out, err = run("""
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
npx prisma generate 2>&1
""", 120)
print(' ', out[-200:])

# DB push
print('\n[3] Prisma db push...')
ec, out, err = run("""
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
npx prisma db push 2>&1
""", 60)
print(' ', out[-200:])

# Build
print('\n[4] Build...')
ec, out, err = run("""
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
npm run build 2>&1
""", 60)
print(' ', out[-200:])

# PM2 restart
print('\n[5] PM2 restart...')
ec, out, err = run("""
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1
pm2 save
sleep 2
curl -s http://localhost:3000/api/meetings
""", 30)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[:200])

# Final verify
time.sleep(2)
print('\n[6] Verify...')
ec, out, err = run("curl -s http://localhost/api/meetings", 10)
print('  Nginx:', out[:100])
ec, out, err = run("pg_isready && echo 'DB:OK' || echo 'DB:DOWN'", 5)
print('  DB:', out)
ec, out, err = run("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"admin@meeting.com\",\"password\":\"admin123\",\"name\":\"Admin\"}'", 10)
print('  Register:', out[:200])

print('\n' + '='*50)
print('[Done] http://118.31.249.156/api')
print('='*50)
ssh.close()
