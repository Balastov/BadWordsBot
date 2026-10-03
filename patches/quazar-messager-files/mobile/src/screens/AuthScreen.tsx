import React, {useState} from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import {authApi} from '../api/auth';
import {useAuthStore} from '../store/auth';
import {formatAuthError} from '../utils/authErrors';

export default function AuthScreen() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const setToken = useAuthStore(s => s.setToken);

  const submit = async () => {
    setError('');
    setLoading(true);
    try {
      const data =
        mode === 'login'
          ? await authApi.login(email.trim(), password)
          : await authApi.register(username.trim(), email.trim(), password);
      await setToken(data.access_token);
    } catch (err: unknown) {
      const detail = (err as {response?: {data?: {detail?: unknown}}})?.response?.data?.detail;
      setError(formatAuthError(detail));
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={s.root}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={s.card}>
        <Text style={s.logo}>Quazar</Text>

        <View style={s.tabs}>
          <Pressable
            style={[s.tab, mode === 'login' && s.activeTab]}
            onPress={() => setMode('login')}>
            <Text style={[s.tabText, mode === 'login' && s.activeTabText]}>Войти</Text>
          </Pressable>
          <Pressable
            style={[s.tab, mode === 'register' && s.activeTab]}
            onPress={() => setMode('register')}>
            <Text style={[s.tabText, mode === 'register' && s.activeTabText]}>Регистрация</Text>
          </Pressable>
        </View>

        {mode === 'register' && (
          <TextInput
            style={s.input}
            placeholder="Имя пользователя"
            placeholderTextColor="#555"
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
          />
        )}
        <TextInput
          style={s.input}
          placeholder="Email"
          placeholderTextColor="#555"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
        />
        <TextInput
          style={s.input}
          placeholder="Пароль"
          placeholderTextColor="#555"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />

        {error !== '' && <Text style={s.error}>{error}</Text>}

        <Pressable style={[s.submit, loading && s.disabled]} onPress={submit} disabled={loading}>
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={s.submitText}>
              {mode === 'login' ? 'Войти' : 'Создать аккаунт'}
            </Text>
          )}
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  root: {flex: 1, backgroundColor: '#0f1117', alignItems: 'center', justifyContent: 'center'},
  card: {width: '88%', maxWidth: 360},
  logo: {
    fontSize: 32,
    fontWeight: '700',
    color: '#6c63ff',
    textAlign: 'center',
    letterSpacing: 2,
    marginBottom: 32,
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: '#0f1117',
    borderRadius: 10,
    overflow: 'hidden',
    marginBottom: 20,
  },
  tab: {flex: 1, paddingVertical: 11, alignItems: 'center'},
  activeTab: {backgroundColor: '#6c63ff'},
  tabText: {color: '#888', fontWeight: '600', fontSize: 14},
  activeTabText: {color: '#fff'},
  input: {
    backgroundColor: '#1a1d27',
    borderWidth: 1,
    borderColor: '#2a2d3a',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: '#e0e0e0',
    fontSize: 14,
    marginBottom: 12,
  },
  error: {color: '#ff6b6b', fontSize: 13, marginBottom: 10},
  submit: {
    backgroundColor: '#6c63ff',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 4,
  },
  disabled: {opacity: 0.5},
  submitText: {color: '#fff', fontWeight: '700', fontSize: 15},
});
