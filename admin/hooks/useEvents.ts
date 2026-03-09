import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getEvents, getEvent, createEvent, updateEvent } from '@/api/events';

export function useEvents() {
  return useQuery({ queryKey: ['events'], queryFn: getEvents });
}

export function useEvent(id: string) {
  return useQuery({ queryKey: ['events', id], queryFn: () => getEvent(id) });
}

export function useCreateEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => createEvent(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['events'] }),
  });
}

export function useUpdateEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) =>
      updateEvent(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['events'] }),
  });
}
