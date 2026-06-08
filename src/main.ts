import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { ValidationPipe } from '@nestjs/common';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  const whitelist = [
    'http://localhost:5173',
    'https://ai-meeting-frontend.vercel.app',
  ];
  app.enableCors({
    origin: (origin, callback) => {
      if (!origin || whitelist.includes(origin)) {
        callback(null, true);
      } else {
        callback(new Error('Not allowed by CORS'));
      }
    },
    credentials: true,
  });

  app.setGlobalPrefix('api'); // 你要保留 /api，没问题
  app.useGlobalPipes(new ValidationPipe({ whitelist: true }));

  // ✅ 修复：用 Railway 的 PORT + 监听 0.0.0.0
  const port = process.env.PORT || 3000;
  await app.listen(port, '0.0.0.0');

  console.log('Running on port:', port);
}
bootstrap();
