import { PrismaService } from '../prisma/prisma.service';
import { CreateTranscriptDto } from './dto/create-transcript.dto';
export declare class TranscriptService {
    private readonly prisma;
    constructor(prisma: PrismaService);
    create(meetingId: string, dto: CreateTranscriptDto): Promise<{
        id: string;
        createdAt: Date;
        meetingId: string;
        speakerLabel: string;
        text: string;
        startTimeMs: bigint;
        endTimeMs: bigint;
        isFinal: boolean;
    }>;
    createBatch(meetingId: string, dtos: CreateTranscriptDto[]): Promise<import(".prisma/client").Prisma.BatchPayload>;
    findAll(meetingId: string): Promise<{
        startTimeMs: number;
        endTimeMs: number;
        id: string;
        createdAt: Date;
        meetingId: string;
        speakerLabel: string;
        text: string;
        isFinal: boolean;
    }[]>;
}
