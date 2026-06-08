import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateMessageDto } from './dto';

@Injectable()
export class ChatService {
  constructor(private readonly prisma: PrismaService) {}

  async create(meetingId: string, userId: string, dto: CreateMessageDto) {
    // Verify meeting exists
    const meeting = await this.prisma.meeting.findUnique({ where: { id: meetingId } });
    if (!meeting) throw new NotFoundException('Meeting not found');

    // Get user name
    const user = await this.prisma.user.findUnique({ where: { id: userId }, select: { name: true } });
    if (!user) throw new NotFoundException('User not found');

    return this.prisma.chatMessage.create({
      data: {
        meetingId,
        userId,
        userName: user.name,
        content: dto.content,
      },
    });
  }

  async findAll(meetingId: string) {
    return this.prisma.chatMessage.findMany({
      where: { meetingId },
      orderBy: { createdAt: 'asc' },
    });
  }
}
