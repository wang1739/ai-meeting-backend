import { Injectable, ForbiddenException, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateMeetingDto } from './dto';

@Injectable()
export class MeetingService {
  constructor(private prisma: PrismaService) {}

  async getActionItemsStats(userId: string) {
    const totalCount = await this.prisma.actionItem.count({
      where: {
        assigneeUserId: userId,
        status: { in: ['open', 'in_progress'] },
      },
    });
    return { totalCount };
  }

  async delete(id: string, userId: string) {
    const meeting = await this.prisma.meeting.findUnique({
      where: { id },
      select: { creatorId: true },
    });

    if (!meeting) {
      throw new NotFoundException('会议不存在');
    }

    if (meeting.creatorId !== userId) {
      throw new ForbiddenException('只能删除自己创建的会议');
    }

    await this.prisma.meeting.delete({
      where: { id },
    });

    return { message: '删除成功' };
  }

  async endMeeting(id: string, userId: string) {
    const meeting = await this.prisma.meeting.findUnique({
      where: { id },
      select: { creatorId: true },
    });

    if (!meeting) {
      throw new NotFoundException('会议不存在');
    }

    if (meeting.creatorId !== userId) {
      throw new ForbiddenException('只能结束自己创建的会议');
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

  async create(dto: CreateMeetingDto, userId: string) {
    // 将前端传入的字符串 startTime/endTime 转为 Date 对象
    const toDate = (time: string | undefined, date: string | undefined): Date | undefined => {
      if (!time && !date) return undefined;
      if (time && time.includes('T')) return new Date(time);        // 完整 ISO
      if (time && date) return new Date(`${date}T${time}`);         // date + time 拼接
      if (date) return new Date(`${date}T00:00:00`);               // 仅日期
      if (time) return new Date(time);                             // 仅时间（兜底）
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

  async findAll(userId: string) {
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

  async findOne(id: string, userId: string) {
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
      throw new NotFoundException('会议不存在');
    }

    const isCreator = meeting.creatorId === userId;
    const isParticipant = meeting.participants.some((p) => p.userId === userId);

    if (!isCreator && !isParticipant) {
      throw new ForbiddenException('无权访问此会议');
    }

    return meeting;
  }

  async getStats(userId: string) {
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
}
