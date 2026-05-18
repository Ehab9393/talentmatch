// TalentMatch — Search Engine (keyword, filter, fuzzy, synonyms)

const SYNONYMS = {
  'programmer': ['developer', 'software engineer', 'coder', 'engineer', 'coding'],
  'coder': ['developer', 'programmer', 'software engineer', 'coding'],
  'developer': ['programmer', 'software engineer', 'coder', 'engineer'],
  'software engineer': ['developer', 'programmer', 'coder', 'engineer'],
  'ui designer': ['ux designer', 'product designer', 'visual designer', 'ui/ux', 'designer'],
  'ux designer': ['ui designer', 'product designer', 'ui/ux', 'designer'],
  'data scientist': ['data analyst', 'ml engineer', 'machine learning', 'analytics'],
  'data analyst': ['data scientist', 'analytics', 'business analyst'],
  'frontend': ['front-end', 'front end', 'ui developer', 'react developer', 'javascript developer'],
  'backend': ['back-end', 'back end', 'server-side', 'api developer'],
  'fullstack': ['full-stack', 'full stack', 'frontend', 'backend'],
  'devops': ['cloud engineer', 'infrastructure engineer', 'sre', 'platform engineer'],
  'marketing': ['digital marketing', 'growth', 'seo', 'content marketing'],
  'manager': ['lead', 'head', 'director', 'vp'],
  'intern': ['internship', 'graduate', 'entry level', 'fresher'],
  'it': ['information technology', 'tech', 'technical', 'software', 'computing', 'computer science', 'engineer', 'developer'],
  'information technology': ['it', 'tech', 'software', 'computer science', 'engineering'],
  'tech': ['it', 'technology', 'software', 'engineering', 'developer'],
  'cybersecurity': ['cyber security', 'security', 'information security', 'infosec', 'network security', 'penetration testing', 'ethical hacking'],
  'cyber security': ['cybersecurity', 'security', 'infosec', 'information security'],
  'infosec': ['cybersecurity', 'cyber security', 'information security', 'security'],
  'security': ['cybersecurity', 'infosec', 'information security', 'network security'],
  'network': ['networking', 'network engineer', 'network security', 'infrastructure'],
  'cloud': ['aws', 'gcp', 'azure', 'devops', 'infrastructure', 'cloud engineer'],
  'mobile': ['ios', 'android', 'react native', 'flutter', 'app developer'],
  'ai': ['artificial intelligence', 'machine learning', 'deep learning', 'ml', 'data science'],
  'machine learning': ['ai', 'artificial intelligence', 'deep learning', 'data science', 'ml engineer'],
};

function levenshtein(a, b) {
  const m = a.length, n = b.length;
  const dp = Array.from({ length: m + 1 }, (_, i) => [i]);
  for (let j = 1; j <= n; j++) dp[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] = a[i - 1] === b[j - 1]
        ? dp[i - 1][j - 1]
        : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
    }
  }
  return dp[m][n];
}

function fuzzyWordMatch(word, target, threshold = 0.72) {
  if (target.includes(word) || word.includes(target)) return true;
  if (word.length < 3 || target.length < 3) return word === target;
  const maxLen = Math.max(word.length, target.length);
  return (1 - levenshtein(word, target) / maxLen) >= threshold;
}

function expandQuery(query) {
  const q = query.toLowerCase().trim();
  const terms = new Set([q]);
  const qWords = q.split(/\s+/);

  Object.entries(SYNONYMS).forEach(([key, syns]) => {
    const keyWords = key.split(/\s+/);
    // Match if query equals the key, or query contains all words of the key, or key equals query
    const qMatchesKey = q === key || keyWords.every(kw => qWords.includes(kw));
    const keyMatchesQ = key === q || qWords.every(qw => keyWords.includes(qw));

    if (qMatchesKey || keyMatchesQ) {
      syns.forEach(s => terms.add(s));
      terms.add(key);
    }

    syns.forEach(s => {
      const sWords = s.split(/\s+/);
      const qMatchesSyn = q === s || sWords.every(sw => qWords.includes(sw));
      if (qMatchesSyn) {
        terms.add(key);
        syns.forEach(ss => terms.add(ss));
      }
    });
  });
  return [...terms];
}

function jobMatchesQuery(job, query) {
  if (!query || !query.trim()) return true;
  const q = query.toLowerCase().trim();
  const expanded = expandQuery(q);

  const searchable = [
    job.title, job.company, job.description?.replace(/<[^>]+>/g, ''),
    (job.tags || []).join(' '), (job.requiredSkills || []).join(' '),
    job.jobRole, job.jobFunction, job.location, job.city, job.country
  ].join(' ').toLowerCase();

  // Exact or substring match
  if (expanded.some(t => searchable.includes(t))) return true;

  // Fuzzy word-by-word match
  const qWords = q.split(/\s+/);
  const textWords = searchable.split(/\s+/).filter(w => w.length >= 3);
  return qWords.every(qw =>
    textWords.some(tw => fuzzyWordMatch(qw, tw))
  );
}

