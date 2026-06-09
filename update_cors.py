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

# 1. Update CORS in main.ts
print('\n[1] Update CORS whitelist...')
ec, out = run("""
cat > /root/ai-meeting-backend/src/main.ts << 'EOF'
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { ValidationPipe } from '@nestjs/common';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.enableCors({
    origin: [
      'http://localhost:5173',
      'https://ai-meeting-frontend-orpin.vercel.app',
      'http://118.31.249.156',
    ],
    credentials: true,
  });

  app.setGlobalPrefix('api');
  app.useGlobalPipes(new ValidationPipe({ whitelist: true }));

  const port = process.env.PORT || 3000;
  await app.listen(port, '0.0.0.0');
  console.log('Running on port:', port);
}
bootstrap();
EOF
echo 'UPDATED'
""", 5)
print(' ', out)

# 2. Rebuild
print('\n[2] Rebuild...')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
npx tsc -p tsconfig.build.json --outDir dist --skipLibCheck 2>&1
echo 'REBUILD_DONE'
""", 30)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[-200:])

# 3. Restart PM2
print('\n[3] PM2 restart...')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
pm2 restart ai-meeting-backend 2>&1
pm2 save
sleep 2
curl -s http://localhost:3000/api/meetings
""", 20)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[:200])

# 4. Verify
time.sleep(2)
print('\n[4] Verify...')
ec, out = run("curl -s http://localhost/api/meetings", 10)
print('  API:', out[:100])
ec, out = run("pg_isready && echo 'DB:OK' || echo 'DB:DOWN'", 5)
print('  DB:', out)

print('\n[Done]')
print('Backend: http://118.31.249.156/api')
print('Frontend: https://ai-meeting-frontend-orpin.vercel.app')
ssh.close()
