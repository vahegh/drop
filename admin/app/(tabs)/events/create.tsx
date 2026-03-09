import { useState } from 'react';
import {
  View, Text, TextInput, ScrollView, TouchableOpacity,
  StyleSheet, Alert, ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useEvent, useCreateEvent, useUpdateEvent } from '@/hooks/useEvents';

export default function CreateEventScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id?: string }>();
  const isEdit = !!id;

  const { data: existing } = useEvent(id ?? '');
  const { mutateAsync: create, isPending: creating } = useCreateEvent();
  const { mutateAsync: update, isPending: updating } = useUpdateEvent();

  const [form, setForm] = useState({
    name: existing?.name ?? '',
    starts_at: existing?.starts_at ?? '',
    ends_at: existing?.ends_at ?? '',
    venue_id: existing?.venue_id ?? '',
    image_url: existing?.image_url ?? '',
    description: existing?.description ?? '',
    general_admission_price: String(existing?.general_admission_price ?? ''),
    member_ticket_price: String(existing?.member_ticket_price ?? ''),
    max_capacity: String(existing?.max_capacity ?? ''),
    shared: String(existing?.shared ?? 'false'),
  });

  function set(key: string, val: string) {
    setForm((f) => ({ ...f, [key]: val }));
  }

  async function submit() {
    try {
      const body = {
        ...form,
        general_admission_price: parseInt(form.general_admission_price),
        member_ticket_price: parseInt(form.member_ticket_price),
        max_capacity: parseInt(form.max_capacity),
        shared: form.shared === 'true',
      };
      if (isEdit) {
        await update({ id: id!, body });
      } else {
        await create(body);
      }
      router.back();
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail ?? 'Failed');
    }
  }

  const loading = creating || updating;

  return (
    <ScrollView style={s.container} contentContainerStyle={s.content}>
      <Text style={s.heading}>{isEdit ? 'Edit Event' : 'Create Event'}</Text>
      {(
        [
          ['name', 'Name'],
          ['starts_at', 'Starts at (ISO)'],
          ['ends_at', 'Ends at (ISO)'],
          ['venue_id', 'Venue ID (UUID)'],
          ['image_url', 'Image URL'],
          ['description', 'Description'],
          ['general_admission_price', 'GA Price (AMD)'],
          ['member_ticket_price', 'Member Price (AMD)'],
          ['max_capacity', 'Capacity'],
          ['shared', 'Shared (true/false)'],
        ] as [string, string][]
      ).map(([key, label]) => (
        <View key={key}>
          <Text style={s.label}>{label}</Text>
          <TextInput
            style={s.input}
            value={form[key as keyof typeof form]}
            onChangeText={(v) => set(key, v)}
            placeholderTextColor="#555"
            autoCapitalize="none"
          />
        </View>
      ))}
      <TouchableOpacity style={s.btn} onPress={submit} disabled={loading}>
        {loading ? <ActivityIndicator color="#000" /> : <Text style={s.btnText}>{isEdit ? 'Save' : 'Create'}</Text>}
      </TouchableOpacity>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  content: { padding: 24, paddingBottom: 60 },
  heading: { color: '#fff', fontSize: 22, fontWeight: '700', marginBottom: 24 },
  label: { color: '#aaa', fontSize: 12, marginBottom: 4 },
  input: {
    backgroundColor: '#111', color: '#fff', borderRadius: 8, padding: 12,
    marginBottom: 14, fontSize: 15, borderWidth: 1, borderColor: '#333',
  },
  btn: { backgroundColor: '#fff', borderRadius: 8, padding: 16, alignItems: 'center', marginTop: 8 },
  btnText: { color: '#000', fontWeight: '700', fontSize: 16 },
});
