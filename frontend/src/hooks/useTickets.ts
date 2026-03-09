import { useQuery } from '@tanstack/react-query'
import { getTickets } from '../api/tickets'

export function useTickets(eventId?: string) {
  return useQuery({
    queryKey: ['tickets', eventId],
    queryFn: () => getTickets(eventId),
  })
}
