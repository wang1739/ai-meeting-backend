import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# 1. Download Node 22
print('\n[1] Download Node.js 22...')
script = """
set -ex
cd /tmp
curl -fsSL --connect-timeout 30 --max-time 180 https://nodejs.org/dist/v22.12.0/node-v22.12.0-linux-x64.tar.xz -o node22.tar.xz
ls -lh node22.tar.xz
echo 'DOWNLOAD_OK'
"""
sin, sout, serr = ssh.exec_command('bash -s', timeout=240)
sin.write(script)
sin.close()
out = sout.read().decode(errors='replace').strip()
print(' ', out[-100:])

# 2. Install Node 22
print('\n[2] Install Node.js 22...')
script = """
set -ex
cd /tmp
tar -xf node22.tar.xz
cp -rf node-v22.12.0-linux-x64/* /usr/local/
/usr/local/bin/node --version
/usr/local/bin/npm --version
# Install pm2
npm install -g pm2 2>&1 | tail -3
echo 'NODE22_OK'
"""
sin, sout, serr = ssh.exec_command('bash -s', timeout=30)
sin.write(script)
sin.close()
print(' ', sout.read().decode(errors='replace').strip()[-100:])

# 3. npm install
print('\n[3] npm install...')
script = """
set -ex
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
node --version
rm -rf node_modules package-lock.json 2>/dev/null
npm install 2>&1 | tail -10
echo 'INSTALL_DONE'
"""
sin, sout, serr = ssh.exec_command('bash -s', timeout=600)
sin.write(script)
sin.close()
out = sout.read().decode(errors='replace').strip()
print(' ', ''.join(c if c.isascii() else '?' for c in out[-400:]))

# 4. Prisma generate + db push + build
print('\n[4] Prisma generate + db push + build...')
script = """
set -ex
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
npx prisma generate 2>&1 | tail -3
npx prisma db push 2>&1 | tail -3
npm run build 2>&1 | tail -5
echo 'BUILD_OK'
"""
sin, sout, serr = ssh.exec_command('bash -s', timeout=120)
sin.write(script)
sin.close()
out = sout.read().decode(errors='replace').strip()
print(' ', ''.join(c if c.isascii() else '?' for c in out[-400:]))

# 5. PM2 restart
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
print(' ', ''.join(c if c.isascii() else '?' for c in out[:200]))

# 6. Verify
time.sleep(2)
print('\n[6] Verify...')
_, out, _ = ssh.exec_command("curl -s http://localhost/api/meetings", timeout=10)
print('  Nginx:', out.read().decode(errors='replace').strip()[:100])
_, out, _ = ssh.exec_command("pg_isready && echo 'DB:OK' || echo 'DB:DOWN'", timeout=5)
print('  DB:', out.read().decode(errors='replace').strip())
_, out, _ = ssh.exec_command("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"admin@meeting.com\",\"password\":\"admin123\",\"name\":\"Admin\"}'", timeout=10)
print('  Register:', out.read().decode(errors='replace').strip()[:150])

print('\n[Done] http://118.31.249.156/api')
ssh.close()
