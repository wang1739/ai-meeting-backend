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
exports.MeetingReviewService = void 0;
const common_1 = require("@nestjs/common");
const prisma_service_1 = require("../prisma/prisma.service");
let MeetingReviewService = class MeetingReviewService {
    prisma;
    constructor(prisma) {
        this.prisma = prisma;
    }
    async getSummary(meetingId, userId) {
        const meeting = await this.prisma.meeting.findUnique({
            where: { id: meetingId },
        });
        if (!meeting)
            throw new common_1.NotFoundException('会议不存在');
        const summaries = await this.prisma.meetingSummary.findMany({
            where: { meetingId },
        });
        if (summaries.length === 0) {
            return null;
        }
        const findSummary = (type) => summaries.find((s) => s.summaryType === type)?.content || '';
        let keyDecisions = [];
        try {
            keyDecisions = JSON.parse(findSummary('key_decisions'));
        }
        catch {
            keyDecisions = [];
        }
        let keywords = [];
        try {
            keywords = JSON.parse(findSummary('keywords'));
        }
        catch {
            keywords = [];
        }
        return {
            oneLineSummary: findSummary('one_line'),
            detailedSummary: findSummary('detailed'),
            keyDecisions,
            keywords,
        };
    }
    async getActionItems(meetingId, userId) {
        const meeting = await this.prisma.meeting.findUnique({
            where: { id: meetingId },
        });
        if (!meeting)
            throw new common_1.NotFoundException('会议不存在');
        const items = await this.prisma.actionItem.findMany({
            where: { meetingId },
        });
        return items.map((item) => ({
            id: item.id,
            description: item.description,
            assignee: item.assigneeName || '',
            dueDate: item.dueDate?.toISOString() || null,
            status: item.status === 'open' ? 'open' : item.status === 'in_progress' ? 'in_progress' : 'done',
        }));
    }
    async updateActionItemStatus(meetingId, itemId, status) {
        const meeting = await this.prisma.meeting.findUnique({
            where: { id: meetingId },
        });
        if (!meeting)
            throw new common_1.NotFoundException('会议不存在');
        const item = await this.prisma.actionItem.findUnique({
            where: { id: itemId },
        });
        if (!item)
            throw new common_1.NotFoundException('行动项不存在');
        const validStatuses = ['open', 'in_progress', 'done'];
        if (!validStatuses.includes(status)) {
            throw new common_1.NotFoundException('无效的状态值');
        }
        return this.prisma.actionItem.update({
            where: { id: itemId },
            data: { status },
        });
    }
};
exports.MeetingReviewService = MeetingReviewService;
exports.MeetingReviewService = MeetingReviewService = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [prisma_service_1.PrismaService])
], MeetingReviewService);
//# sourceMappingURL=meeting-review.service.js.map