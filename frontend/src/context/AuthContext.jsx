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

    // Session/Idle Logic
    const IDLE_TIMEOUT = 10 * 60 * 1000; // 10 minutes
    const WARNING_TIME = 60 * 1000; // 1 minute before timeout

    const [idleTimer, setIdleTimer] = useState(null);
    const [showSessionModal, setShowSessionModal] = useState(false);
    const [timeLeft, setTimeLeft] = useState(60);

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
        delete axios.defaults.headers.common['Authorization'];
        setShowSessionModal(false);
    };

    const resetIdleTimer = () => {
        if (!token) return;

        if (idleTimer) clearTimeout(idleTimer);

        // Timer for Warning
        const newTimer = setTimeout(() => {
            setShowSessionModal(true);
        }, IDLE_TIMEOUT - WARNING_TIME);

        setIdleTimer(newTimer);
    };

    // Activity Listeners
    useEffect(() => {
        if (!token) return;

        const events = ['mousemove', 'keydown', 'click', 'scroll'];
        const pinger = () => {
            if (!showSessionModal) resetIdleTimer();
        };

        events.forEach(e => window.addEventListener(e, pinger));
        resetIdleTimer();

        return () => {
            events.forEach(e => window.removeEventListener(e, pinger));
            if (idleTimer) clearTimeout(idleTimer);
        };
    }, [token, showSessionModal]);

    // Countdown when modal is open
    useEffect(() => {
        let interval;
        if (showSessionModal) {
            setTimeLeft(60);
            interval = setInterval(() => {
                setTimeLeft((prev) => {
                    if (prev <= 1) {
                        clearInterval(interval);
                        logout();
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [showSessionModal]);

    const extendSession = () => {
        setShowSessionModal(false);
        resetIdleTimer();
        // Optional: Ping server to check token validity
        axios.get('/api/users/me').catch(() => logout());
    };

    useEffect(() => {
        const initAuth = async () => {
            if (token) {
                try {
                    axios.get('/api/users/me')
                        .then(res => setUser(res.data))
                        .catch(err => {
                            console.error("Token verification failed", err);
                            logout();
                        });
                } catch (error) {
                    console.error("Auth Error", error);
                }
            }
            setLoading(false);
        };

        initAuth();
    }, [token]);

    const login = async (username, password) => {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        try {
            const response = await axios.post('/api/token', formData);
            const accessToken = response.data.access_token;

            localStorage.setItem('token', accessToken);
            setToken(accessToken);
            axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;

            const userRes = await axios.get('/api/users/me');
            setUser(userRes.data);

            return { success: true };
        } catch (error) {
            console.error("Login failed", error);
            return { success: false, error: error.response?.data?.detail || "Error de conexión" };
        }
    };

    // Logout defined above

    return (
        <AuthContext.Provider value={{ user, token, login, logout, loading }}>
            {!loading && children}

            {/* Session Timeout Modal */}
            {showSessionModal && (
                <div className="fixed inset-0 bg-black/50 z-[9999] flex items-center justify-center p-4">
                    <div className="bg-white rounded-lg shadow-xl p-6 max-w-sm w-full animate-in fade-in zoom-in">
                        <h3 className="text-lg font-bold text-slate-800 mb-2">⏳ Tu sesión va a expirar</h3>
                        <p className="text-slate-600 mb-4">
                            Por seguridad, tu sesión se cerrará en <span className="font-bold text-red-500">{timeLeft} segundos</span> por inactividad.
                        </p>
                        <p className="text-sm text-slate-500 mb-6">¿Deseas mantenerte conectado?</p>

                        <div className="flex space-x-3">
                            <button
                                onClick={logout}
                                className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded hover:bg-slate-50"
                            >
                                Salir
                            </button>
                            <button
                                onClick={extendSession}
                                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-medium"
                            >
                                Continuar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
