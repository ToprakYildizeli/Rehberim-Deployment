import api from './client';

export function login(username, password) {
  return api.post('/auth/login/', { username, password });
}

export function registerCounselor(data) {
  return api.post('/auth/register/counselor/', data);
}

export function refreshToken(refresh) {
  return api.post('/auth/refresh/', { refresh });
}

export function logout(refresh, accessToken) {
  return api.post(
    '/auth/logout/',
    { refresh },
    { headers: { Authorization: `Bearer ${accessToken}` } }
  );
}

export function getMe(accessToken) {
  return api.get('/auth/me/', {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

/** PATCH /api/auth/me/ — ad/soyad/e-posta günceller, güncel kullanıcı objesini döner.
 *  Kısmi: yalnızca gönderilen alanlar değişir (auth-contract §5.4b). */
export async function updateMe(fields) {
  const { data } = await api.patch('/auth/me/', fields);
  return data;
}
