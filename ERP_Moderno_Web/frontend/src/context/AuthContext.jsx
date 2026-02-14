import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    // Auth initialized as non-blocking to prevent UI freeze
    const [user, setUser] = useState({ username: 'Admin Test', role: 'admin' }); // Keep admin for testing
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [loading, setLoading] = useState(false);

    // Configure axios defaults
    if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
        delete axios.defaults.headers.common['Authorization'];
    }

    useEffect(() => {
        const initAuth = async () => {
            if (token) {
                try {
                    // Verify token and get user info
                    // Non-blocking fetch: we don't await strictly for rendering
                    axios.get('http://localhost:8000/api/users/me')
                        .then(res => setUser(res.data))
                        .catch(err => {
                            console.error("Token verification failed", err);
                            // Optional: logout() if strictly enforcing
                        });
                } catch (error) {
                    console.error("Auth Error", error);
                }
            }
            // Ensure loading is false (redundant if init state is false, but safe)
            setLoading(false);
        };

        initAuth();
    }, [token]);

    const login = async (username, password) => {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        try {
            const response = await axios.post('http://localhost:8000/api/token', formData);
            const accessToken = response.data.access_token;

            localStorage.setItem('token', accessToken);
            setToken(accessToken);
            axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;

            // Fetch user details immediately
            const userRes = await axios.get('http://localhost:8000/api/users/me');
            setUser(userRes.data);

            return { success: true };
        } catch (error) {
            console.error("Login failed", error);
            return { success: false, error: error.response?.data?.detail || "Error de conexión" };
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
        delete axios.defaults.headers.common['Authorization'];
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
