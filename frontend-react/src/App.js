import React, { useState } from 'react';
import './App.css';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [allJobs, setAllJobs] = useState([]);
  const [filteredJobs, setFilteredJobs] = useState([]);
  const [jobMatches, setJobMatches] = useState({});
  const [selectedJob, setSelectedJob] = useState(null);
  const [matchData, setMatchData] = useState(null);
  const [roadmap, setRoadmap] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  // Generate a simulated turnover rate based on company name (for demo purposes)
  const generateTurnoverRate = (company) => {
    if (!company) return 12;
    // Simple hash function to generate consistent but varied turnover rates
    let hash = 0;
    for (let i = 0; i < company.length; i++) {
      hash = ((hash << 5) - hash) + company.charCodeAt(i);
      hash = hash & hash;
    }
    // Generate rate between 5% and 25%
    const rate = 5 + (Math.abs(hash) % 21);
    return rate;
  };

  const calculateMatch = (userSkills, jobSkills) => {
    if (!jobSkills || jobSkills.length === 0) return 0;
    if (!userSkills || userSkills.length === 0) return 0;
    
    const userSkillsLower = userSkills.map(s => s.toLowerCase().trim());
    const jobSkillsLower = jobSkills.map(s => s.toLowerCase().trim());
    
    const matchedSkills = jobSkillsLower.filter(skill => 
      userSkillsLower.some(userSkill => 
        userSkill.includes(skill) || skill.includes(userSkill)
      )
    );
    
    return (matchedSkills.length / jobSkillsLower.length) * 100;
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);

    try {
      const allowedTypes = ['application/pdf', 'text/plain'];
      const allowedExtensions = ['.pdf', '.txt'];
      const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      
      if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
        alert('Please upload a .pdf or .txt file');
        setLoading(false);
        return;
      }

      const formData = new FormData();
      formData.append('file', file);

      const uploadRes = await axios.post(`${API_URL}/api/upload-resume`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setCurrentUser(uploadRes.data.user);
      
      const fileType = uploadRes.data.file_type;
      console.log(`Successfully processed ${fileType} file with ${uploadRes.data.extracted_skills.length} skills extracted`);

      const jobsRes = await axios.get(`${API_URL}/api/jobs`);
      const jobs = jobsRes.data;
      
      const matches = {};
      for (const job of jobs) {
        if (job.required_skills && job.required_skills.length > 0) {
          matches[job.id] = calculateMatch(uploadRes.data.user.skills, job.required_skills);
        } else {
          matches[job.id] = 0;
        }
      }
      
      setJobMatches(matches);
      
      const sortedJobs = [...jobs].sort((a, b) => 
        (matches[b.id] || 0) - (matches[a.id] || 0)
      );
      
      setAllJobs(sortedJobs);
      setFilteredJobs(sortedJobs);

    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      alert('Error processing resume: ' + errorMsg);
    }

    setLoading(false);
  };

  const searchJobs = () => {
    const filtered = allJobs.filter(job => {
      const matchesSearch = !searchTerm || 
        job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.location.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesLocation = !locationFilter || job.location.includes(locationFilter);
      const matchesType = !typeFilter || (job.employment_type && job.employment_type.includes(typeFilter));

      return matchesSearch && matchesLocation && matchesType;
    });
    
    const sortedFiltered = [...filtered].sort((a, b) => 
      (jobMatches[b.id] || 0) - (jobMatches[a.id] || 0)
    );

    setFilteredJobs(sortedFiltered);
  };

  const showJobDetail = async (jobId) => {
    setLoading(true);
    setRoadmap(null);

    try {
      const jobRes = await axios.get(`${API_URL}/api/jobs/${jobId}`);
      setSelectedJob(jobRes.data);

      const matchRes = await axios.post(`${API_URL}/api/ai/match-skills`, null, {
        params: { user_id: currentUser.id, job_id: jobId }
      });
      setMatchData(matchRes.data);
      
      if (matchRes.data.match_percentage !== undefined) {
        setJobMatches(prev => ({
          ...prev,
          [jobId]: matchRes.data.match_percentage
        }));
      }

    } catch (error) {
      alert('Error loading job details: ' + error.message);
    }

    setLoading(false);
  };

  const applyToJob = async (jobId) => {
    try {
      await axios.post(`${API_URL}/api/applications`, {
        user_id: currentUser.id,
        job_id: jobId
      });
      alert('Application submitted successfully!');
    } catch (error) {
      alert('Error submitting application: ' + error.message);
    }
  };

  const generateRoadmap = async (jobId) => {
    setLoading(true);

    try {
      const roadmapRes = await axios.post(`${API_URL}/api/ai/generate-roadmap`, null, {
        params: { user_id: currentUser.id, job_id: jobId }
      });
      setRoadmap(roadmapRes.data);
    } catch (error) {
      alert('Error generating roadmap: ' + error.message);
    }

    setLoading(false);
  };

  return (
    <div className="App">
      <header className="header">
        <h1>🎯jobscope.</h1>
        <p><h3>Your AI-powered career kaki</h3></p>
      </header>

      <div className="container">
        {!currentUser && (
          <div className="card">
            <h2>Step 1: Upload Your Resume</h2>
            <div className="upload-area" onClick={() => document.getElementById('resume-file').click()}>
              <input
                type="file"
                id="resume-file"
                accept=".pdf,.txt"
                style={{ display: 'none' }}
                onChange={handleFileUpload}
              />
              <p>📄 Click or drag your resume here</p>
              <p className="small">PDF or TXT format</p>
            </div>
          </div>
        )}

        {currentUser && (
          <div className="card user-info">
            <h3>Your Profile</h3>
            <p><strong>Name:</strong> {currentUser.name}</p>
            <p><strong>Email:</strong> {currentUser.email}</p>
            <p><strong>Skills:</strong> {currentUser.skills.join(', ')}</p>
          </div>
        )}

        {currentUser && !selectedJob && (
          <>
            <div className="card">
              <h2>Step 2: Search Jobs</h2>
              <div className="search-bar">
                <input
                  type="text"
                  placeholder="Search by job title, company, or location..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && searchJobs()}
                />
                <button onClick={searchJobs}>🔍 Search</button>
              </div>
              <div className="filters">
                <select value={locationFilter} onChange={(e) => setLocationFilter(e.target.value)}>
                  <option value="">All Locations</option>
                  <option value="Singapore">Singapore</option>
                </select>
                <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                  <option value="">All Types</option>
                  <option value="Internship">Internship</option>
                  <option value="Full Time">Full Time</option>
                  <option value="Contract">Contract</option>
                </select>
              </div>
            </div>

            <div className="card">
              <h2>Jobs</h2>
              <div className="job-list">
                {filteredJobs.slice(0, 349).map(job => {
                  const matchPercentage = jobMatches[job.id] || 0;
                  const matchClass = matchPercentage >= 70 ? 'high-match' : 
                                    matchPercentage >= 40 ? 'medium-match' : 'low-match';
                  const turnoverRate = generateTurnoverRate(job.company);
                  
                  return (
                    <div key={job.id} className="job-card" onClick={() => showJobDetail(job.id)}>
                      <div className="job-header">
                        <div>
                          <div className="job-title">{job.title}</div>
                          <div className="job-company">{job.company}</div>
                        </div>
                        <div className="badge-container">
                          <div className={`match-badge ${matchClass}`}>
                            {matchPercentage.toFixed(0)}% Match
                          </div>
                          <div className="turnover-badge">
                            {turnoverRate}% Turnover
                          </div>
                        </div>
                      </div>
                      <div className="job-meta">
                        <span className="meta-tag">📍 {job.location}</span>
                        <span className="meta-tag">💼 {job.employment_type || 'N/A'}</span>
                        {job.salary && <span className="meta-tag">💰 {job.salary}</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {selectedJob && !roadmap && (
          <div className="card">
            <button className="back-btn" onClick={() => setSelectedJob(null)}>← Back to Jobs</button>
            <h2>{selectedJob.title}</h2>
            <h3>{selectedJob.company}</h3>
            <div className="company-stats">
              <span className="stat-item">📊 Company Turnover Rate: {generateTurnoverRate(selectedJob.company)}%</span>
            </div>
            
            {matchData && (
              <>
                <div className="match-score">
                  <h3>Match Score: <span>{matchData.match_percentage.toFixed(1)}%</span></h3>
                </div>

                <div className="skills-section">
                  <h4>✅ Your Matching Skills ({matchData.matched_skills.length})</h4>
                  <div className="skill-tags">
                    {matchData.matched_skills.map((skill, i) => (
                      <span key={i} className="skill-tag matched">{skill}</span>
                    ))}
                  </div>
                </div>

                <div className="skills-section">
                  <h4>📚 Skills to Learn ({matchData.missing_skills.length})</h4>
                  <div className="skill-tags">
                    {matchData.missing_skills.map((skill, i) => (
                      <span key={i} className="skill-tag missing">{skill}</span>
                    ))}
                  </div>
                </div>
              </>
            )}

            <div className="job-description">
              <h4>Job Description</h4>
              <p>{selectedJob.job_description || 'No description available'}</p>
            </div>

            <div className="action-buttons">
              <button className="apply-btn" onClick={() => applyToJob(selectedJob.id)}>Apply Now</button>
              <button className="roadmap-btn" onClick={() => generateRoadmap(selectedJob.id)}>📚 Get Learning Roadmap</button>
            </div>
          </div>
        )}

        {roadmap && (
          <div className="card">
            <button className="back-btn" onClick={() => setRoadmap(null)}>← Back to Job</button>
            <h2>📚 Your Personalized Learning Roadmap</h2>

            <div className="roadmap-section">
              <h3>Skills to Learn</h3>
              {roadmap.roadmap.map((item, i) => (
                <div key={i} className="roadmap-item">
                  <h4>{item.skill} - {item.priority} Priority</h4>
                  <p>⏱️ Estimated Time: {item.estimated_time}</p>
                  <p><strong>Resources:</strong></p>
                  <ul>
                    {item.resources.map((r, j) => <li key={j}>{r}</li>)}
                  </ul>
                </div>
              ))}
            </div>

            <div className="roadmap-section">
              <h3>Recommended Projects</h3>
              <ul>
                {roadmap.projects.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            </div>
          </div>
        )}

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Processing...</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
