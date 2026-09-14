const AUTH_API = 'http://127.0.0.1:8000/api';
let accessToken = null;
let refreshToken = localStorage.getItem('emperator_refresh_token');

function authHeaders(extra = {}) {
  return accessToken ? { ...extra, Authorization: `Bearer ${accessToken}` } : extra;
}

async function authRequest(path, options = {}) {
  const response = await fetch(AUTH_API + path, {
    ...options,
    headers: authHeaders({ 'Content-Type': 'application/json', ...(options.headers || {}) })
  });
  return response;
}

async function saveTokens(data) {
  accessToken = data.access_token;
  refreshToken = data.refresh_token;
  localStorage.setItem('emperator_refresh_token', refreshToken);
}

async function doLogin(phone, password) {
  const r = await authRequest('/auth/login', { method: 'POST', body: JSON.stringify({ phone, password }) });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || 'ورود ناموفق بود');
  await saveTokens(data);
  return getMe();
}

async function doRegister(name, phone, password, restaurantName) {
  const r = await authRequest('/auth/register', { method: 'POST', body: JSON.stringify({ name, phone, password, restaurant_name: restaurantName }) });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || 'ثبت‌نام ناموفق بود');
  await saveTokens(data);
  return getMe();
}

async function refreshAccessToken() {
  if (!refreshToken) return false;
  const r = await fetch(AUTH_API + '/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  if (!r.ok) {
    accessToken = null;
    refreshToken = null;
    localStorage.removeItem('emperator_refresh_token');
    return false;
  }
  await saveTokens(await r.json());
  return true;
}

async function getMe() {
  const r = await authRequest('/auth/me');
  if (!r.ok) throw new Error('نشست کاربر معتبر نیست');
  return r.json();
}

async function doLogout() {
  if (refreshToken && accessToken) {
    await authRequest('/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) }).catch(() => {});
  }
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem('emperator_refresh_token');
  showAuthScreen();
}

function setUser(user) {
  const box = document.querySelector('.user');
  if (box) box.innerHTML = `${(user.name || 'ک').slice(0, 1)}<span>${user.role || 'کاربر'}</span>`;
}

function showAuthScreen() {
  document.getElementById('authScreen')?.classList.remove('hidden');
  document.querySelector('.app-shell')?.classList.add('locked');
}

function hideAuthScreen() {
  document.getElementById('authScreen')?.classList.add('hidden');
  document.querySelector('.app-shell')?.classList.remove('locked');
}

function setupAuthUI() {
  const form = document.getElementById('authForm');
  const mode = document.getElementById('authMode');
  const restaurant = document.getElementById('restaurantField');
  const title = document.getElementById('authTitle');
  const submit = document.getElementById('authSubmit');
  const switchBtn = document.getElementById('authSwitch');
  const error = document.getElementById('authError');

  switchBtn.onclick = () => {
    const register = mode.value !== 'register';
    mode.value = register ? 'register' : 'login';
    document.getElementById('nameField').classList.toggle('hidden', !register);
    restaurant.classList.toggle('hidden', !register);
    title.textContent = register ? 'ساخت حساب امپراتور' : 'ورود به امپراتور';
    submit.textContent = register ? 'ساخت حساب و ورود' : 'ورود';
    switchBtn.textContent = register ? 'قبلاً حساب دارم' : 'حساب جدید بساز';
    error.textContent = '';
  };

  form.onsubmit = async (event) => {
    event.preventDefault();
    error.textContent = '';
    submit.disabled = true;
    try {
      const fd = new FormData(form);
      const user = mode.value === 'register'
        ? await doRegister(fd.get('name'), fd.get('phone'), fd.get('password'), fd.get('restaurant_name'))
        : await doLogin(fd.get('phone'), fd.get('password'));
      setUser(user);
      hideAuthScreen();
      await refresh();
    } catch (e) {
      error.textContent = e.message || 'خطایی رخ داد';
    } finally {
      submit.disabled = false;
    }
  };

  document.getElementById('logoutBtn')?.addEventListener('click', doLogout);
}

document.addEventListener('DOMContentLoaded', async () => {
  setupAuthUI();
  showAuthScreen();
  if (await refreshAccessToken()) {
    try {
      const user = await getMe();
      setUser(user);
      hideAuthScreen();
      await refresh();
    } catch (_) {
      showAuthScreen();
    }
  }
});
