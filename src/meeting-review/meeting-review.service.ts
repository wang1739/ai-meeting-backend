import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class MeetingReviewService {
  constructor(private prisma: PrismaService) {}

  async getSummary(meetingId: string, userId: string) {
    const meeting = await this.prisma.meeting.findUnique({
      where: { id: meetingId },
    });
    if (!meeting) throw new NotFoundException('会议不存在');

    // 查询数据库中的摘要
    const summaries = await this.prisma.meetingSummary.findMany({
      where: { meetingId },
    });

    if (summaries.length === 0) {
      return null;
    }

    const findSummary = (type: string) =>
      summaries.find((s) => s.summaryType === type)?.content || '';

    let keyDecisions: string[] = [];
    try {
      keyDecisions = JSON.parse(findSummary('key_decisions'));
    } catch {
      keyDecisions = [];
    }

    let keywords: string[] = [];
    try {
      keywords = JSON.parse(findSummary('keywords'));
    } catch {
      keywords = [];
    }

    return {
      oneLineSummary: findSummary('one_line'),
      detailedSummary: findSummary('detailed'),
      keyDecisions,
      keywords,
    };
  }

  async getActionItems(meetingId: string, userId: string) {
    const meeting = await this.prisma.meeting.findUnique({
      where: { id: meetingId },
    });
    if (!meeting) throw new NotFoundException('会议不存在');

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

  async updateActionItemStatus(meetingId: string, itemId: string, status: string) {
    const meeting = await this.prisma.meeting.findUnique({
      where: { id: meetingId },
    });
    if (!meeting) throw new NotFoundException('会议不存在');

    const item = await this.prisma.actionItem.findUnique({
      where: { id: itemId },
    });
    if (!item) throw new NotFoundException('行动项不存在');

    const validStatuses = ['open', 'in_progress', 'done'];
    if (!validStatuses.includes(status)) {
      throw new NotFoundException('无效的状态值');
    }

    return this.prisma.actionItem.update({
      where: { id: itemId },
      data: { status },
    });
  }
}
