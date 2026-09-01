import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach the bearer token to every request so resource modules don't each
// have to pass headers by hand.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access');
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function forceLogout() {
  localStorage.removeItem('access');
  localStorage.removeItem('refresh');
  localStorage.removeItem('user');
  if (!window.location.pathname.startsWith('/giris')) {
    window.location.assign('/giris');
  }
}

// Aynı anda birden çok istek 401 alırsa tek bir refresh isteği yapılır;
// diğerleri o promise'i bekler.
let refreshing = null;

// Access token süresi dolduğunda (401) refresh token ile otomatik yenile ve
// isteği bir kez tekrar dene. Refresh de geçersizse oturumu kapat, login'e dön.
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const { response, config } = error;
    // Yalnızca kimlik uçları hariç tutulur (yenileme döngüsüne girmemek için).
    // /auth/me/ sıradan bir kaynak çağrısıdır; onun 401'i yenilenebilmeli.
    const isCredentialCall = ['/auth/login/', '/auth/refresh/', '/auth/logout/']
      .some((path) => config?.url?.includes(path));
    if (response?.status !== 401 || config?._retry || isCredentialCall) {
      return Promise.reject(error);
    }
    const refresh = localStorage.getItem('refresh');
    if (!refresh) {
      forceLogout();
      return Promise.reject(error);
    }
    config._retry = true;
    try {
      if (!refreshing) {
        // İnterceptor döngüsüne girmemek için ham axios kullan.
        refreshing = axios.post(`${baseURL}/auth/refresh/`, { refresh });
      }
      const { data } = await refreshing;
      refreshing = null;
      localStorage.setItem('access', data.access);
      config.headers.Authorization = `Bearer ${data.access}`;
      return api(config);
    } catch (e) {
      refreshing = null;
      forceLogout();
      return Promise.reject(e);
    }
  }
);

export default api;
