import { useQuery } from '@tanstack/react-query';
import { getPayments } from '@/api/payments';

export function usePayments() {
  return useQuery({ queryKey: ['payments'], queryFn: getPayments });
}
