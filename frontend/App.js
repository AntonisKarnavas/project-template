import './global.css';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import LoginScreen from './screens/LoginScreen';
import SignupScreen from './screens/SignupScreen';
import { View, Text, TouchableOpacity, ActivityIndicator } from 'react-native';
import useFirebaseAuthStore from './store/firebaseAuthStore';
import { styled } from 'nativewind';
import { useEffect } from 'react';

const Stack = createNativeStackNavigator();

function HomeScreen() {
  const logout = useFirebaseAuthStore((state) => state.logout);
  return (
    <View className="flex-1 justify-center items-center bg-white">
      <Text className="text-2xl mb-4 font-bold">Welcome!</Text>
      <TouchableOpacity onPress={logout} className="bg-red-500 p-3 rounded-lg">
        <Text className="text-white font-bold">Logout</Text>
      </TouchableOpacity>
    </View>
  );
}

export default function App() {
  const user = useFirebaseAuthStore((state) => state.user);
  const isLoading = useFirebaseAuthStore((state) => state.isLoading);
  const initializeAuth = useFirebaseAuthStore((state) => state.initializeAuth);

  useEffect(() => {
    initializeAuth();
  }, []);

  if (isLoading) {
    return (
      <View className="flex-1 justify-center items-center bg-slate-900">
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          {user ? (
            <Stack.Screen name="Home" component={HomeScreen} />
          ) : (
            <>
              <Stack.Screen name="Login" component={LoginScreen} />
              <Stack.Screen name="Signup" component={SignupScreen} />
            </>
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
