import { PrismaService } from '../prisma/prisma.service';
export declare class MeetingReviewService {
    private prisma;
    constructor(prisma: PrismaService);
    getSummary(meetingId: string, userId: string): Promise<{
        oneLineSummary: string;
        detailedSummary: string;
        keyDecisions: string[];
        keywords: string[];
    } | null>;
    getActionItems(meetingId: string, userId: string): Promise<{
        id: string;
        description: string;
        assignee: string;
        dueDate: string | null;
        status: string;
    }[]>;
    updateActionItemStatus(meetingId: string, itemId: string, status: string): Promise<{
        id: string;
        createdAt: Date;
        assigneeUserId: string | null;
        status: string;
        meetingId: string;
        description: string;
        assigneeName: string | null;
        dueDate: Date | null;
        sourceSegmentId: bigint | null;
    }>;
}
