import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { RoleProvider } from './context/RoleProvider';
import DashboardLayout from './components/layout/DashboardLayout';
import Welcome from './pages/Welcome';
import Login from './pages/Login';
import Register from './pages/Register';
import Panel from './pages/Panel';
import Ogrenciler from './pages/Ogrenciler';
import OgrenciDetay from './pages/OgrenciDetay';
import Takvim from './pages/Takvim';
import DersProgrami from './pages/DersProgrami';
import Ayarlar from './pages/Ayarlar';

function ProtectedRoute({ children }) {
  const { isLoggedIn } = useAuth();
  return isLoggedIn ? children : <Navigate to="/giris" replace />;
}

function GuestRoute({ children }) {
  const { isLoggedIn } = useAuth();
  return isLoggedIn ? <Navigate to="/panel" replace /> : children;
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <RoleProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<GuestRoute><Welcome /></GuestRoute>} />
              <Route path="/giris" element={<GuestRoute><Login /></GuestRoute>} />
              <Route path="/kayit" element={<GuestRoute><Register /></GuestRoute>} />

              <Route
                element={
                  <ProtectedRoute>
                    <DashboardLayout />
                  </ProtectedRoute>
                }
              >
                <Route path="/panel" element={<Panel />} />
                <Route path="/ogrenciler" element={<Ogrenciler />} />
                <Route path="/ogrenciler/:id" element={<OgrenciDetay />} />
                <Route path="/takvim" element={<Takvim />} />
                <Route path="/ders-programi" element={<DersProgrami />} />
                <Route path="/ayarlar" element={<Ayarlar />} />
              </Route>

              <Route path="/dashboard" element={<Navigate to="/panel" replace />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </RoleProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
