import { View, Text, StyleSheet, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { usePeople, useUpdatePersonStatus } from '@/hooks/usePeople';

export default function PersonDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: people, isLoading } = usePeople();
  const { mutate: updateStatus, isPending } = useUpdatePersonStatus();

  const person = people?.find((p: any) => p.id === id);

  function confirm(status: string) {
    Alert.alert('Confirm', `Set status to ${status}?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Yes', onPress: () => updateStatus({ id, status }) },
    ]);
  }

  if (isLoading || !person) return <ActivityIndicator color="#fff" style={{ marginTop: 40 }} />;

  return (
    <View style={s.container}>
      <Text style={s.name}>{person.first_name} {person.last_name}</Text>
      <Text style={s.meta}>{person.email}</Text>
      {person.instagram_handle && <Text style={s.meta}>@{person.instagram_handle}</Text>}
      {person.telegram_handle && <Text style={s.meta}>tg: {person.telegram_handle}</Text>}
      <View style={[s.badge, s[`badge_${person.status}` as keyof typeof s]]}>
        <Text style={s.badgeText}>{person.status}</Text>
      </View>

      <View style={s.actions}>
        {person.status !== 'verified' && (
          <TouchableOpacity style={[s.btn, s.btnVerify]} onPress={() => confirm('verified')} disabled={isPending}>
            <Text style={s.btnText}>Verify</Text>
          </TouchableOpacity>
        )}
        {person.status !== 'member' && (
          <TouchableOpacity style={[s.btn, s.btnMember]} onPress={() => confirm('member')} disabled={isPending}>
            <Text style={s.btnText}>Make Member</Text>
          </TouchableOpacity>
        )}
        {person.status !== 'rejected' && (
          <TouchableOpacity style={[s.btn, s.btnReject]} onPress={() => confirm('rejected')} disabled={isPending}>
            <Text style={s.btnText}>Reject</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000', padding: 24 },
  name: { color: '#fff', fontSize: 22, fontWeight: '700', marginBottom: 8 },
  meta: { color: '#aaa', fontSize: 14, marginBottom: 4 },
  badge: { alignSelf: 'flex-start', paddingHorizontal: 12, paddingVertical: 5, borderRadius: 14, marginTop: 12 },
  badge_pending: { backgroundColor: '#555' },
  badge_verified: { backgroundColor: '#1a6e3c' },
  badge_member: { backgroundColor: '#4a2fa0' },
  badge_rejected: { backgroundColor: '#7a1010' },
  badgeText: { color: '#fff', fontSize: 13 },
  actions: { marginTop: 32, gap: 12 },
  btn: { padding: 16, borderRadius: 10, alignItems: 'center' },
  btnVerify: { backgroundColor: '#1a6e3c' },
  btnMember: { backgroundColor: '#4a2fa0' },
  btnReject: { backgroundColor: '#7a1010' },
  btnText: { color: '#fff', fontWeight: '600', fontSize: 15 },
});
