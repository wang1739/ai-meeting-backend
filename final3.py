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

DB_URL = 'postgresql://meeting_admin:Meeting@2024!@localhost:5432/ai_meeting?schema=public'

# 1. Ensure .env exists
print('\n[1] Create .env...')
ec, out = run(f"""cat > /root/ai-meeting-backend/.env << 'EOF'
DATABASE_URL={DB_URL}
JWT_SECRET=ai-meeting-jwt-secret-key-2024
JWT_EXPIRES_IN=7d
PORT=3000
NODE_ENV=production
EOF
cat /root/ai-meeting-backend/.env
""", 5)
print(' ', out)

# 2. Prisma db push with DATABASE_URL
print('\n[2] Prisma db push...')
ec, out = run(f"""
export PATH=/usr/local/bin:$PATH
export DATABASE_URL='{DB_URL}'
cd /root/ai-meeting-backend
npx prisma db push 2>&1
""", 60)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[-300:])

# 3. PM2 restart
print('\n[3] PM2 restart...')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1
pm2 save
sleep 3
curl -s http://localhost:3000/api/meetings
""", 20)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[:200])

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
