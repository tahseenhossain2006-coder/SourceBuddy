import { AuthProvider } from '@/features/auth/AuthProvider';
import { AppRoutes } from '@/routes';

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}