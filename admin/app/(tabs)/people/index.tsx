import { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { usePeople } from '@/hooks/usePeople';

const STATUSES = ['all', 'pending', 'verified', 'member', 'rejected'];

export default function PeopleScreen() {
  const router = useRouter();
  const [filter, setFilter] = useState<string | undefined>(undefined);
  const { data, isLoading } = usePeople(filter);

  return (
    <View style={s.container}>
      <View style={s.filters}>
        {STATUSES.map((st) => (
          <TouchableOpacity
            key={st}
            style={[s.pill, filter === (st === 'all' ? undefined : st) && s.pillActive]}
            onPress={() => setFilter(st === 'all' ? undefined : st)}
          >
            <Text style={s.pillText}>{st}</Text>
          </TouchableOpacity>
        ))}
      </View>
      {isLoading ? (
        <ActivityIndicator color="#fff" style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={data ?? []}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <TouchableOpacity style={s.row} onPress={() => router.push(`/(tabs)/people/${item.id}`)}>
              <Text style={s.name}>{item.first_name} {item.last_name}</Text>
              <View style={[s.badge, s[`badge_${item.status}` as keyof typeof s]]}>
                <Text style={s.badgeText}>{item.status}</Text>
              </View>
            </TouchableOpacity>
          )}
          ItemSeparatorComponent={() => <View style={s.sep} />}
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  filters: { flexDirection: 'row', flexWrap: 'wrap', padding: 12, gap: 8 },
  pill: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, backgroundColor: '#222' },
  pillActive: { backgroundColor: '#fff' },
  pillText: { color: '#fff', fontSize: 12 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  name: { color: '#fff', fontSize: 15 },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  badge_pending: { backgroundColor: '#555' },
  badge_verified: { backgroundColor: '#1a6e3c' },
  badge_member: { backgroundColor: '#4a2fa0' },
  badge_rejected: { backgroundColor: '#7a1010' },
  badgeText: { color: '#fff', fontSize: 11 },
  sep: { height: 1, backgroundColor: '#1a1a1a' },
});
