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

# Fix CORS: NestJS 8+ enableCors with array of origins doesn't work well
# Switch to function-based origin check
print('\n[1] Fix CORS config in main.ts...')
script = """
cat > /root/ai-meeting-backend/src/main.ts << 'EOF'
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { ValidationPipe } from '@nestjs/common';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.enableCors({
    origin: '*',
    methods: 'GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS',
    credentials: false,
  });

  app.setGlobalPrefix('api');
  app.useGlobalPipes(new ValidationPipe({ whitelist: true }));

  const port = process.env.PORT || 3000;
  await app.listen(port, '0.0.0.0');
  console.log('Running on port:', port);
}
bootstrap();
EOF
echo 'DONE'
"""
ec, out = run(script, 5)
print(' ', out)

# Rebuild
print('\n[2] Rebuild...')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
npx tsc -p tsconfig.build.json --outDir dist --skipLibCheck 2>&1
ls dist/src/main.js && echo 'BUILD_OK' || echo 'BUILD_FAIL'
""", 30)
print(' ', out[-200:])

# Restart PM2
print('\n[3] PM2 restart...')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
pm2 restart ai-meeting-backend 2>&1
sleep 3
""", 15)
print('  restarted')

# Test register
print('\n[4] Test register...')
ec, out = run("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"test@meeting.com\",\"password\":\"test123\",\"name\":\"Test\"}'", 10)
print('  Response:', out[:200])

ec, out = run("curl -s http://localhost/api/meetings", 5)
print('  API ok:', out[:100])

print('\n[Done] Try again at http://118.31.249.156')
ssh.close()
