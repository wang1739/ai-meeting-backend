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

# Update Nginx config to serve both frontend and backend
nginx_conf = """server {{
    listen 80;
    server_name _;
    root /usr/share/nginx/html/ai-meeting;
    index index.html;

    location /api/ {{
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }}

    location /socket.io/ {{
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }}

    location / {{
        try_files $uri $uri/ /index.html;
    }}
}}
"""

run(f"cat > /etc/nginx/conf.d/ai-meeting.conf << 'EOF'\n{nginx_conf}\nEOF", 5)
print('Config written')

# Test and reload
ec, out = run('nginx -t 2>&1', 5)
print('nginx -t:', out[:200])

ec, out = run('nginx -s reload 2>/dev/null || systemctl reload nginx 2>/dev/null || nginx 2>/dev/null || true', 5)
print('Nginx reloaded')

# Verify
ec, out = run('curl -s http://localhost/api/meetings', 5)
print('API:', out[:100] if out else 'empty')

ec, out = run('curl -s http://localhost/ | head -5', 5)
print('Frontend:', out[:150] if out else 'empty')

print('\n[Done] http://118.31.249.156')
ssh.close()
