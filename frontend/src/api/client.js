import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach the access token to every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// When the access token expires (401), quietly get a new one with the refresh
// token and retry the request. If that fails too, send the user back to login.
const NO_REFRESH_URLS = ['/login/', '/register/', '/token/refresh/'];
let refreshPromise = null; // shared so several failing requests refresh only once

const refreshAccessToken = () => {
  if (!refreshPromise) {
    const refresh = localStorage.getItem('refresh_token');
    // plain axios (not `api`) so this call skips our own interceptors
    refreshPromise = axios
      .post('/api/token/refresh/', { refresh })
      .then((res) => {
        localStorage.setItem('access_token', res.data.access);
        if (res.data.refresh) {
          localStorage.setItem('refresh_token', res.data.refresh);
        }
        return res.data.access;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
};

const forceLogout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  // reloading shows the login screen because there is no token any more
  window.location.reload();
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    const isAuthCall = NO_REFRESH_URLS.some((u) => original?.url?.includes(u));
    const hasRefresh = Boolean(localStorage.getItem('refresh_token'));

    if (status === 401 && original && !original._retried && !isAuthCall && hasRefresh) {
      original._retried = true;
      try {
        const newAccess = await refreshAccessToken();
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api(original);
      } catch (refreshError) {
        forceLogout();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;