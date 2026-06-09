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

# 1. Check dist structure
print('\n[1] Check dist structure:')
ec, out = run("ls /root/ai-meeting-backend/dist/src/main.js 2>/dev/null && echo 'OK' || echo 'MISSING'", 5)
print('  main.js:', out)

ec, out = run("find /root/ai-meeting-backend/dist -name '*.js' | head -10", 5)
print('  js files:', out[:300])

# 2. If main.js is missing (built to wrong dir), fix
ec, out = run("ls /root/ai-meeting-backend/dist/main.js 2>/dev/null && echo 'ROOT_OK' || echo 'ROOT_MISSING'", 5)
print('  dist/main.js:', out)

if 'ROOT_OK' in out:
    print('\n[2] dist/main.js is in root, not dist/src/. Fixing...')
    ec, out = run("""
    export PATH=/usr/local/bin:$PATH
    cd /root/ai-meeting-backend
    # Rebuild to proper structure
    npx tsc -p tsconfig.build.json --outDir dist 2>&1 | tail -5
    echo 'DONE'
    """, 30)
    print(' ', out)
    # Check again
    ec, out = run("ls /root/ai-meeting-backend/dist/src/main.js 2>/dev/null && echo 'SRC_OK' || echo 'SRC_MISSING'", 5)
    print('  dist/src/main.js:', out)

# 3. Start PM2
print('\n[3] Starting PM2...')
# First find the right main.js path
ec, out = run("find /root/ai-meeting-backend/dist -name 'main.js' -not -path '*/node_modules/*' 2>/dev/null", 5)
print('  Found main.js at:', out)

if out.strip():
    main_path = out.strip().split('\n')[0]
    # Get relative path from project root
    rel_path = main_path.replace('/root/ai-meeting-backend/', '')
    print(f'  Using: {rel_path}')
else:
    # Emergency: build from scratch with manual tsc
    print('  No main.js found! Rebuilding with manual tsc...')
    ec, out = run("""
    export PATH=/usr/local/bin:$PATH
    cd /root/ai-meeting-backend
    npx tsc --outDir dist --skipLibCheck 2>&1 | tail -5
    find dist -name 'main.js' 2>/dev/null
    """, 30)
    print(' ', out)

# 4. Start app
print('\n[4] Starting application...')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
MAIN_PATH=$(find dist -name 'main.js' -not -path '*/node_modules/*' 2>/dev/null | head -1)
echo "Main path: $MAIN_PATH"
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start "$MAIN_PATH" --name ai-meeting-backend -i 1 2>&1
pm2 save 2>&1
sleep 3
curl -s http://localhost:3000/api/meetings
""", 30)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[:300])

# 5. Final verify
time.sleep(2)
print('\n[5] Final verification...')
ec, out = run("curl -s http://localhost/api/meetings", 10)
print('  Nginx:', out[:100])
ec, out = run("pg_isready && echo 'DB:OK' || echo 'DB:DOWN'", 5)
print('  DB:', out)

print('\n[Done] http://118.31.249.156/api')
ssh.close()
