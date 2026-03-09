import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getPeople, updatePersonStatus } from '@/api/people';

export function usePeople(status?: string) {
  return useQuery({
    queryKey: ['people', status],
    queryFn: () => getPeople(status),
  });
}

export function useUpdatePersonStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      updatePersonStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['people'] }),
  });
}
