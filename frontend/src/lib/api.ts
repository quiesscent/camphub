import axios from 'axios';

const BASE_URL = 'http://127.0.0.1:8000';

// API Documentation URLs
export const API_DOCS = {
    SWAGGER: `${BASE_URL}/api/docs/`,
    REDOC: `${BASE_URL}/api/redoc/`,
    SCHEMA: `${BASE_URL}/api/schema/`,
};

const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor for authentication
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Add a response interceptor for token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // If the error is 401 and we haven't retried yet
        if (error.response.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshToken = localStorage.getItem('refreshToken');
                const response = await axios.post(`${BASE_URL}/api/token/refresh/`, {
                    refresh: refreshToken,
                });

                const { access } = response.data;
                localStorage.setItem('accessToken', access);

                originalRequest.headers.Authorization = `Bearer ${access}`;
                return axios(originalRequest);
            } catch (error) {
                // If refresh token fails, logout user
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                window.location.href = '/login';
                return Promise.reject(error);
            }
        }

        return Promise.reject(error);
    }
);

export default api;
