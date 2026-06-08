import { IsOptional, IsString, IsNotEmpty } from 'class-validator';

export class UpdateActionItemDto {
  @IsNotEmpty()
  @IsString()
  status: string;

  @IsOptional()
  @IsString()
  description?: string;

  @IsOptional()
  @IsString()
  assigneeName?: string;
}
