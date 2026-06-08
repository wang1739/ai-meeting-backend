"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.TranscriptService = void 0;
const common_1 = require("@nestjs/common");
const prisma_service_1 = require("../prisma/prisma.service");
let TranscriptService = class TranscriptService {
    prisma;
    constructor(prisma) {
        this.prisma = prisma;
    }
    async create(meetingId, dto) {
        const meeting = await this.prisma.meeting.findUnique({ where: { id: meetingId } });
        if (!meeting)
            throw new common_1.NotFoundException('Meeting not found');
        return this.prisma.transcriptionSegment.create({
            data: {
                meetingId,
                speakerLabel: dto.speakerLabel,
                text: dto.text,
                startTimeMs: dto.startTimeMs,
                endTimeMs: dto.endTimeMs,
                isFinal: dto.isFinal ?? true,
            },
        });
    }
    async createBatch(meetingId, dtos) {
        const meeting = await this.prisma.meeting.findUnique({ where: { id: meetingId } });
        if (!meeting)
            throw new common_1.NotFoundException('Meeting not found');
        return this.prisma.transcriptionSegment.createMany({
            data: dtos.map((d) => ({
                meetingId,
                speakerLabel: d.speakerLabel,
                text: d.text,
                startTimeMs: d.startTimeMs,
                endTimeMs: d.endTimeMs,
                isFinal: d.isFinal ?? true,
            })),
        });
    }
    async findAll(meetingId) {
        const segments = await this.prisma.transcriptionSegment.findMany({
            where: { meetingId },
            orderBy: { startTimeMs: 'asc' },
        });
        return segments.map((s) => ({
            ...s,
            startTimeMs: Number(s.startTimeMs),
            endTimeMs: Number(s.endTimeMs),
        }));
    }
};
exports.TranscriptService = TranscriptService;
exports.TranscriptService = TranscriptService = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [prisma_service_1.PrismaService])
], TranscriptService);
//# sourceMappingURL=transcript.service.js.map