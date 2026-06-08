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
exports.MeetingService = void 0;
const common_1 = require("@nestjs/common");
const prisma_service_1 = require("../prisma/prisma.service");
let MeetingService = class MeetingService {
    prisma;
    constructor(prisma) {
        this.prisma = prisma;
    }
    async getActionItemsStats(userId) {
        const totalCount = await this.prisma.actionItem.count({
            where: {
                assigneeUserId: userId,
                status: { in: ['open', 'in_progress'] },
            },
        });
        return { totalCount };
    }
    async delete(id, userId) {
        const meeting = await this.prisma.meeting.findUnique({
            where: { id },
            select: { creatorId: true },
        });
        if (!meeting) {
            throw new common_1.NotFoundException('会议不存在');
        }
        if (meeting.creatorId !== userId) {
            throw new common_1.ForbiddenException('只能删除自己创建的会议');
        }
        await this.prisma.meeting.delete({
            where: { id },
        });
        return { message: '删除成功' };
    }
    async endMeeting(id, userId) {
        const meeting = await this.prisma.meeting.findUnique({
            where: { id },
            select: { creatorId: true },
        });
        if (!meeting) {
            throw new common_1.NotFoundException('会议不存在');
        }
        if (meeting.creatorId !== userId) {
            throw new common_1.ForbiddenException('只能结束自己创建的会议');
        }
        const updatedMeeting = await this.prisma.meeting.update({
            where: { id },
            data: {
                status: 'ended',
                endTime: new Date(),
            },
        });
        return updatedMeeting;
    }
    async create(dto, userId) {
        const toDate = (time, date) => {
            if (!time && !date)
                return undefined;
            if (time && time.includes('T'))
                return new Date(time);
            if (time && date)
                return new Date(`${date}T${time}`);
            if (date)
                return new Date(`${date}T00:00:00`);
            if (time)
                return new Date(time);
            return undefined;
        };
        const meeting = await this.prisma.meeting.create({
            data: {
                title: dto.title,
                date: dto.date,
                startTime: toDate(dto.startTime, dto.date),
                endTime: toDate(dto.endTime, dto.date),
                backgroundInfo: dto.backgroundInfo,
                agenda: dto.agenda,
                creatorId: userId,
                participants: dto.participants
                    ? {
                        create: dto.participants.map((p) => ({
                            userId: p.userId,
                            role: p.role,
                            isSpeaker: p.isSpeaker,
                        })),
                    }
                    : undefined,
            },
            include: {
                creator: { select: { id: true, name: true, email: true } },
                participants: {
                    include: { user: { select: { id: true, name: true, email: true } } },
                },
            },
        });
        return meeting;
    }
    async findAll(userId) {
        const meetings = await this.prisma.meeting.findMany({
            where: {
                OR: [
                    { creatorId: userId },
                    { participants: { some: { userId } } },
                ],
            },
            include: {
                creator: { select: { id: true, name: true, email: true } },
                participants: {
                    include: { user: { select: { id: true, name: true, email: true } } },
                },
            },
            orderBy: { createdAt: 'desc' },
        });
        return meetings;
    }
    async findOne(id, userId) {
        const meeting = await this.prisma.meeting.findUnique({
            where: { id },
            include: {
                creator: { select: { id: true, name: true, email: true } },
                participants: {
                    include: { user: { select: { id: true, name: true, email: true } } },
                },
            },
        });
        if (!meeting) {
            throw new common_1.NotFoundException('会议不存在');
        }
        const isCreator = meeting.creatorId === userId;
        const isParticipant = meeting.participants.some((p) => p.userId === userId);
        if (!isCreator && !isParticipant) {
            throw new common_1.ForbiddenException('无权访问此会议');
        }
        return meeting;
    }
    async getStats(userId) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const todayEnd = new Date(today);
        todayEnd.setDate(today.getDate() + 1);
        const weekStart = new Date(today);
        weekStart.setDate(today.getDate() - today.getDay());
        weekStart.setHours(0, 0, 0, 0);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekStart.getDate() + 7);
        const todayMeetings = await this.prisma.meeting.count({
            where: {
                OR: [
                    { creatorId: userId },
                    { participants: { some: { userId } } },
                ],
                startTime: {
                    gte: today,
                    lt: todayEnd,
                },
                status: {
                    not: 'cancelled',
                },
            },
        });
        const weekMeetings = await this.prisma.meeting.findMany({
            where: {
                OR: [
                    { creatorId: userId },
                    { participants: { some: { userId } } },
                ],
                startTime: {
                    gte: weekStart,
                    lt: weekEnd,
                },
                status: 'ended',
                endTime: {
                    not: null,
                },
            },
            select: {
                startTime: true,
                endTime: true,
            },
        });
        let totalMs = 0;
        weekMeetings.forEach((m) => {
            if (m.startTime && m.endTime) {
                totalMs += new Date(m.endTime).getTime() - new Date(m.startTime).getTime();
            }
        });
        const weekTotalHours = (totalMs / (1000 * 60 * 60)).toFixed(1);
        return {
            todayCount: todayMeetings,
            weekTotalHours,
        };
    }
};
exports.MeetingService = MeetingService;
exports.MeetingService = MeetingService = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [prisma_service_1.PrismaService])
], MeetingService);
//# sourceMappingURL=meeting.service.js.map