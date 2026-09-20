import React from 'react';import {useAuth} from '../auth/AuthProvider.jsx';
export default function ProtectedRoute({children,fallback}){const{isAuthenticated}=useAuth();return isAuthenticated?children:(fallback||null)}
