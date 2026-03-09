import { useQuery } from '@tanstack/react-query'
import { getMe } from '../api/auth'
import { getPersonStats } from '../api/people'

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    retry: false,
  })
}

export function usePeopleStats() {
  return useQuery({
    queryKey: ['people', 'stats'],
    queryFn: getPersonStats,
    staleTime: 1000 * 60 * 5,
  })
}
