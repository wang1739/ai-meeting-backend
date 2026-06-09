import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

def run(cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    return ec, out, err

# 1. Fix permissions for node_modules/.bin
print('\n[1] Fix permissions...')
ec, out, err = run("chmod -R 755 /root/ai-meeting-backend/node_modules/.bin/ 2>&1; echo 'done'", 15)
print('  done')

# 2. Prisma generate
print('\n[2] Prisma generate...')
ec, out, err = run("""
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
node --version
npx prisma generate 2>&1
""", 120)
print(' ', ''.join(c if c.isascii() else '?' for c in out[-300:]))

# 3. Prisma db push
print('\n[3] Prisma db push...')
ec, out, err = run("""
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
npx prisma db push 2>&1
""", 60)
print(' ', ''.join(c if c.isascii() else '?' for c in out[-300:]))

# 4. Build
print('\n[4] Nest build...')
ec, out, err = run("""
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
npx nest build 2>&1
""", 60)
print(' ', ''.join(c if c.isascii() else '?' for c in out[-200:]))

# 5. Restart PM2
print('\n[5] Restart PM2...')
ec, out, err = run("""
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1
pm2 save
sleep 2
echo 'PM2_OK'
""", 30)

# 6. Verify
time.sleep(2)
print('\n[6] Verify...')
ec, out, err = run('curl -s http://localhost:3000/api/meetings', 10)
print('  API(3000):', out[:80] if out else 'empty')

ec, out, err = run('curl -s http://localhost/api/meetings', 10)
print('  Nginx(80):', out[:80] if out else 'empty')

ec, out, err = run('pg_isready && echo "DB:OK" || echo "DB:DOWN"', 5)
print(' ', out)

ec, out, err = run("""
export PATH="/usr/local/bin:$PATH"
node --version
""", 5)
print('  Node:', out)

ec, out, err = run('curl -s -X POST http://localhost/api/auth/register -H "Content-Type: application/json" -d \'{"email":"admin@meeting.com","password":"admin123","name":"Admin"}\'', 10)
print('  Register:', out[:150] if out else 'empty')

print('\n' + '='*50)
print('[OK] http://118.31.249.156/api')
print('='*50)
ssh.close()
