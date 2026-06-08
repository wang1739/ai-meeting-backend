import { IsString, IsNotEmpty, IsNumber, IsOptional, IsBoolean } from 'class-validator';

export class CreateTranscriptDto {
  @IsString()
  @IsNotEmpty()
  speakerLabel: string;

  @IsString()
  @IsNotEmpty()
  text: string;

  @IsNumber()
  startTimeMs: number;

  @IsNumber()
  endTimeMs: number;

  @IsBoolean()
  @IsOptional()
  isFinal?: boolean;
}
