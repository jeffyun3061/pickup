import { apiFetch } from '@/src/data/apiClient';

export type InquiryPayload = {
  email?: string;
  category: string;
  message: string;
};

export async function submitInquiry(payload: InquiryPayload): Promise<void> {
  await apiFetch('/api/v1/inquiries', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
