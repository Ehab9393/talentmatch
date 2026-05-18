// TalentMatch API client — talks to the Flask backend
// Falls back to localStorage (DB.*) when the backend is unreachable.

const API_BASE = 'http://localhost:5000/api';

let _cachedUser = null;
let _backendAvailable = null; // null = unknown, true/false after first probe

const API = {
  // ── Token management ─────────────────────────────────────────────
  getToken() { return localStorage.getItem('tm_jwt'); },
  setToken(t) { localStorage.setItem('tm_jwt', t); },
  clearToken() { localStorage.removeItem('tm_jwt'); _cachedUser = null; },
  clearCache() { _cachedUser = null; },

  // ── Core request helper ──────────────────────────────────────────
  async request(method, path, body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = this.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);

    try {
      const res = await fetch(API_BASE + path, opts);
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw Object.assign(new Error(data.error || 'Request failed'), { status: res.status, data });
      return data;
    } catch (e) {
      if (e.name === 'TypeError') {
        // Network error — backend unavailable
        _backendAvailable = false;
        throw Object.assign(new Error('Backend unavailable'), { isNetworkError: true });
      }
      throw e;
    }
  },

  async probe() {
    if (_backendAvailable !== null) return _backendAvailable;
    try {
      await fetch(API_BASE + '/health', { method: 'GET', signal: AbortSignal.timeout(1500) });
      _backendAvailable = true;
    } catch {
      _backendAvailable = false;
    }
    return _backendAvailable;
  },

  // ── Auth ─────────────────────────────────────────────────────────
  async register(data) {
    const res = await this.request('POST', '/auth/register', data);
    if (res.token) { this.setToken(res.token); _cachedUser = res.user; }
    return res;
  },

  async login(email, password) {
    const res = await this.request('POST', '/auth/login', { email, password });
    if (res.token) { this.setToken(res.token); _cachedUser = res.user; }
    return res;
  },

  async logout() {
    this.clearToken();
    window.location.href = 'index.html';
  },

  async getMe() {
    if (_cachedUser) return _cachedUser;
    if (!this.getToken()) return null;
    try {
      _cachedUser = await this.request('GET', '/auth/me');
      return _cachedUser;
    } catch (e) {
      if (e.status === 401) this.clearToken();
      return null;
    }
  },

  async updateMe(data) {
    const res = await this.request('PUT', '/auth/me', data);
    _cachedUser = res;
    return res;
  },

  // ── Jobs ─────────────────────────────────────────────────────────
  async getJobs(params = {}) {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (Array.isArray(v)) v.forEach(i => qs.append(k, i));
      else if (v !== undefined && v !== null && v !== '') qs.append(k, v);
    });
    const q = qs.toString();
    return this.request('GET', '/jobs' + (q ? '?' + q : ''));
  },

  async getJob(id) { return this.request('GET', `/jobs/${id}`); },
  async createJob(data) { return this.request('POST', '/jobs', data); },
  async deleteJob(id) { return this.request('DELETE', `/jobs/${id}`); },
  async applyToJob(id) { return this.request('POST', `/jobs/${id}/apply`); },
  async toggleSaved(id) { return this.request('POST', `/jobs/${id}/saved`); },
  async getSavedIds() { return this.request('GET', '/saved'); },
  async getJobApplications(id) { return this.request('GET', `/jobs/${id}/applications`); },

  // ── Candidates ───────────────────────────────────────────────────
  async getCandidates(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request('GET', '/candidates' + (qs ? '?' + qs : ''));
  },
  async getCandidate(id) { return this.request('GET', `/candidates/${id}`); },

  // ── Recommendations ──────────────────────────────────────────────
  async getJobRecommendations() { return this.request('GET', '/recommendations/jobs'); },
  async getCandidateRecommendations(jobId) {
    return this.request('GET', '/recommendations/candidates' + (jobId ? `?jobId=${jobId}` : ''));
  },

  // ── Membership ───────────────────────────────────────────────────
  async toggleMembership() {
    const res = await this.request('POST', '/membership');
    _cachedUser = res.user;
    return res;
  },

  // ── My data ──────────────────────────────────────────────────────
  async getMyApplications() { return this.request('GET', '/my/applications'); },
  async getMyJobs() { return this.request('GET', '/my/jobs'); },
};

// ── Compatibility shim ────────────────────────────────────────────────────────
// Pages that used Auth.* / DB.* still work when backend is unavailable.
// This shim wraps API calls with a localStorage fallback.

const TM = {
  async getUser() {
    if (await API.probe()) {
      return API.getMe();
    }
    return Auth.getCurrentUser();
  },

  async requireAuth(redirectTo = 'login.html') {
    const user = await this.getUser();
    if (!user) { window.location.href = redirectTo; return null; }
    return user;
  },

  async getJobs(params = {}) {
    if (await API.probe()) return API.getJobs(params);
    let jobs = searchJobs(params.q || '', params);
    return jobs;
  },

  async applyToJob(jobId) {
    if (await API.probe()) {
      try { return await API.applyToJob(jobId); }
      catch (e) { return { ok: false, error: e.message }; }
    }
    const user = Auth.getCurrentUser();
    if (!user) return { ok: false, error: 'Not logged in' };
    const ok = DB.applyToJob(jobId, user.id);
    return ok ? { ok: true } : { ok: false, error: 'Already applied' };
  },

  async toggleSaved(jobId) {
    if (await API.probe()) return API.toggleSaved(jobId);
    const user = Auth.getCurrentUser();
    if (!user) return { saved: false };
    const saved = DB.toggleSaved(user.id, jobId);
    return { saved };
  },

  async getSavedIds() {
    if (await API.probe()) return API.getSavedIds();
    const user = Auth.getCurrentUser();
    return user ? DB.getSaved(user.id) : [];
  },
};
