export interface CreateMeetingDto {
  title: string;
  date?: string;
  startTime?: string;
  endTime?: string;
  backgroundInfo?: string;
  agenda?: string;
  participants?: {
    userId: string;
    role: 'host' | 'guest' | 'audience';
    isSpeaker: boolean;
  }[];
}
