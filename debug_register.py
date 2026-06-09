import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

def run(cmd, timeout=30):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    return ec, out

# 1. Check PM2 logs
print('\n[1] PM2 logs (last 20 lines):')
ec, out = run('pm2 logs ai-meeting-backend --lines 20 --nostream 2>/dev/null || echo "no pm2 logs"', 10)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(safe[:800])

# 2. Check PostgreSQL status
print('\n[2] PostgreSQL:')
ec, out = run('pg_isready && echo "OK" || echo "DOWN"', 5)
print(' ', out)

# 3. Test DB connection from app
print('\n[3] Test register directly:')
ec, out = run('curl -s -v -X POST http://localhost/api/auth/register -H "Content-Type: application/json" -d \'{"email":"test@meeting.com","password":"test123","name":"Test"}\' 2>&1 | tail -20', 10)
print(' ', out[:500])

# 4. Check PM2 error log
print('\n[4] PM2 error log:')
ec, out = run('cat /root/.pm2/logs/ai-meeting-backend-error*.log 2>/dev/null | tail -30 || echo "no error log"', 10)
print(' ', out[:600])

# 5. Check if Prisma client works
print('\n[5] Test Prisma DB access:')
script = """
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
node -e "
const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();
p.user.count().then(c => console.log('User count:', c)).catch(e => console.error('Error:', e.message));
" 2>&1
"""
stdin, stdout, stderr = ssh.exec_command('bash -s', timeout=15)
stdin.write(script)
stdin.close()
out = stdout.read().decode(errors='replace').strip()
print(' ', out[:300])

ssh.close()
