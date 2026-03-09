import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useEvents } from '@/hooks/useEvents';

export default function EventsScreen() {
  const router = useRouter();
  const { data, isLoading } = useEvents();

  return (
    <View style={s.container}>
      <TouchableOpacity style={s.createBtn} onPress={() => router.push('/(tabs)/events/create')}>
        <Text style={s.createBtnText}>+ Create Event</Text>
      </TouchableOpacity>
      {isLoading ? (
        <ActivityIndicator color="#fff" style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={data ?? []}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <TouchableOpacity style={s.row} onPress={() => router.push(`/(tabs)/events/${item.id}`)}>
              <Text style={s.name}>{item.name}</Text>
              <Text style={s.date}>{new Date(item.starts_at).toLocaleDateString()}</Text>
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
  createBtn: {
    margin: 16, backgroundColor: '#fff', borderRadius: 8,
    padding: 14, alignItems: 'center',
  },
  createBtnText: { color: '#000', fontWeight: '700', fontSize: 15 },
  row: { padding: 16 },
  name: { color: '#fff', fontSize: 16, fontWeight: '600' },
  date: { color: '#aaa', fontSize: 13, marginTop: 4 },
  sep: { height: 1, backgroundColor: '#1a1a1a' },
});
