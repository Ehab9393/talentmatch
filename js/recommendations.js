// TalentMatch — Recommendation Engine
// Scores candidate↔job matches across 5 dimensions.
// NOTE: levenshtein() and fuzzyWordMatch() live in search.js which is always loaded first.

const EDU_ORDER = ['high school', 'diploma', 'associate', "bachelor's", "bachelor", "master's", "master", 'mba', 'phd', 'doctorate'];

function eduIndex(level) {
  const l = (level || '').toLowerCase();
  const idx = EDU_ORDER.findIndex(e => l.includes(e));
  return idx === -1 ? 0 : idx;
}

function skillSimilarity(setA, setB) {
  if (!setA.length || !setB.length) return 0;
  const a = setA.map(s => s.toLowerCase());
  const b = setB.map(s => s.toLowerCase());
  const matched = a.filter(s => b.some(bs => bs.includes(s) || s.includes(bs) || fuzzyWordMatch(s, bs, 0.8)));
  return matched.length / b.length;
}

// ── Candidate → Jobs ──────────────────────────────────────
function scoreJobForCandidate(candidate, job) {
  let score = 0;

  // 1. Skills (40 pts)
  const skillScore = skillSimilarity(candidate.skills || [], job.requiredSkills || []);
  score += skillScore * 40;

  // 2. Experience (20 pts)
  const candExp = parseInt(candidate.yearsOfExperience) || 0;
  const jobExp = parseInt(job.requiredExperience) || 0;
  if (candExp >= jobExp) score += 20;
  else if (candExp >= jobExp - 1) score += 12;
  else if (candExp >= jobExp - 2) score += 6;

  // 3. Work mode preference (20 pts)
  const pm = (candidate.preferredWorkMode || '').toLowerCase();
  const jm = (job.workMode || '').toLowerCase();
  if (!pm || pm === 'no preference') score += 14;
  else if (pm === jm) score += 20;
  else if (jm === 'hybrid') score += 12;

  // 4. Location preference (10 pts) — checks city AND country
  const pl = (candidate.preferredLocation || '').toLowerCase();
  const jc = (job.city || '').toLowerCase();
  const jcountry = (job.country || '').toLowerCase();
  if (pl && (jc.includes(pl) || pl.includes(jc) || jcountry.includes(pl) || pl.includes(jcountry))) score += 10;
  else if (!pl) score += 5;

  // 5. Education (10 pts)
  const candEdu = eduIndex(candidate.educationLevel);
  const jobEdu = eduIndex(job.requiredEducation);
  if (candEdu >= jobEdu) score += 10;
  else if (candEdu >= jobEdu - 1) score += 5;

  return Math.round(Math.min(100, score));
}

// Returns sorted job recommendations for a candidate
function recommendJobsForCandidate(candidate, limit = null, allJobs = null) {
  const jobs = allJobs || DB.getJobs();
  const scored = jobs.map(job => ({
    ...job,
    matchScore: scoreJobForCandidate(candidate, job)
  }));
  scored.sort((a, b) => b.matchScore - a.matchScore);
  return limit ? scored.slice(0, limit) : scored;
}

// ── Job → Candidates ──────────────────────────────────────
function scoreCandidateForJob(candidate, job) {
  let score = 0;

  // 1. Skills (40 pts) — candidate must have job's required skills
  const skillScore = skillSimilarity(candidate.skills || [], job.requiredSkills || []);
  score += skillScore * 40;

  // 2. Experience (20 pts)
  const candExp = parseInt(candidate.yearsOfExperience) || 0;
  const jobExp = parseInt(job.requiredExperience) || 0;
  if (candExp >= jobExp) score += 20;
  else if (candExp >= jobExp - 1) score += 12;
  else if (candExp >= jobExp - 2) score += 6;

  // 3. Work mode (20 pts)
  const pm = (candidate.preferredWorkMode || '').toLowerCase();
  const jm = (job.workMode || '').toLowerCase();
  if (!pm || pm === 'no preference') score += 14;
  else if (pm === jm) score += 20;
  else if (pm === 'hybrid') score += 12;

  // 4. Location (10 pts) — checks city AND country (consistent with scoreJobForCandidate)
  const pl = (candidate.preferredLocation || '').toLowerCase();
  const jc = (job.city || '').toLowerCase();
  const jcountry = (job.country || '').toLowerCase();
  if (pl && (jc.includes(pl) || pl.includes(jc) || jcountry.includes(pl) || pl.includes(jcountry))) score += 10;
  else if (!pl) score += 5;

  // 5. Education (10 pts)
  const candEdu = eduIndex(candidate.educationLevel);
  const jobEdu = eduIndex(job.requiredEducation);
  if (candEdu >= jobEdu) score += 10;
  else if (candEdu >= jobEdu - 1) score += 5;

  return Math.round(Math.min(100, score));
}

// Returns sorted candidate recommendations for a job
function recommendCandidatesForJob(job, limit = null) {
  const candidates = DB.getUsers().filter(u => u.type === 'candidate');
  const scored = candidates.map(c => ({
    ...c,
    matchScore: scoreCandidateForJob(c, job)
  }));
  scored.sort((a, b) => b.matchScore - a.matchScore);
  return limit ? scored.slice(0, limit) : scored;
}

// ── Membership limit helper ────────────────────────────────
function getRecommendationLimit(user) {
  return user?.isMember ? null : 10; // null = unlimited
}
