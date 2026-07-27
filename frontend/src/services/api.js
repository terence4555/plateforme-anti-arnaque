import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

async function ensureCsrf() {
  if (getCookie('csrftoken')) return;
  try {
    await axios.get('/api/auth/csrf/', { withCredentials: true });
  } catch {
    // ignore
  }
}

api.interceptors.request.use(async (config) => {
  const method = config.method?.toLowerCase();
  if (method === 'post' || method === 'put' || method === 'patch' || method === 'delete') {
    if (!getCookie('csrftoken')) {
      await ensureCsrf();
    }
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
  }
  return config;
});

export default api;
