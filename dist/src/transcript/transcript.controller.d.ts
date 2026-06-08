import { TranscriptService } from './transcript.service';
import { CreateTranscriptDto } from './dto/create-transcript.dto';
export declare class TranscriptController {
    private readonly transcriptService;
    constructor(transcriptService: TranscriptService);
    create(meetingId: string, dto: CreateTranscriptDto | CreateTranscriptDto[]): Promise<{
        id: string;
        createdAt: Date;
        meetingId: string;
        speakerLabel: string;
        text: string;
        startTimeMs: bigint;
        endTimeMs: bigint;
        isFinal: boolean;
    } | import("@prisma/client").Prisma.BatchPayload>;
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
