import { MeetingReviewService } from './meeting-review.service';
import { UpdateActionItemDto } from './dto/update-action-item.dto';
export declare class MeetingReviewController {
    private readonly reviewService;
    constructor(reviewService: MeetingReviewService);
    getSummary(id: string, req: any): Promise<{
        oneLineSummary: string;
        detailedSummary: string;
        keyDecisions: string[];
        keywords: string[];
    } | null>;
    getActionItems(id: string, req: any): Promise<{
        id: string;
        description: string;
        assignee: string;
        dueDate: string | null;
        status: string;
    }[]>;
    updateActionItem(id: string, itemId: string, dto: UpdateActionItemDto): Promise<{
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
