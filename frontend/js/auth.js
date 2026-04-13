let authMode = 'login';
const ADMIN_EMAILS = ['admin@stockpulse.com']; // Sync with backend

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
        } else {
            errDiv.innerText = "Error: Please check your credentials or Supabase configuration";
            errDiv.classList.remove('hidden');
        }
    } catch (err) {
        errDiv.innerText = err.message;
        errDiv.classList.remove('hidden');
    }
}

function logout() {
    localStorage.removeItem('supabase_token');
    checkAuth();
    navigate('home');
}

async function checkAuth() {
    const token = localStorage.getItem('supabase_token');
    const loggedOutDiv = document.getElementById('user-area-logged-out');
    const loggedInDiv = document.getElementById('user-area-logged-in');
    const adminLink = document.getElementById('admin-link');
    
    if (!token) {
        loggedOutDiv.classList.remove('hidden');
        loggedInDiv.classList.add('hidden');
        adminLink.style.display = 'none';
        return;
    }

    try {
        const user = await api.get('/auth/me');
        if (user.email) {
            document.getElementById('user-email').innerText = user.email;
            loggedOutDiv.classList.add('hidden');
            loggedInDiv.classList.remove('hidden');
            
            // Show admin link if admin
            if (ADMIN_EMAILS.includes(user.email)) {
                adminLink.style.display = 'block';
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
