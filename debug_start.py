import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

def run(cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    return ec, out

# 1. Check dist exists
print('\n[1] Check dist...')
ec, out = run("ls /root/ai-meeting-backend/dist/src/main.js 2>/dev/null && echo 'EXISTS' || echo 'MISSING'", 5)
print('  dist/main.js:', out)

# 2. Try starting app directly
print('\n[2] Try starting directly...')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
# Kill any previous
pkill -f "node dist" 2>/dev/null || true
sleep 1
# Start directly and capture output
timeout 10 node dist/src/main.js 2>&1 || true
""", 20)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[:500])

# 3. Check recent PM2 logs
print('\n[3] PM2 logs...')
ec, out = run("pm2 logs ai-meeting-backend --lines 20 --nostream 2>/dev/null || echo 'no logs'", 10)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[:500])

# 4. Check if dist was properly built
print('\n[4] Check dist files...')
ec, out = run("ls /root/ai-meeting-backend/dist/src/ 2>/dev/null | head -20", 5)
print(' ', out[:300])

# 5. If dist is missing, rebuild
if 'MISSING' in out:
    print('\n[5] Dist missing, rebuilding...')
    ec, out = run("""
    export PATH=/usr/local/bin:$PATH
    cd /root/ai-meeting-backend
    npm run build 2>&1
    """, 60)
    safe = ''.join(c if c.isascii() else '?' for c in out)
    print(' ', safe[-300:])

ssh.close()
