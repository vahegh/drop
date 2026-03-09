import { Tabs } from 'expo-router';

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarStyle: { backgroundColor: '#000', borderTopColor: '#222' },
        tabBarActiveTintColor: '#fff',
        tabBarInactiveTintColor: '#555',
        headerStyle: { backgroundColor: '#000' },
        headerTintColor: '#fff',
      }}
    >
      <Tabs.Screen name="people/index" options={{ title: 'People', tabBarLabel: 'People' }} />
      <Tabs.Screen name="events/index" options={{ title: 'Events', tabBarLabel: 'Events' }} />
      <Tabs.Screen name="checkin/index" options={{ title: 'Check-in', tabBarLabel: 'Scan' }} />
      <Tabs.Screen name="payments/index" options={{ title: 'Payments', tabBarLabel: 'Payments' }} />
    </Tabs>
  );
}
