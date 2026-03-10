import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import AdminDashboard from "./pages/admin/AdminDashboard";
import InternDashboard from "./pages/Intern/InternDashboard";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";


export default function App() {
return (
<AuthProvider>
<BrowserRouter>
<Routes>
<Route path="/login" element={<Login />} />
<Route
path="/admin"
element={
<ProtectedRoute role="admin">
<AdminDashboard />
</ProtectedRoute>
}
/>
<Route
path="/intern"
element={
<ProtectedRoute role="intern">
<InternDashboard />
</ProtectedRoute>
}
/>
<Route path="*" element={<Navigate to="/login" />} />
</Routes>
</BrowserRouter>
</AuthProvider>
);
}