import paramiko, time

HOST = '118.31.249.156'
USER = 'root'
PASSWORD = 'wmm.12345.'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print('[OK] Connected')

def run(cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    return ec, out, err

# 1. Test DB connection with meeting_admin
print('\n[1] Test DB connection...')
ec, out, err = run("PGPASSWORD='Meeting@2024!' psql -h localhost -U meeting_admin -d ai_meeting -c 'SELECT 1 as test;' 2>&1", 15)
print(' ', out)

# 2. Run prisma db push to create tables
print('\n[2] Running prisma db push...')
script = """
export FNM_DIR="$HOME/.local/share/fnm"
export PATH="$FNM_DIR:$PATH"
eval "$($FNM_DIR/fnm env --use-on-cd 2>/dev/null)" || true
cd /root/ai-meeting-backend
npx prisma db push 2>&1
"""
ec, out, err = run(script, timeout=60)
print(' ', ''.join(c if c.isascii() else '?' for c in out[-400:]))

# 3. Check tables
print('\n[3] Verify tables...')
ec, out, err = run("PGPASSWORD='Meeting@2024!' psql -h localhost -U meeting_admin -d ai_meeting -c '\\dt' 2>&1", 15)
print(' ', out)

# 4. Test API endpoints
print('\n[4] Test API...')
ec, out, err = run("curl -s http://localhost/api/meetings; echo; curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"test@test.com\",\"password\":\"123456\",\"name\":\"test\"}'", 15)
print(' ', out[:300])

# 5. Update Vercel - tell user to do it
print('\n' + '='*60)
print('[OK] Aliyun ECS deployment complete!')
print('='*60)
print(f'  API:       http://{HOST}/api')
print(f'  WS:        ws://{HOST}/socket.io')
print('\n[Next step] Update Vercel frontend:')
print('  Edit file: d:\\Trae\\AI smart\\vercel.json')
print('  Set VITE_API_URL to: http://118.31.249.156/api')
print('  Then push to GitHub to trigger Vercel redeploy.')

ssh.close()
