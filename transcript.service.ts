import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateTranscriptDto } from './dto/create-transcript.dto';

@Injectable()
export class TranscriptService {
  constructor(private readonly prisma: PrismaService) {}

  async create(meetingId: string, dto: CreateTranscriptDto) {
    const meeting = await this.prisma.meeting.findUnique({ where: { id: meetingId } });
    if (!meeting) throw new NotFoundException('Meeting not found');

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

  async createBatch(meetingId: string, dtos: CreateTranscriptDto[]) {
    const meeting = await this.prisma.meeting.findUnique({ where: { id: meetingId } });
    if (!meeting) throw new NotFoundException('Meeting not found');

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

  async findAll(meetingId: string) {
    const segments = await this.prisma.transcriptionSegment.findMany({
      where: { meetingId },
      orderBy: { startTimeMs: 'asc' },
    });
    // BigInt 无法直接被 JSON.stringify 序列化，转为 number
    return segments.map((s) => ({
      ...s,
      startTimeMs: Number(s.startTimeMs),
      endTimeMs: Number(s.endTimeMs),
    }));
  }
}
