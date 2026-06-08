"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const core_1 = require("@nestjs/core");
const app_module_1 = require("./app.module");
const common_1 = require("@nestjs/common");
async function bootstrap() {
    const app = await core_1.NestFactory.create(app_module_1.AppModule);
    const whitelist = [
        'http://localhost:5173',
        'https://ai-meeting-frontend.vercel.app',
    ];
    app.enableCors({
        origin: (origin, callback) => {
            if (!origin || whitelist.includes(origin)) {
                callback(null, true);
            }
            else {
                callback(new Error('Not allowed by CORS'));
            }
        },
        credentials: true,
    });
    app.setGlobalPrefix('api');
    app.useGlobalPipes(new common_1.ValidationPipe({ whitelist: true }));
    const port = process.env.PORT || 3000;
    await app.listen(port, '0.0.0.0');
    console.log('Running on port:', port);
}
bootstrap();
//# sourceMappingURL=main.js.map