import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthProvider";
import { UserRole } from "./auth.types";

export function ProtectedRoute({
  role,
  children,
}: {
  role: UserRole;
  children: JSX.Element;
}) {
  const { token, role: userRole } = useAuth();

  if (!token) return <Navigate to="/login" replace />;
  if (userRole !== role) return <Navigate to="/login" replace />;

  return children;
}