function candidateMatchesQuery(candidate, query) {
  if (!query || !query.trim()) return true;
  const q = query.toLowerCase().trim();
  const expanded = expandQuery(q);

  const searchable = [
    candidate.name, candidate.bio,
    (candidate.skills || []).join(' '),
    candidate.fieldOfStudy, candidate.educationLevel,
    candidate.location, candidate.preferredLocation,
    (candidate.workExperience || []).map(w => `${w.title} ${w.company} ${w.description}`).join(' ')
  ].join(' ').toLowerCase();

  if (expanded.some(t => searchable.includes(t))) return true;

  const qWords = q.split(/\s+/);
  const textWords = searchable.split(/\s+/).filter(w => w.length >= 3);
  return qWords.every(qw => textWords.some(tw => fuzzyWordMatch(qw, tw)));
}

// ── Job Search ────────────────────────────────────────────
function searchJobs(query, filters = {}) {
  let jobs = DB.getJobs();

  // Keyword + fuzzy
  if (query && query.trim()) {
    jobs = jobs.filter(j => jobMatchesQuery(j, query));
  }

  // Filters
  if (filters.jobType && filters.jobType.length) {
    jobs = jobs.filter(j => filters.jobType.includes(j.jobType));
  }
  if (filters.workMode && filters.workMode.length) {
    jobs = jobs.filter(j => filters.workMode.includes(j.workMode));
  }
  if (filters.jobFunction && filters.jobFunction.length) {
    jobs = jobs.filter(j => filters.jobFunction.includes(j.jobFunction));
  }
  if (filters.experienceLevel && filters.experienceLevel.length) {
    jobs = jobs.filter(j => filters.experienceLevel.includes(j.jobLevel));
  }
  if (filters.minSalary && !isNaN(filters.minSalary)) {
    jobs = jobs.filter(j => j.maxSalary >= Number(filters.minSalary));
  }
  if (filters.maxSalary && !isNaN(filters.maxSalary)) {
    jobs = jobs.filter(j => j.minSalary <= Number(filters.maxSalary));
  }
  if (filters.location && filters.location.trim()) {
    const loc = filters.location.toLowerCase().trim();
    jobs = jobs.filter(j =>
      (j.city || '').toLowerCase().includes(loc) ||
      (j.country || '').toLowerCase().includes(loc) ||
      (j.location || '').toLowerCase().includes(loc)
    );
  }
  if (filters.experience && filters.experience.trim()) {
    const exp = parseInt(filters.experience);
    // Only filter when exp > 0; value of 0 means "no filter" (user hasn't set a preference)
    if (!isNaN(exp) && exp > 0) {
      jobs = jobs.filter(j => parseInt(j.requiredExperience || 0) <= exp);
    }
  }

  // Sort
  if (filters.sort === 'salary-high') {
    jobs.sort((a, b) => b.maxSalary - a.maxSalary);
  } else if (filters.sort === 'salary-low') {
    jobs.sort((a, b) => a.minSalary - b.minSalary);
  } else if (filters.sort === 'recent') {
    jobs.sort((a, b) => new Date(b.postedAt) - new Date(a.postedAt));
  } else {
    // Popular default
    jobs.sort((a, b) => (b.applicants || 0) - (a.applicants || 0));
  }

  return jobs;
}

// ── Candidate Search ──────────────────────────────────────
function searchCandidates(query, filters = {}) {
  let candidates = DB.getUsers().filter(u => u.type === 'candidate');

  if (query && query.trim()) {
    candidates = candidates.filter(c => candidateMatchesQuery(c, query));
  }

  if (filters.skills && filters.skills.length) {
    candidates = candidates.filter(c =>
      filters.skills.some(s =>
        (c.skills || []).some(cs => cs.toLowerCase().includes(s.toLowerCase()))
      )
    );
  }
  if (filters.workMode && filters.workMode.length) {
    candidates = candidates.filter(c => filters.workMode.includes(c.preferredWorkMode));
  }
  if (filters.minExperience && !isNaN(filters.minExperience)) {
    candidates = candidates.filter(c => parseInt(c.yearsOfExperience || 0) >= Number(filters.minExperience));
  }
  if (filters.education) {
    const edu = filters.education.toLowerCase();
    candidates = candidates.filter(c => (c.educationLevel || '').toLowerCase().includes(edu));
  }
  if (filters.location && filters.location.trim()) {
    const loc = filters.location.toLowerCase().trim();
    candidates = candidates.filter(c =>
      (c.location || '').toLowerCase().includes(loc) ||
      (c.preferredLocation || '').toLowerCase().includes(loc)
    );
  }

  return candidates;
}
