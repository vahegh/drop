import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useEvent } from '@/hooks/useEvents';

export default function EventDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { data: event, isLoading } = useEvent(id);

  if (isLoading || !event) return <ActivityIndicator color="#fff" style={{ marginTop: 40 }} />;

  return (
    <View style={s.container}>
      <Text style={s.name}>{event.name}</Text>
      <Text style={s.meta}>Starts: {new Date(event.starts_at).toLocaleString()}</Text>
      <Text style={s.meta}>Ends: {new Date(event.ends_at).toLocaleString()}</Text>
      <Text style={s.meta}>Capacity: {event.max_capacity}</Text>
      <Text style={s.meta}>GA: {event.general_admission_price} AMD</Text>
      {event.early_bird_price && (
        <Text style={s.meta}>Early Bird: {event.early_bird_price} AMD</Text>
      )}
      <Text style={s.meta}>Member: {event.member_ticket_price} AMD</Text>
      <TouchableOpacity
        style={s.editBtn}
        onPress={() => router.push({ pathname: '/(tabs)/events/create', params: { id } })}
      >
        <Text style={s.editBtnText}>Edit Event</Text>
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000', padding: 24 },
  name: { color: '#fff', fontSize: 22, fontWeight: '700', marginBottom: 16 },
  meta: { color: '#aaa', fontSize: 14, marginBottom: 6 },
  editBtn: { marginTop: 32, backgroundColor: '#fff', borderRadius: 8, padding: 16, alignItems: 'center' },
  editBtnText: { color: '#000', fontWeight: '700', fontSize: 15 },
});
