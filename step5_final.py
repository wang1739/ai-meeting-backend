import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK] Connected')

# Check if node_modules exists
ec, out, _ = ssh.exec_command("ls /root/ai-meeting-backend/node_modules/.package-lock.json 2>/dev/null && echo 'EXISTS' || echo 'MISSING'", timeout=10)
out = out.read().decode(errors='replace').strip()
print('  node_modules:', out)

if 'MISSING' in out:
    print('\n[1] Reinstalling node_modules (this may take a while)...')
    script = """
set -ex
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
node --version
npm --version

# Reinstall - use --prefer-offline to speed up
npm install --prefer-offline 2>&1 | tail -10
echo 'NPM_DONE'
"""
    sin, sout, serr = ssh.exec_command('bash -s', timeout=600)
    sin.write(script)
    sin.close()
    out = sout.read().decode(errors='replace').strip()
    print(' ', out[-300:])

# Prisma generate
print('\n[2] Prisma generate...')
script = """
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
npx prisma generate 2>&1 | tail -5
"""
sin, sout, serr = ssh.exec_command('bash -s', timeout=120)
sin.write(script)
sin.close()
out = sout.read().decode(errors='replace').strip()
print(' ', out[-200:])

# DB push
print('\n[3] Prisma db push...')
script = """
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
npx prisma db push 2>&1 | tail -5
"""
sin, sout, serr = ssh.exec_command('bash -s', timeout=60)
sin.write(script)
sin.close()
out = sout.read().decode(errors='replace').strip()
print(' ', out[-200:])

# Build
print('\n[4] Nest build...')
script = """
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
npm run build 2>&1
"""
sin, sout, serr = ssh.exec_command('bash -s', timeout=60)
sin.write(script)
sin.close()
out = sout.read().decode(errors='replace').strip()
print(' ', out[-200:])

# PM2 restart
print('\n[5] PM2 restart...')
script = """
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1
pm2 save
sleep 3
curl -s http://localhost:3000/api/meetings
"""
sin, sout, serr = ssh.exec_command('bash -s', timeout=30)
sin.write(script)
sin.close()
out = sout.read().decode(errors='replace').strip()
print(' ', out[:200])

# Final verify
time.sleep(2)
print('\n[6] Verify...')
ec, out, _ = ssh.exec_command("curl -s http://localhost/api/meetings", timeout=10)
print('  Nginx:', out.read().decode(errors='replace').strip()[:100])

ec, out, _ = ssh.exec_command("pg_isready && echo 'DB:OK' || echo 'DB:DOWN'", timeout=5)
print('  DB:', out.read().decode(errors='replace').strip())

ec, out, _ = ssh.exec_command("""
export PATH="/usr/local/bin:$PATH"
node --version
""", timeout=5)
print('  Node:', out.read().decode(errors='replace').strip())

print('\n[Done] http://118.31.249.156/api')
ssh.close()
