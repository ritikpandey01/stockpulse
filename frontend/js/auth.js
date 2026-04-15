// ========== Auth Logic (Sidebar-compatible) ==========
let authMode = 'login';
const ADMIN_EMAILS = ['ritikpandey.4161@gmail.com'];

function openAuthModal() {
    document.getElementById('auth-modal').classList.remove('hidden');
}

function closeAuthModal() {
    document.getElementById('auth-modal').classList.add('hidden');
    document.getElementById('auth-error').classList.add('hidden');
}

function switchAuthTab(mode) {
    authMode = mode;
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.auth-tab[onclick="switchAuthTab('${mode}')"]`).classList.add('active');
    document.getElementById('auth-submit-btn').innerText = mode === 'login' ? 'Login' : 'Sign Up';
    document.getElementById('auth-error').classList.add('hidden');
}

async function handleAuth(e) {
    e.preventDefault();
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    const errDiv = document.getElementById('auth-error');

    try {
        const res = await api.post(`/auth/${authMode}`, { email, password });
        if (res.access_token) {
            localStorage.setItem('supabase_token', res.access_token);
            closeAuthModal();
            checkAuth();
        } else if (res.message) {
            errDiv.innerText = res.message;
            errDiv.style.color = '#10B981'; // Green for success
            errDiv.classList.remove('hidden');
        } else {
            errDiv.innerText = res.error || "Error: Check credentials or Supabase rate limits.";
            errDiv.style.color = '#EF4444'; // Red for error
            errDiv.classList.remove('hidden');
        }
    } catch (err) {
        errDiv.innerText = err.message || "Network error. Please try again later.";
        errDiv.style.color = '#EF4444';
        errDiv.classList.remove('hidden');
    }
}

function logout() {
    localStorage.removeItem('supabase_token');
    checkAuth();
    navigate('dashboard');
}

async function checkAuth() {
    const token = localStorage.getItem('supabase_token');
    const loggedOut = document.getElementById('sidebar-logged-out');
    const loggedIn = document.getElementById('sidebar-logged-in');
    const adminLink = document.getElementById('admin-link');

    if (!token) {
        loggedOut.classList.remove('hidden');
        loggedIn.classList.add('hidden');
        adminLink.style.display = 'none';
        return;
    }

    try {
        const user = await api.get('/auth/me');
        if (user.email) {
            document.getElementById('user-email-display').innerText = user.email;
            document.getElementById('user-avatar').innerText = user.email[0].toUpperCase();
            loggedOut.classList.add('hidden');
            loggedIn.classList.remove('hidden');

            if (ADMIN_EMAILS.includes(user.email)) {
                adminLink.style.display = 'flex';
            } else {
                adminLink.style.display = 'none';
            }
        } else {
            throw new Error("Invalid token");
        }
    } catch (err) {
        logout();
    }
}
