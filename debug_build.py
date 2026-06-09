import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

def run(cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    return ec, out

# 1. Check prisma.config.js
print('\n[1] prisma.config.js:')
ec, out = run('cat /root/ai-meeting-backend/prisma.config.js 2>/dev/null || echo NOT_FOUND', 5)
print(out[:300])

# Also check prisma.config.ts
print('\n[2] prisma.config.ts:')
ec, out = run('cat /root/ai-meeting-backend/prisma.config.ts 2>/dev/null || echo NOT_FOUND', 5)
print(out[:300])

# Check if there's a prisma directory
print('\n[3] Prisma dir:')
ec, out = run('ls -la /root/ai-meeting-backend/prisma/ 2>/dev/null || echo NO_PRISMA_DIR', 5)
print(out[:300])

# Check package.json prisma version
print('\n[4] Package.json prisma:')
ec, out = run('grep prisma /root/ai-meeting-backend/package.json 2>/dev/null', 5)
print(out[:200])

# Check node --version and prisma version
print('\n[5] Versions:')
ec, out = run('export PATH=/usr/local/bin:$PATH && node --version && npx prisma --version 2>&1 | head -3', 10)
print(out[:200])

# Check dotenv
print('\n[6] dotenv in node_modules:')
ec, out = run('ls /root/ai-meeting-backend/node_modules/dotenv 2>/dev/null && echo EXISTS || echo MISSING', 5)
print(out[:200])

ssh.close()
