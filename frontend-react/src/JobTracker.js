import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './JobTracker.css';

const API_URL = 'http://localhost:8000';

function JobTracker({ currentUser }) {
  const [trackedJobs, setTrackedJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingJob, setEditingJob] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    company: '',
    position: '',
    status: 'Applied',
    dateApplied: new Date().toISOString().split('T')[0],
    notes: ''
  });

  useEffect(() => {
    if (currentUser) {
      loadTrackedJobs();
    }
  }, [currentUser]);

  const loadTrackedJobs = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/job-tracker/${currentUser.id}`);
      setTrackedJobs(response.data);
    } catch (error) {
      console.error('Error loading tracked jobs:', error);
    }
    setLoading(false);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!currentUser) {
      alert('Please upload your resume on the Home page first to create a user profile.');
      return;
    }
    
    setLoading(true);
    try {
      if (editingJob) {
        // Update existing job
        await axios.put(`${API_URL}/api/job-tracker/${editingJob.id}`, {
          ...formData,
          userId: currentUser.id
        });
        alert('Job updated successfully!');
      } else {
        // Create new job
        await axios.post(`${API_URL}/api/job-tracker`, {
          ...formData,
          userId: currentUser.id
        });
        alert('Job added successfully!');
      }
      
      // Reset form and reload
      setFormData({
        company: '',
        position: '',
        status: 'Applied',
        dateApplied: new Date().toISOString().split('T')[0],
        notes: ''
      });
      setEditingJob(null);
      setShowAddForm(false);
      await loadTrackedJobs();
    } catch (error) {
      alert('Error saving job: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const handleEdit = (job) => {
    setEditingJob(job);
    setFormData({
      company: job.company,
      position: job.position,
      status: job.status,
      dateApplied: job.dateApplied,
      notes: job.notes || ''
    });
    setShowAddForm(true);
  };

  const handleDelete = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this job?')) return;
    
    setLoading(true);
    try {
      await axios.delete(`${API_URL}/api/job-tracker/${jobId}`);
      alert('Job deleted successfully!');
      await loadTrackedJobs();
    } catch (error) {
      alert('Error deleting job: ' + error.message);
    }
    setLoading(false);
  };

  const handleExportCSV = () => {
    if (trackedJobs.length === 0) {
      alert('No jobs to export');
      return;
    }

    const headers = ['Company', 'Position', 'Status', 'Date Applied', 'Notes'];
    const rows = trackedJobs.map(job => [
      job.company,
      job.position,
      job.status,
      job.dateApplied,
      job.notes || ''
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `job-tracker-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const getStatusColor = (status) => {
    const colors = {
      'Applied': '#3498db',
      'Interview Scheduled': '#f39c12',
      'Interview Completed': '#9b59b6',
      'Offer Received': '#2ecc71',
      'Rejected': '#e74c3c',
      'Withdrawn': '#95a5a6'
    };
    return colors[status] || '#7f8c8d';
  };

  const statusOptions = [
    'Applied',
    'Interview Scheduled',
    'Interview Completed',
    'Offer Received',
    'Rejected',
    'Withdrawn'
  ];

  return (
    <div className="job-tracker-container">
      <div className="tracker-header">
        <h1>📊 Job Application Tracker</h1>
        <p>Keep track of all your job applications in one place</p>
      </div>

      {!currentUser && (
        <div className="card">
          <p>Please upload your resume first to use the Job Tracker.</p>
        </div>
      )}

      {currentUser && (
        <>
          <div className="tracker-actions">
            <button 
              className="btn-primary" 
              onClick={() => {
                setShowAddForm(true);
                setEditingJob(null);
                setFormData({
                  company: '',
                  position: '',
                  status: 'Applied',
                  dateApplied: new Date().toISOString().split('T')[0],
                  notes: ''
                });
              }}
            >
              ➕ Add New Application
            </button>
            <button 
              className="btn-secondary" 
              onClick={handleExportCSV}
              disabled={trackedJobs.length === 0}
            >
              📥 Export to CSV
            </button>
          </div>

          {showAddForm && (
            <div className="card form-card">
              <h2>{editingJob ? 'Edit Application' : 'Add New Application'}</h2>
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label>Company Name *</label>
                  <input
                    type="text"
                    name="company"
                    value={formData.company}
                    onChange={handleInputChange}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Position *</label>
                  <input
                    type="text"
                    name="position"
                    value={formData.position}
                    onChange={handleInputChange}
                    required
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Status *</label>
                    <select
                      name="status"
                      value={formData.status}
                      onChange={handleInputChange}
                      required
                    >
                      {statusOptions.map(status => (
                        <option key={status} value={status}>{status}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Date Applied *</label>
                    <input
                      type="date"
                      name="dateApplied"
                      value={formData.dateApplied}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Notes</label>
                  <textarea
                    name="notes"
                    value={formData.notes}
                    onChange={handleInputChange}
                    rows="4"
                    placeholder="Add any additional notes about the application..."
                  />
                </div>

                <div className="form-actions">
                  <button type="submit" className="btn-primary">
                    {editingJob ? 'Update' : 'Add'} Application
                  </button>
                  <button 
                    type="button" 
                    className="btn-cancel" 
                    onClick={() => {
                      setShowAddForm(false);
                      setEditingJob(null);
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          <div className="card">
            <h2>Your Applications ({trackedJobs.length})</h2>
            
            {loading && <div className="loading">Loading...</div>}
            
            {!loading && trackedJobs.length === 0 && (
              <div className="empty-state">
                <p>No applications tracked yet. Add your first application to get started!</p>
              </div>
            )}

            {!loading && trackedJobs.length > 0 && (
              <div className="jobs-grid">
                {trackedJobs.map(job => (
                  <div key={job.id} className="job-tracker-card">
                    <div className="job-tracker-header">
                      <div>
                        <h3>{job.position}</h3>
                        <p className="company-name">{job.company}</p>
                      </div>
                      <div 
                        className="status-badge" 
                        style={{ backgroundColor: getStatusColor(job.status) }}
                      >
                        {job.status}
                      </div>
                    </div>
                    
                    <div className="job-tracker-details">
                      <p><strong>Applied:</strong> {new Date(job.dateApplied).toLocaleDateString()}</p>
                      {job.notes && (
                        <p className="job-notes"><strong>Notes:</strong> {job.notes}</p>
                      )}
                    </div>

                    <div className="job-tracker-actions">
                      <button 
                        className="btn-edit" 
                        onClick={() => handleEdit(job)}
                      >
                        ✏️ Edit
                      </button>
                      <button 
                        className="btn-delete" 
                        onClick={() => handleDelete(job.id)}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default JobTracker;
