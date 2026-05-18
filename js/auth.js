// TalentMatch — Authentication & Navigation
const Auth = {
  login(email, password) {
    const user = DB.getUserByEmail(email);
    if (!user) return { ok: false, error: 'No account found with that email.' };
    if (user.password !== password) return { ok: false, error: 'Incorrect password.' };
    DB.setSession(user);
    return { ok: true, user };
  },

  register(data) {
    if (DB.getUserByEmail(data.email)) return { ok: false, error: 'An account with that email already exists.' };
    const user = {
      id: 'u' + Date.now(),
      type: data.type || 'candidate',
      isMember: false,
      name: data.name,
      email: data.email,
      password: data.password,
      mobile: data.mobile || '',
      // employer fields
      company: data.company || '',
      companyLogo: data.companyLogo || 'default',
      companyDescription: data.companyDescription || '',
      // candidate fields
      skills: [],
      workExperience: [],
      preferredWorkMode: '',
      preferredLocation: '',
      bio: '',
      location: '',
      educationLevel: '',
      fieldOfStudy: '',
      yearsOfExperience: ''
    };
    DB.addUser(user);
    DB.setSession(user);
    return { ok: true, user };
  },

  logout() {
    DB.clearSession();
    window.location.href = 'index.html';
  },

  getCurrentUser() { return DB.getCurrentUser(); },

  requireAuth(redirectTo = 'login.html') {
    if (!DB.getSession()) {
      window.location.href = redirectTo;
      return null;
    }
    return DB.getCurrentUser();
  },

  requireType(type, redirectTo = 'index.html') {
    const user = this.requireAuth();
    if (user && user.type !== type) {
      window.location.href = redirectTo;
      return null;
    }
    return user;
  }
};

// ── Navbar renderer ───────────────────────────────────────
function renderNavbar(activePage = '') {
  const user = Auth.getCurrentUser();
  const navEl = document.getElementById('navbar');
  if (!navEl) return;

  const memberBadge = user?.isMember ? '<span class="member-badge">PRO</span>' : '';

  const authSection = user
    ? `<div class="nav-user" id="navUserBtn">
         <div class="nav-avatar">${user.name.charAt(0).toUpperCase()}</div>
         <span>${user.name.split(' ')[0]}${memberBadge}</span>
         <span>▾</span>
         <div class="nav-dropdown" id="navDropdown">
           ${user.type === 'candidate' ? `
             <a href="profile.html">My Profile</a>
             <a href="find-jobs.html">Find Jobs</a>
             <a href="dashboard-candidate.html">Dashboard</a>
           ` : `
             <a href="employers.html">Post a Job</a>
             <a href="candidates.html">Browse Candidates</a>
             <a href="dashboard-employer.html">Dashboard</a>
           `}
           <a href="membership.html">Membership ${memberBadge}</a>
           <button onclick="Auth.logout()">Logout</button>
         </div>
       </div>`
    : `<a href="login.html" class="btn btn-outline btn-sm">Contact Us</a>
       <a href="login.html" class="btn btn-primary btn-sm">Login</a>`;

  navEl.innerHTML = `
    <nav class="navbar">
      <div class="navbar-inner">
        <a href="index.html" class="logo">
          <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
            <circle cx="13" cy="13" r="12" stroke="#4A6CF7" stroke-width="2"/>
            <circle cx="13" cy="13" r="4" fill="#4A6CF7"/>
            <line x1="13" y1="1" x2="13" y2="7" stroke="#4A6CF7" stroke-width="2"/>
            <line x1="13" y1="19" x2="13" y2="25" stroke="#4A6CF7" stroke-width="2"/>
            <line x1="1" y1="13" x2="7" y2="13" stroke="#4A6CF7" stroke-width="2"/>
            <line x1="19" y1="13" x2="25" y2="13" stroke="#4A6CF7" stroke-width="2"/>
          </svg>
          <div>TalentMatch<span class="logo-sub">AI powered Recruitment</span></div>
        </a>
        <div class="nav-links">
          <a href="index.html" class="${activePage === 'home' ? 'active' : ''}">Home</a>
          <a href="find-jobs.html" class="${activePage === 'jobs' ? 'active' : ''}">Find Jobs</a>
          <a href="employers.html" class="${activePage === 'employers' ? 'active' : ''}">Employers</a>
          <a href="profile.html" class="${activePage === 'profile' ? 'active' : ''}">My Profile</a>
          <a href="about.html" class="${activePage === 'about' ? 'active' : ''}">About Us</a>
        </div>
        <div class="nav-actions">${authSection}</div>
      </div>
    </nav>`;

  // Dropdown toggle
  const btn = document.getElementById('navUserBtn');
  const dd = document.getElementById('navDropdown');
  if (btn && dd) {
    btn.addEventListener('click', e => { e.stopPropagation(); dd.classList.toggle('open'); });
    document.addEventListener('click', () => dd.classList.remove('open'));
  }
}

function renderFooter() {
  const el = document.getElementById('footer');
  if (!el) return;
  el.innerHTML = `
    <footer class="footer">
      <div class="footer-grid">
        <div class="footer-brand">
          <a href="index.html" class="logo">
            <svg width="22" height="22" viewBox="0 0 26 26" fill="none">
              <circle cx="13" cy="13" r="12" stroke="#4A6CF7" stroke-width="2"/>
              <circle cx="13" cy="13" r="4" fill="#4A6CF7"/>
              <line x1="13" y1="1" x2="13" y2="7" stroke="#4A6CF7" stroke-width="2"/>
              <line x1="13" y1="19" x2="13" y2="25" stroke="#4A6CF7" stroke-width="2"/>
              <line x1="1" y1="13" x2="7" y2="13" stroke="#4A6CF7" stroke-width="2"/>
              <line x1="19" y1="13" x2="25" y2="13" stroke="#4A6CF7" stroke-width="2"/>
            </svg>
            TalentMatch
          </a>
          <p>Connecting talent with opportunity through intelligent matching.</p>
          <p class="call">Call now: <strong>+61 123 456 789</strong></p>
          <address>120 Liverpool Street, Sydney, NSW 0056, Australia</address>
        </div>
        <div class="footer-col">
          <h4>Quick Link</h4>
          <ul>
            <li><a href="about.html">About</a></li>
            <li><a href="#">Contact</a></li>
            <li><a href="login.html">Admin</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>Candidate</h4>
          <ul>
            <li><a href="find-jobs.html">Browse Jobs</a></li>
            <li><a href="employers.html">Browse Employers</a></li>
            <li><a href="dashboard-candidate.html">Candidate Dashboard</a></li>
            <li><a href="#">Saved Jobs</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>Employers</h4>
          <ul>
            <li><a href="employers.html">Post a Job</a></li>
            <li><a href="candidates.html">Browse Candidates</a></li>
            <li><a href="dashboard-employer.html">Employer Dashboard</a></li>
            <li><a href="#">Applications</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2025 TalentMatch – Job Portal. All rights reserved</p>
        <div class="social-links">
          <a href="#">f</a><a href="#">▶</a><a href="#">@</a><a href="#">in</a>
        </div>
      </div>
    </footer>`;
}
