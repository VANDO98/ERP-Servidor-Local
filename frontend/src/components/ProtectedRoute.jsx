import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ adminOnly = false }) => {
    // Auth OFF for testing
    // const { user, token } = useAuth();

    // if (!token || !user) {
    //     return <Navigate to="/login" replace />;
    // }

    // if (adminOnly && user?.role !== 'admin') {
    //    return <div className="p-8 text-center text-red-600 font-bold">Acceso Denegado: Requiere permisos de Administrador.</div>;
    // }

    return <Outlet />;
};

export default ProtectedRoute;
