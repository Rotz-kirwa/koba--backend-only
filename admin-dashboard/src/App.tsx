import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Orders from './pages/Orders';
import Products from './pages/Products';
import Users from './pages/Users';
import Payments from './pages/Payments';
import Login from './pages/Login';

function ProtectedAdmin({ children }: { children: ReactNode }) {
  const token = localStorage.getItem('admin_token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function AdminLayout() {
  return (
    <ProtectedAdmin>
      <div className="flex">
        <Sidebar />
        <div className="flex-1 bg-gray-50">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/products" element={<Products />} />
            <Route path="/users" element={<Users />} />
            <Route path="/payments" element={<Payments />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </ProtectedAdmin>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={<AdminLayout />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
