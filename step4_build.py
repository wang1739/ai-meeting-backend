import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

print('\n[1] Rebuild backend (npm install + prisma generate + db push + build)...')
script = """
set -ex
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
echo "Node: $(node --version)"
echo "NPM: $(npm --version)"

# Fix permissions
chmod -R 755 node_modules/.bin/ 2>/dev/null || true

# Reinstall
rm -rf node_modules package-lock.json 2>/dev/null
npm install 2>&1 | tail -5

npx prisma generate 2>&1
npx prisma db push 2>&1
npm run build 2>&1
echo 'STEP1_DONE'
"""
sin, sout, serr = ssh.exec_command('bash -s', timeout=180)
sin.write(script)
sin.close()
out = sout.read().decode(errors='replace').strip()
print(' ', ''.join(c if c.isascii() else '?' for c in out[-400:]))

# Restart PM2
print('\n[2] Restart PM2...')
script = """
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1
pm2 save
sleep 3
curl -s http://localhost:3000/api/meetings
"""
sin, sout, serr = ssh.exec_command('bash -s', timeout=60)
sin.write(script)
sin.close()
out = sout.read().decode(errors='replace').strip()
print(' ', out[-200:])

# Final test
time.sleep(2)
print('\n[3] Final test...')
_, out, _ = ssh.exec_command("curl -s http://localhost/api/meetings", timeout=10)
print('  Nginx:', out.read().decode(errors='replace').strip()[:100])

_, out, _ = ssh.exec_command("pg_isready && echo 'DB:OK' || echo 'DB:DOWN'", timeout=10)
print('  DB:', out.read().decode(errors='replace').strip())

_, out, _ = ssh.exec_command("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"admin@meeting.com\",\"password\":\"admin123\",\"name\":\"Admin\"}'", timeout=10)
print('  Register:', out.read().decode(errors='replace').strip()[:150])

print('\n[Done] http://118.31.249.156/api')
ssh.close()
