// TalentMatch — Data Layer (localStorage)
const DB = {
  KEYS: {
    users: 'tm_users',
    jobs: 'tm_jobs',
    applications: 'tm_applications',
    session: 'tm_session',
    saved: 'tm_saved',
    init: 'tm_init'
  },

  init() {
    // Bump version string to force re-seed with new data
    if (localStorage.getItem(this.KEYS.init) !== '4') {
      this._seed();
      localStorage.setItem(this.KEYS.init, '4');
    }
  },

  // ── Users ──────────────────────────────────────────────
  getUsers() { return JSON.parse(localStorage.getItem(this.KEYS.users) || '[]'); },
  saveUsers(u) { localStorage.setItem(this.KEYS.users, JSON.stringify(u)); },
  getUserById(id) { return this.getUsers().find(u => u.id === id) || null; },
  getUserByEmail(email) { return this.getUsers().find(u => u.email.toLowerCase() === email.toLowerCase()) || null; },
  updateUser(updated) {
    const users = this.getUsers().map(u => u.id === updated.id ? { ...u, ...updated } : u);
    this.saveUsers(users);
  },
  addUser(user) {
    const users = this.getUsers();
    users.push(user);
    this.saveUsers(users);
  },

  // ── Jobs ──────────────────────────────────────────────
  getJobs() { return JSON.parse(localStorage.getItem(this.KEYS.jobs) || '[]'); },
  saveJobs(j) { localStorage.setItem(this.KEYS.jobs, JSON.stringify(j)); },
  getJobById(id) { return this.getJobs().find(j => j.id === id) || null; },
  addJob(job) {
    const jobs = this.getJobs();
    jobs.unshift(job);
    this.saveJobs(jobs);
  },
  deleteJob(id) {
    this.saveJobs(this.getJobs().filter(j => j.id !== id));
  },

  // ── Applications ──────────────────────────────────────
  getApplications() { return JSON.parse(localStorage.getItem(this.KEYS.applications) || '[]'); },
  saveApplications(a) { localStorage.setItem(this.KEYS.applications, JSON.stringify(a)); },
  applyToJob(jobId, candidateId) {
    const apps = this.getApplications();
    const exists = apps.find(a => a.jobId === jobId && a.candidateId === candidateId);
    if (exists) return false;
    apps.push({ id: 'app' + Date.now(), jobId, candidateId, status: 'applied', appliedAt: new Date().toISOString() });
    this.saveApplications(apps);
    // increment applicants count
    const jobs = this.getJobs().map(j => j.id === jobId ? { ...j, applicants: (j.applicants || 0) + 1 } : j);
    this.saveJobs(jobs);
    return true;
  },
  hasApplied(jobId, candidateId) {
    return this.getApplications().some(a => a.jobId === jobId && a.candidateId === candidateId);
  },
  getCandidateApplications(candidateId) {
    const apps = this.getApplications().filter(a => a.candidateId === candidateId);
    return apps.map(a => ({ ...a, job: this.getJobById(a.jobId) })).filter(a => a.job);
  },
  getJobApplications(jobId) {
    const apps = this.getApplications().filter(a => a.jobId === jobId);
    return apps.map(a => ({ ...a, candidate: this.getUserById(a.candidateId) })).filter(a => a.candidate);
  },

  // ── Session ──────────────────────────────────────────
  getSession() { return JSON.parse(localStorage.getItem(this.KEYS.session) || 'null'); },
  setSession(user) { localStorage.setItem(this.KEYS.session, JSON.stringify(user)); },
  clearSession() { localStorage.removeItem(this.KEYS.session); },
  getCurrentUser() {
    const s = this.getSession();
    if (!s) return null;
    return this.getUserById(s.id) || null;
  },

  // ── Saved Jobs ────────────────────────────────────────
  getSaved(userId) {
    const all = JSON.parse(localStorage.getItem(this.KEYS.saved) || '{}');
    return all[userId] || [];
  },
  toggleSaved(userId, jobId) {
    const all = JSON.parse(localStorage.getItem(this.KEYS.saved) || '{}');
    if (!all[userId]) all[userId] = [];
    const idx = all[userId].indexOf(jobId);
    if (idx >= 0) all[userId].splice(idx, 1);
    else all[userId].push(jobId);
    localStorage.setItem(this.KEYS.saved, JSON.stringify(all));
    return idx < 0; // true = now saved
  },

  // ── Seed Data ─────────────────────────────────────────
  _seed() {
    const users = [
      {
        id: 'u1', type: 'candidate', isMember: false,
        name: 'Alice Chen', email: 'alice@example.com', password: 'password123',
        mobile: '+61 412 345 678',
        location: 'Sydney, Australia', educationLevel: "Bachelor's",
        fieldOfStudy: 'Computer Science', yearsOfExperience: '3',
        skills: ['React', 'JavaScript', 'Node.js', 'Python', 'CSS'],
        preferredWorkMode: 'remote', preferredLocation: 'Sydney',
        bio: 'Full-stack developer with 3 years of experience building scalable web applications.',
        workExperience: [
          { title: 'Frontend Developer', company: 'TechCorp', from: '2022-01', to: '2024-06', current: false, description: 'Built React dashboards and REST APIs.' }
        ]
      },
      {
        id: 'u2', type: 'candidate', isMember: true,
        name: 'Bob Kumar', email: 'bob@example.com', password: 'password123',
        mobile: '+61 498 765 432',
        location: 'Melbourne, Australia', educationLevel: "Master's",
        fieldOfStudy: 'Data Science', yearsOfExperience: '5',
        skills: ['Python', 'Machine Learning', 'TensorFlow', 'SQL', 'Data Analysis'],
        preferredWorkMode: 'hybrid', preferredLocation: 'Melbourne',
        bio: 'Data scientist with expertise in ML and deep learning.',
        workExperience: [
          { title: 'Data Analyst', company: 'Analytics Co', from: '2020-03', to: '2023-12', current: false, description: 'Developed predictive models for retail clients.' }
        ]
      },
      {
        id: 'u3', type: 'candidate', isMember: false,
        name: 'Sara Lee', email: 'sara@example.com', password: 'password123',
        mobile: '+1 555 123 4567',
        location: 'New York, USA', educationLevel: "Bachelor's",
        fieldOfStudy: 'Design', yearsOfExperience: '4',
        skills: ['Figma', 'UI Design', 'UX Research', 'Adobe XD', 'Prototyping'],
        preferredWorkMode: 'hybrid', preferredLocation: 'New York',
        bio: 'UI/UX designer passionate about creating intuitive user experiences.',
        workExperience: [
          { title: 'UI Designer', company: 'DesignStudio', from: '2021-06', to: '', current: true, description: 'Leading product design for B2B SaaS products.' }
        ]
      },
      {
        id: 'u4', type: 'candidate', isMember: false,
        name: 'James Nguyen', email: 'james@example.com', password: 'password123',
        mobile: '+61 411 222 333',
        location: 'Brisbane, Australia', educationLevel: "Bachelor's",
        fieldOfStudy: 'Cybersecurity', yearsOfExperience: '2',
        skills: ['Penetration Testing', 'SIEM', 'Network Security', 'Python', 'Linux'],
        preferredWorkMode: 'on-site', preferredLocation: 'Brisbane',
        bio: 'Cybersecurity graduate eager to protect systems and networks.',
        workExperience: [
          { title: 'Security Intern', company: 'SecureTech', from: '2023-01', to: '2023-12', current: false, description: 'Assisted with vulnerability assessments and security audits.' }
        ]
      },
      {
        id: 'u5', type: 'candidate', isMember: false,
        name: 'Maria Santos', email: 'maria@example.com', password: 'password123',
        mobile: '+61 422 333 444',
        location: 'Sydney, Australia', educationLevel: "Bachelor's",
        fieldOfStudy: 'Business', yearsOfExperience: '3',
        skills: ['Sales', 'CRM', 'Communication', 'Negotiation', 'Customer Service'],
        preferredWorkMode: 'hybrid', preferredLocation: 'Sydney',
        bio: 'Sales professional with a track record of exceeding targets.',
        workExperience: [
          { title: 'Sales Executive', company: 'RetailPlus', from: '2021-03', to: '', current: true, description: 'Managed key accounts and grew revenue by 35%.' }
        ]
      },
      {
        id: 'e1', type: 'employer', isMember: true,
        name: 'Google HR', email: 'hr@google.example.com', password: 'password123',
        mobile: '+1 650 000 0000',
        company: 'Google', companyLogo: 'google',
        companyDescription: 'Organising the world\'s information and making it universally accessible.',
        location: 'Sydney, Australia'
      },
      {
        id: 'e2', type: 'employer', isMember: true,
        name: 'Microsoft Recruiting', email: 'recruit@microsoft.example.com', password: 'password123',
        mobile: '+1 425 000 0000',
        company: 'Microsoft', companyLogo: 'microsoft',
        companyDescription: 'Empower every person and organisation on the planet to achieve more.',
        location: 'Melbourne, Australia'
      },
      {
        id: 'e3', type: 'employer', isMember: false,
        name: 'Amazon Talent', email: 'talent@amazon.example.com', password: 'password123',
        mobile: '+1 206 000 0000',
        company: 'Amazon', companyLogo: 'amazon',
        companyDescription: 'Work hard. Have fun. Make history.',
        location: 'Sydney, Australia'
      }
    ];

    const jobs = [
      // ── Engineering ──────────────────────────────────────────────
      {
        id: 'j1', employerId: 'e1',
        title: 'Software Engineer (Frontend)', company: 'Google', companyLogo: 'google',
        jobType: 'full-time', minSalary: 120000, maxSalary: 160000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['React', 'JavaScript', 'TypeScript', 'CSS', 'REST APIs'],
        requiredExperience: '3', requiredEducation: "Bachelor's",
        workMode: 'hybrid', jobRole: 'Software Engineer', jobFunction: 'Engineering',
        jobLevel: 'Mid-level', tags: ['frontend', 'react', 'javascript', 'typescript'],
        description: '<p>Join Google\'s Sydney team as a <strong>Frontend Software Engineer</strong> building next-generation web products.</p><ul><li>Build high-performance React applications</li><li>Collaborate with cross-functional teams</li><li>Mentor junior engineers</li></ul>',
        applicants: 45, rating: 4.9, postedAt: '2025-05-12'
      },
      {
        id: 'j2', employerId: 'e2',
        title: 'Full Stack Developer', company: 'Microsoft', companyLogo: 'microsoft',
        jobType: 'full-time', minSalary: 100000, maxSalary: 135000, currency: 'AUD',
        location: 'Melbourne, Australia', country: 'Australia', city: 'Melbourne',
        requiredSkills: ['Node.js', 'React', 'Python', 'PostgreSQL', 'Docker'],
        requiredExperience: '4', requiredEducation: "Bachelor's",
        workMode: 'hybrid', jobRole: 'Software Engineer', jobFunction: 'Engineering',
        jobLevel: 'Senior', tags: ['fullstack', 'nodejs', 'react', 'python', 'backend'],
        description: '<p>Microsoft seeks a <strong>Full Stack Developer</strong> to build scalable enterprise tools.</p><ul><li>Develop REST APIs and microservices</li><li>Build React frontends</li><li>Manage PostgreSQL databases</li></ul>',
        applicants: 38, rating: 4.7, postedAt: '2025-05-10'
      },
      {
        id: 'j3', employerId: 'e3',
        title: 'Backend Developer (Python)', company: 'Amazon', companyLogo: 'amazon',
        jobType: 'full-time', minSalary: 110000, maxSalary: 145000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Python', 'Django', 'AWS', 'PostgreSQL', 'Docker', 'REST APIs'],
        requiredExperience: '3', requiredEducation: "Bachelor's",
        workMode: 'remote', jobRole: 'Backend Developer', jobFunction: 'Engineering',
        jobLevel: 'Mid-level', tags: ['backend', 'python', 'django', 'aws'],
        description: '<p>Build and scale Amazon\'s backend services using Python and AWS.</p><ul><li>Design and implement REST APIs</li><li>Optimise database queries and performance</li><li>Deploy services to AWS infrastructure</li></ul>',
        applicants: 52, rating: 4.8, postedAt: '2025-05-11'
      },
      {
        id: 'j4', employerId: 'e1',
        title: 'Cloud Infrastructure Engineer', company: 'Google', companyLogo: 'google',
        jobType: 'full-time', minSalary: 135000, maxSalary: 175000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Kubernetes', 'Docker', 'GCP', 'Terraform', 'Python'],
        requiredExperience: '5', requiredEducation: "Bachelor's",
        workMode: 'remote', jobRole: 'Cloud Engineer', jobFunction: 'Engineering',
        jobLevel: 'Senior', tags: ['cloud', 'kubernetes', 'docker', 'gcp', 'devops'],
        description: '<p>Join the Google Cloud team to build reliable, scalable infrastructure.</p><ul><li>Manage Kubernetes clusters and GCP services</li><li>Automate infrastructure with Terraform</li><li>Ensure 99.9% uptime SLAs</li></ul>',
        applicants: 29, rating: 4.9, postedAt: '2025-05-13'
      },
      {
        id: 'j5', employerId: 'e2',
        title: 'iOS / Mobile Developer', company: 'Microsoft', companyLogo: 'microsoft',
        jobType: 'full-time', minSalary: 115000, maxSalary: 150000, currency: 'AUD',
        location: 'Melbourne, Australia', country: 'Australia', city: 'Melbourne',
        requiredSkills: ['Swift', 'iOS', 'React Native', 'Xcode', 'REST APIs'],
        requiredExperience: '3', requiredEducation: "Bachelor's",
        workMode: 'hybrid', jobRole: 'Mobile Developer', jobFunction: 'Engineering',
        jobLevel: 'Mid-level', tags: ['ios', 'swift', 'mobile', 'react native'],
        description: '<p>Build cutting-edge mobile experiences for Microsoft\'s growing app portfolio.</p><ul><li>Develop iOS apps with Swift and SwiftUI</li><li>Integrate REST APIs and push notifications</li><li>Write unit and UI tests</li></ul>',
        applicants: 21, rating: 4.6, postedAt: '2025-05-08'
      },
      {
        id: 'j6', employerId: 'e3',
        title: 'Software Engineering Intern', company: 'Amazon', companyLogo: 'amazon',
        jobType: 'internship', minSalary: 40000, maxSalary: 55000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Python', 'Java', 'Git', 'Data Structures', 'Algorithms'],
        requiredExperience: '0', requiredEducation: "Bachelor's",
        workMode: 'on-site', jobRole: 'Software Engineer', jobFunction: 'Engineering',
        jobLevel: 'Fresher', tags: ['internship', 'graduate', 'python', 'java'],
        description: '<p>12-week paid internship on Amazon\'s engineering teams in Sydney.</p><ul><li>Work on real production features</li><li>Mentorship from senior engineers</li><li>Possibility of full-time offer</li></ul>',
        applicants: 134, rating: 4.8, postedAt: '2025-05-14'
      },
      // ── Cybersecurity / IT ────────────────────────────────────────
      {
        id: 'j7', employerId: 'e1',
        title: 'Cybersecurity Analyst', company: 'Google', companyLogo: 'google',
        jobType: 'full-time', minSalary: 110000, maxSalary: 145000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Cybersecurity', 'SIEM', 'Penetration Testing', 'Network Security', 'Python'],
        requiredExperience: '3', requiredEducation: "Bachelor's",
        workMode: 'hybrid', jobRole: 'Cybersecurity Analyst', jobFunction: 'Cybersecurity',
        jobLevel: 'Mid-level', tags: ['cybersecurity', 'security', 'infosec', 'network security', 'it'],
        description: '<p>Google is hiring a <strong>Cybersecurity Analyst</strong> to protect our infrastructure from threats.</p><ul><li>Monitor security incidents using SIEM tools</li><li>Conduct vulnerability assessments and penetration tests</li><li>Develop and enforce security policies</li></ul>',
        applicants: 28, rating: 4.7, postedAt: '2025-05-13'
      },
      {
        id: 'j8', employerId: 'e2',
        title: 'IT Support Engineer', company: 'Microsoft', companyLogo: 'microsoft',
        jobType: 'full-time', minSalary: 70000, maxSalary: 90000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['IT Support', 'Networking', 'Windows', 'Linux', 'Active Directory'],
        requiredExperience: '2', requiredEducation: "Bachelor's",
        workMode: 'on-site', jobRole: 'IT Support', jobFunction: 'Cybersecurity',
        jobLevel: 'Mid-level', tags: ['it', 'support', 'networking', 'information technology', 'helpdesk'],
        description: '<p>Keep Microsoft\'s Sydney office running with hands-on IT support.</p><ul><li>Troubleshoot hardware and software issues</li><li>Manage Active Directory and network infrastructure</li><li>Deploy and maintain IT systems</li></ul>',
        applicants: 19, rating: 4.5, postedAt: '2025-05-11'
      },
      {
        id: 'j9', employerId: 'e3',
        title: 'Network Security Engineer', company: 'Amazon', companyLogo: 'amazon',
        jobType: 'full-time', minSalary: 115000, maxSalary: 150000, currency: 'AUD',
        location: 'Melbourne, Australia', country: 'Australia', city: 'Melbourne',
        requiredSkills: ['Network Security', 'Firewall', 'VPN', 'Cybersecurity', 'Cisco', 'Python'],
        requiredExperience: '4', requiredEducation: "Bachelor's",
        workMode: 'hybrid', jobRole: 'Network Security Engineer', jobFunction: 'Cybersecurity',
        jobLevel: 'Senior', tags: ['cybersecurity', 'network', 'security', 'infosec', 'it', 'firewall'],
        description: '<p>Design and protect Amazon\'s network infrastructure.</p><ul><li>Configure and manage firewalls, VPNs, and IDS/IPS</li><li>Perform network security audits</li><li>Respond to security incidents and breaches</li></ul>',
        applicants: 14, rating: 4.6, postedAt: '2025-05-10'
      },
      {
        id: 'j10', employerId: 'e1',
        title: 'Information Security Manager', company: 'Google', companyLogo: 'google',
        jobType: 'full-time', minSalary: 155000, maxSalary: 195000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Information Security', 'Risk Management', 'CISSP', 'ISO 27001', 'Leadership'],
        requiredExperience: '7', requiredEducation: "Master's",
        workMode: 'hybrid', jobRole: 'Security Manager', jobFunction: 'Cybersecurity',
        jobLevel: 'Lead', tags: ['cybersecurity', 'infosec', 'security', 'it', 'management', 'cissp'],
        description: '<p>Lead Google\'s information security program in APAC.</p><ul><li>Oversee the organisation\'s cybersecurity strategy</li><li>Manage a team of security analysts</li><li>Ensure compliance with ISO 27001 and SOC 2</li></ul>',
        applicants: 8, rating: 4.9, postedAt: '2025-05-09'
      },
      // ── Data & Analytics ──────────────────────────────────────────
      {
        id: 'j11', employerId: 'e2',
        title: 'Data Analyst', company: 'Microsoft', companyLogo: 'microsoft',
        jobType: 'full-time', minSalary: 85000, maxSalary: 110000, currency: 'AUD',
        location: 'Melbourne, Australia', country: 'Australia', city: 'Melbourne',
        requiredSkills: ['Python', 'SQL', 'Tableau', 'Excel', 'Statistics'],
        requiredExperience: '2', requiredEducation: "Bachelor's",
        workMode: 'hybrid', jobRole: 'Data Analyst', jobFunction: 'Data & Analytics',
        jobLevel: 'Mid-level', tags: ['data', 'analytics', 'python', 'sql', 'tableau'],
        description: '<p>Turn data into decisions at Microsoft\'s Melbourne analytics hub.</p><ul><li>Analyse large datasets using Python and SQL</li><li>Build dashboards and reports in Tableau</li><li>Present findings to stakeholders</li></ul>',
        applicants: 47, rating: 4.7, postedAt: '2025-05-12'
      },
      {
        id: 'j12', employerId: 'e3',
        title: 'Machine Learning Engineer', company: 'Amazon', companyLogo: 'amazon',
        jobType: 'full-time', minSalary: 130000, maxSalary: 170000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Python', 'Machine Learning', 'TensorFlow', 'PyTorch', 'AWS SageMaker'],
        requiredExperience: '4', requiredEducation: "Master's",
        workMode: 'remote', jobRole: 'ML Engineer', jobFunction: 'Data & Analytics',
        jobLevel: 'Senior', tags: ['machine learning', 'ai', 'python', 'tensorflow', 'data science'],
        description: '<p>Build and deploy ML models that power Amazon\'s recommendation engine.</p><ul><li>Train and evaluate deep learning models</li><li>Deploy models to production with AWS SageMaker</li><li>Monitor model performance and drift</li></ul>',
        applicants: 31, rating: 4.8, postedAt: '2025-05-07'
      },
      {
        id: 'j13', employerId: 'e1',
        title: 'Business Intelligence Developer', company: 'Google', companyLogo: 'google',
        jobType: 'full-time', minSalary: 95000, maxSalary: 125000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Power BI', 'SQL', 'Python', 'Data Warehousing', 'ETL'],
        requiredExperience: '3', requiredEducation: "Bachelor's",
        workMode: 'hybrid', jobRole: 'BI Developer', jobFunction: 'Data & Analytics',
        jobLevel: 'Mid-level', tags: ['bi', 'power bi', 'sql', 'data', 'analytics'],
        description: '<p>Transform raw data into compelling business insights at Google.</p><ul><li>Design and build Power BI dashboards</li><li>Develop ETL pipelines</li><li>Collaborate with business stakeholders</li></ul>',
        applicants: 23, rating: 4.6, postedAt: '2025-05-06'
      },
      // ── Design ────────────────────────────────────────────────────
      {
        id: 'j14', employerId: 'e2',
        title: 'Senior UI/UX Designer', company: 'Microsoft', companyLogo: 'microsoft',
        jobType: 'full-time', minSalary: 100000, maxSalary: 135000, currency: 'AUD',
        location: 'Melbourne, Australia', country: 'Australia', city: 'Melbourne',
        requiredSkills: ['Figma', 'UI Design', 'UX Research', 'Prototyping', 'Adobe XD'],
        requiredExperience: '5', requiredEducation: "Bachelor's",
        workMode: 'hybrid', jobRole: 'UI/UX Designer', jobFunction: 'Design',
        jobLevel: 'Senior', tags: ['design', 'ui', 'ux', 'figma', 'product design'],
        description: '<p>Craft exceptional user experiences for Microsoft\'s flagship products.</p><ul><li>Lead design sprints and user research sessions</li><li>Create wireframes, prototypes, and final designs in Figma</li><li>Collaborate closely with engineers and PMs</li></ul>',
        applicants: 34, rating: 4.8, postedAt: '2025-05-09'
      },
      {
        id: 'j15', employerId: 'e3',
        title: 'Graphic Designer', company: 'Amazon', companyLogo: 'amazon',
        jobType: 'full-time', minSalary: 70000, maxSalary: 90000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Adobe Illustrator', 'Photoshop', 'Branding', 'Typography', 'InDesign'],
        requiredExperience: '2', requiredEducation: "Bachelor's",
        workMode: 'on-site', jobRole: 'Graphic Designer', jobFunction: 'Design',
        jobLevel: 'Mid-level', tags: ['design', 'graphic design', 'branding', 'adobe'],
        description: '<p>Create visual assets for Amazon\'s marketing and brand campaigns.</p><ul><li>Design marketing materials, banners, and social content</li><li>Maintain brand consistency across all platforms</li><li>Work with the marketing team on campaigns</li></ul>',
        applicants: 41, rating: 4.4, postedAt: '2025-05-08'
      },
      {
        id: 'j16', employerId: 'e1',
        title: 'Product Designer (UX)', company: 'Google', companyLogo: 'google',
        jobType: 'full-time', minSalary: 115000, maxSalary: 150000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Figma', 'User Research', 'Interaction Design', 'Design Systems', 'Prototyping'],
        requiredExperience: '4', requiredEducation: "Bachelor's",
        workMode: 'remote', jobRole: 'Product Designer', jobFunction: 'Design',
        jobLevel: 'Senior', tags: ['ux', 'product design', 'figma', 'design systems'],
        description: '<p>Define the future of Google products through world-class UX design.</p><ul><li>Own end-to-end product design from research to launch</li><li>Build and maintain design system components</li><li>Conduct usability testing</li></ul>',
        applicants: 57, rating: 4.9, postedAt: '2025-05-14'
      },
      // ── Marketing ─────────────────────────────────────────────────
      {
        id: 'j17', employerId: 'e2',
        title: 'Digital Marketing Manager', company: 'Microsoft', companyLogo: 'microsoft',
        jobType: 'full-time', minSalary: 95000, maxSalary: 125000, currency: 'AUD',
        location: 'Melbourne, Australia', country: 'Australia', city: 'Melbourne',
        requiredSkills: ['Digital Marketing', 'Google Ads', 'SEO', 'Analytics', 'Content Strategy'],
        requiredExperience: '4', requiredEducation: "Bachelor's",
        workMode: 'hybrid', jobRole: 'Marketing Manager', jobFunction: 'Marketing',
        jobLevel: 'Senior', tags: ['marketing', 'digital marketing', 'seo', 'ads', 'growth'],
        description: '<p>Drive Microsoft\'s digital marketing strategy across APAC.</p><ul><li>Plan and execute paid and organic campaigns</li><li>Manage Google Ads and social media budgets</li><li>Track KPIs and optimise conversion funnels</li></ul>',
        applicants: 26, rating: 4.6, postedAt: '2025-05-10'
      },
      {
        id: 'j18', employerId: 'e3',
        title: 'SEO Specialist', company: 'Amazon', companyLogo: 'amazon',
        jobType: 'full-time', minSalary: 75000, maxSalary: 95000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['SEO', 'Google Analytics', 'Content Marketing', 'Keyword Research', 'HTML'],
        requiredExperience: '2', requiredEducation: "Bachelor's",
        workMode: 'remote', jobRole: 'SEO Specialist', jobFunction: 'Marketing',
        jobLevel: 'Mid-level', tags: ['seo', 'marketing', 'content', 'google analytics'],
        description: '<p>Own Amazon\'s organic search performance across Australia.</p><ul><li>Conduct keyword research and on-page optimisation</li><li>Build backlink strategies</li><li>Report on rankings and traffic trends</li></ul>',
        applicants: 33, rating: 4.5, postedAt: '2025-05-11'
      },
      {
        id: 'j19', employerId: 'e1',
        title: 'Content Marketing Coordinator', company: 'Google', companyLogo: 'google',
        jobType: 'part-time', minSalary: 55000, maxSalary: 70000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Content Writing', 'Social Media', 'Copywriting', 'Marketing', 'WordPress'],
        requiredExperience: '1', requiredEducation: "Bachelor's",
        workMode: 'remote', jobRole: 'Content Coordinator', jobFunction: 'Marketing',
        jobLevel: 'Fresher', tags: ['marketing', 'content', 'social media', 'writing'],
        description: '<p>Create engaging content that tells Google\'s story to Australia.</p><ul><li>Write blog posts, social media content, and email campaigns</li><li>Collaborate with designers on visual content</li><li>Track content performance and engagement</li></ul>',
        applicants: 61, rating: 4.3, postedAt: '2025-05-12'
      },
      // ── Sales ─────────────────────────────────────────────────────
      {
        id: 'j20', employerId: 'e2',
        title: 'Sales Account Executive', company: 'Microsoft', companyLogo: 'microsoft',
        jobType: 'full-time', minSalary: 90000, maxSalary: 130000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Sales', 'B2B Sales', 'CRM', 'Negotiation', 'Salesforce'],
        requiredExperience: '3', requiredEducation: "Bachelor's",
        workMode: 'hybrid', jobRole: 'Account Executive', jobFunction: 'Sales',
        jobLevel: 'Mid-level', tags: ['sales', 'b2b', 'crm', 'account management'],
        description: '<p>Drive revenue growth by winning and expanding enterprise accounts.</p><ul><li>Manage a portfolio of mid-market and enterprise clients</li><li>Run product demos and negotiate contracts</li><li>Achieve and exceed quarterly sales targets</li></ul>',
        applicants: 44, rating: 4.6, postedAt: '2025-05-09'
      },
      {
        id: 'j21', employerId: 'e3',
        title: 'Business Development Representative', company: 'Amazon', companyLogo: 'amazon',
        jobType: 'full-time', minSalary: 65000, maxSalary: 85000, currency: 'AUD',
        location: 'Melbourne, Australia', country: 'Australia', city: 'Melbourne',
        requiredSkills: ['Sales', 'Lead Generation', 'Cold Calling', 'CRM', 'Communication'],
        requiredExperience: '1', requiredEducation: "Bachelor's",
        workMode: 'on-site', jobRole: 'BDR', jobFunction: 'Sales',
        jobLevel: 'Fresher', tags: ['sales', 'bdr', 'lead generation', 'entry level'],
        description: '<p>Kick-start your sales career at Amazon and build a pipeline of new business.</p><ul><li>Prospect and qualify new leads via email and phone</li><li>Set up discovery calls for Account Executives</li><li>Manage leads in Salesforce CRM</li></ul>',
        applicants: 78, rating: 4.4, postedAt: '2025-05-08'
      },
      {
        id: 'j22', employerId: 'e1',
        title: 'Enterprise Sales Manager', company: 'Google', companyLogo: 'google',
        jobType: 'full-time', minSalary: 140000, maxSalary: 190000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Enterprise Sales', 'Strategic Selling', 'Leadership', 'Google Cloud', 'Negotiation'],
        requiredExperience: '7', requiredEducation: "Bachelor's",
        workMode: 'hybrid', jobRole: 'Sales Manager', jobFunction: 'Sales',
        jobLevel: 'Lead', tags: ['sales', 'enterprise', 'google cloud', 'leadership'],
        description: '<p>Lead Google Cloud sales across Australia\'s top 200 enterprises.</p><ul><li>Build and execute territory sales plans</li><li>Coach and manage a team of Account Executives</li><li>Engage C-level stakeholders</li></ul>',
        applicants: 12, rating: 4.8, postedAt: '2025-05-07'
      },
      // ── Customer Service ──────────────────────────────────────────
      {
        id: 'j23', employerId: 'e3',
        title: 'Customer Success Manager', company: 'Amazon', companyLogo: 'amazon',
        jobType: 'full-time', minSalary: 80000, maxSalary: 105000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Customer Service', 'Account Management', 'CRM', 'Communication', 'Problem Solving'],
        requiredExperience: '3', requiredEducation: "Bachelor's",
        workMode: 'hybrid', jobRole: 'Customer Success Manager', jobFunction: 'Customer Service',
        jobLevel: 'Mid-level', tags: ['customer service', 'customer success', 'account management', 'crm'],
        description: '<p>Ensure Amazon\'s enterprise customers achieve their goals on our platform.</p><ul><li>Onboard and support key accounts post-sale</li><li>Drive adoption, renewal, and upsell</li><li>Build long-term customer relationships</li></ul>',
        applicants: 36, rating: 4.5, postedAt: '2025-05-11'
      },
      {
        id: 'j24', employerId: 'e2',
        title: 'Customer Support Specialist', company: 'Microsoft', companyLogo: 'microsoft',
        jobType: 'full-time', minSalary: 60000, maxSalary: 78000, currency: 'AUD',
        location: 'Melbourne, Australia', country: 'Australia', city: 'Melbourne',
        requiredSkills: ['Customer Service', 'Technical Support', 'Communication', 'Microsoft 365', 'Patience'],
        requiredExperience: '1', requiredEducation: "Bachelor's",
        workMode: 'on-site', jobRole: 'Support Specialist', jobFunction: 'Customer Service',
        jobLevel: 'Fresher', tags: ['customer service', 'support', 'helpdesk', 'microsoft 365'],
        description: '<p>Be the first point of contact for Microsoft\'s customers across Australia.</p><ul><li>Resolve customer queries via phone, email, and chat</li><li>Troubleshoot Microsoft 365 and Azure issues</li><li>Escalate complex issues to technical teams</li></ul>',
        applicants: 53, rating: 4.3, postedAt: '2025-05-10'
      },
      {
        id: 'j25', employerId: 'e1',
        title: 'Head of Customer Experience', company: 'Google', companyLogo: 'google',
        jobType: 'full-time', minSalary: 145000, maxSalary: 185000, currency: 'AUD',
        location: 'Sydney, Australia', country: 'Australia', city: 'Sydney',
        requiredSkills: ['Customer Experience', 'Leadership', 'NPS', 'Operations', 'CRM', 'Strategy'],
        requiredExperience: '8', requiredEducation: "Master's",
        workMode: 'hybrid', jobRole: 'CX Head', jobFunction: 'Customer Service',
        jobLevel: 'Lead', tags: ['customer service', 'leadership', 'cx', 'strategy'],
        description: '<p>Define and lead the customer experience strategy for Google APAC.</p><ul><li>Build and scale a world-class CX team</li><li>Drive NPS and CSAT improvements</li><li>Partner with product teams to remove customer pain points</li></ul>',
        applicants: 9, rating: 4.9, postedAt: '2025-05-06'
      }
    ];

    this.saveUsers(users);
    this.saveJobs(jobs);
    this.saveApplications([]);
  }
};
