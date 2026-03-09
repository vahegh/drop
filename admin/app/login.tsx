import { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import * as SecureStore from 'expo-secure-store';
import { adminLogin } from '@/api/auth';
import { TOKEN_KEY } from '@/api/client';

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    if (!email || !password) return;
    setLoading(true);
    try {
      const { access_token } = await adminLogin(email, password);
      await SecureStore.setItemAsync(TOKEN_KEY, access_token);
      router.replace('/(tabs)/people');
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail ?? 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={s.container}>
      <Text style={s.title}>DROP Admin</Text>
      <TextInput
        style={s.input}
        placeholder="Admin email"
        placeholderTextColor="#666"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={s.input}
        placeholder="Password"
        placeholderTextColor="#666"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />
      <TouchableOpacity style={s.btn} onPress={handleLogin} disabled={loading}>
        {loading ? <ActivityIndicator color="#000" /> : <Text style={s.btnText}>Log in</Text>}
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000', justifyContent: 'center', padding: 24 },
  title: { color: '#fff', fontSize: 28, fontWeight: '700', marginBottom: 32, textAlign: 'center' },
  input: {
    backgroundColor: '#111', color: '#fff', borderRadius: 8, padding: 14,
    marginBottom: 12, fontSize: 16, borderWidth: 1, borderColor: '#333',
  },
  btn: {
    backgroundColor: '#fff', borderRadius: 8, padding: 16, alignItems: 'center', marginTop: 8,
  },
  btnText: { color: '#000', fontWeight: '700', fontSize: 16 },
});
