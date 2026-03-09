import { View, Text, FlatList, StyleSheet, ActivityIndicator } from 'react-native';
import { usePayments } from '@/hooks/usePayments';

const STATUS_COLORS: Record<string, string> = {
  CREATED: '#555',
  CONFIRMED: '#1a6e3c',
  REJECTED: '#7a1010',
  REFUNDED: '#7a5500',
  PENDING: '#2a4e8c',
};

export default function PaymentsScreen() {
  const { data, isLoading } = usePayments();

  return (
    <View style={s.container}>
      {isLoading ? (
        <ActivityIndicator color="#fff" style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={data ?? []}
          keyExtractor={(item) => String(item.order_id)}
          renderItem={({ item }) => (
            <View style={s.row}>
              <View style={s.left}>
                <Text style={s.orderId}>#{item.order_id}</Text>
                <Text style={s.amount}>{item.amount} AMD · {item.provider}</Text>
                <Text style={s.date}>{new Date(item.created_at).toLocaleString()}</Text>
              </View>
              <View style={[s.badge, { backgroundColor: STATUS_COLORS[item.status] ?? '#333' }]}>
                <Text style={s.badgeText}>{item.status}</Text>
              </View>
            </View>
          )}
          ItemSeparatorComponent={() => <View style={s.sep} />}
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  left: { flex: 1 },
  orderId: { color: '#fff', fontWeight: '700', fontSize: 15 },
  amount: { color: '#aaa', fontSize: 13, marginTop: 2 },
  date: { color: '#555', fontSize: 12, marginTop: 2 },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12, marginLeft: 12 },
  badgeText: { color: '#fff', fontSize: 11 },
  sep: { height: 1, backgroundColor: '#1a1a1a' },
});
