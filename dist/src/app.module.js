"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AppModule = void 0;
const common_1 = require("@nestjs/common");
const config_1 = require("@nestjs/config");
const prisma_module_1 = require("./prisma/prisma.module");
const auth_module_1 = require("./auth/auth.module");
const meeting_module_1 = require("./meeting/meeting.module");
const meeting_review_module_1 = require("./meeting-review/meeting-review.module");
const ai_module_1 = require("./ai/ai.module");
const chat_module_1 = require("./chat/chat.module");
const transcript_module_1 = require("./transcript/transcript.module");
const schedule_controller_1 = require("./schedule/schedule.controller");
let AppModule = class AppModule {
};
exports.AppModule = AppModule;
exports.AppModule = AppModule = __decorate([
    (0, common_1.Module)({
        imports: [
            config_1.ConfigModule.forRoot({ isGlobal: true }),
            prisma_module_1.PrismaModule,
            auth_module_1.AuthModule,
            meeting_module_1.MeetingModule,
            meeting_review_module_1.MeetingReviewModule,
            ai_module_1.AiModule,
            chat_module_1.ChatModule,
            transcript_module_1.TranscriptModule,
        ],
        controllers: [schedule_controller_1.ScheduleController],
    })
], AppModule);
//# sourceMappingURL=app.module.js.map