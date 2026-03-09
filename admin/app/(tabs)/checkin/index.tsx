import { useState } from 'react';
import { View, Text, StyleSheet, Alert, TouchableOpacity } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { checkIn } from '@/api/attendance';

export default function CheckInScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);

  async function handleBarcode({ data }: { data: string }) {
    if (scanned) return;
    setScanned(true);
    try {
      const res = await checkIn(data);
      setResult({ ok: true, message: res?.message ?? 'Checked in!' });
    } catch (e: any) {
      const msg = e?.response?.data?.detail ?? 'Check-in failed';
      setResult({ ok: false, message: msg });
    }
  }

  if (!permission) return <View style={s.container} />;

  if (!permission.granted) {
    return (
      <View style={s.container}>
        <Text style={s.text}>Camera permission required</Text>
        <TouchableOpacity style={s.btn} onPress={requestPermission}>
          <Text style={s.btnText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={s.container}>
      <CameraView
        style={s.camera}
        facing="back"
        onBarcodeScanned={scanned ? undefined : handleBarcode}
        barcodeScannerSettings={{ barcodeTypes: ['qr'] }}
      />
      {result && (
        <View style={[s.resultBox, result.ok ? s.success : s.failure]}>
          <Text style={s.resultText}>{result.message}</Text>
          <TouchableOpacity style={s.scanAgain} onPress={() => { setScanned(false); setResult(null); }}>
            <Text style={s.scanAgainText}>Scan again</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000', justifyContent: 'center' },
  camera: { flex: 1 },
  text: { color: '#fff', textAlign: 'center', marginBottom: 20 },
  btn: { backgroundColor: '#fff', borderRadius: 8, padding: 14, margin: 24, alignItems: 'center' },
  btnText: { color: '#000', fontWeight: '600' },
  resultBox: {
    position: 'absolute', bottom: 0, left: 0, right: 0,
    padding: 24, alignItems: 'center',
  },
  success: { backgroundColor: '#1a6e3c' },
  failure: { backgroundColor: '#7a1010' },
  resultText: { color: '#fff', fontSize: 16, fontWeight: '600', marginBottom: 12 },
  scanAgain: { backgroundColor: 'rgba(255,255,255,0.2)', borderRadius: 8, padding: 10 },
  scanAgainText: { color: '#fff', fontWeight: '600' },
});
