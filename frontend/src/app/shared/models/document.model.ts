export type DocumentType = 'CV' | 'JOB_OFFER';

export type ProcessingStatus = 'UPLOADED' | 'VALIDATING' | 'PROCESSING' | 'PROCESSED' | 'FAILED';

export interface DocumentSummary {
  id: string;
  document_type: DocumentType;
  original_filename: string;
  mime_type: string;
  file_size: number;
  status: ProcessingStatus;
  page_count: number | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentStatusResponse {
  id: string;
  status: ProcessingStatus;
  error: string | null;
  updated_at: string;
}
