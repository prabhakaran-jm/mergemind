import { useState, useEffect } from 'react'
import { GitBranch, AlertTriangle, CheckCircle, Clock, User, Brain, Target } from 'lucide-react'
import axios from 'axios'
import { AIInsightsCard } from './components/AIInsightsCard'
import { AIRecommendationsCard } from './components/AIRecommendationsCard'
import { AIDashboardCard } from './components/AIDashboardCard'
import { API_BASE_URL } from './utils/apiConfig'

interface MRItem {
  mr_id: number
  project_id: number
  title: string
  author: string
  age_hours: number
  risk_band: string
  risk_score: number
  pipeline_status: string
  approvals_left: number
  notes_count_24_h: number
  additions: number
  deletions: number
}

interface MRSummary {
  summary: string[]
  risks: string[]
  tests: string[]
}

interface MRContext {
  mr_id: number
  project_id: number
  title: string
  author: {
    user_id: number
    name: string
  }
  state: string
  age_hours: number
  risk: {
    score: number
    band: string
    reasons: string[]
  }
  last_pipeline: {
    status: string
    age_min: number
  }
  approvals_left: number
  notes_recent: number
  size: {
    additions: number
    deletions: number
  }
  labels: string[]
  web_url?: string
  source_branch?: string
  target_branch?: string
}

interface Reviewer {
  user_id: number
  name: string
  score: number
  reason: string
}

function App() {
  const [mrs, setMrs] = useState<MRItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedMR, setSelectedMR] = useState<MRContext | null>(null)
  const [summary, setSummary] = useState<MRSummary | null>(null)
  const [reviewers, setReviewers] = useState<Reviewer[]>([])
  const [showModal, setShowModal] = useState(false)
  const [modalLoading, setModalLoading] = useState(false)
  const [showAIInsights, setShowAIInsights] = useState(false)
  const [showAIRecommendations, setShowAIRecommendations] = useState(false)
  const [showAIDashboard, setShowAIDashboard] = useState(false)

  useEffect(() => {
    fetchMRs()
  }, [])

  const fetchMRs = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE_URL}/mrs?limit=50`)
      setMrs(response.data.items)
      setError(null)
    } catch (err) {
      setError('Failed to fetch merge requests')
      console.error('Error fetching MRs:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSummaryClick = async (mrId: number) => {
    try {
      setModalLoading(true)
      setShowModal(true)
      
      // Fetch MR context
      const contextResponse = await axios.get(`${API_BASE_URL}/mr/${mrId}/context`)
      setSelectedMR(contextResponse.data)
      
      // Fetch summary
      const summaryResponse = await axios.post(`${API_BASE_URL}/mr/${mrId}/summary`)
      setSummary(summaryResponse.data)
      
      // Fetch reviewers
      const reviewersResponse = await axios.get(`${API_BASE_URL}/mr/${mrId}/reviewers`)
      setReviewers(reviewersResponse.data.reviewers)
      
    } catch (err) {
      setError('Failed to fetch MR details')
      console.error('Error fetching MR details:', err)
    } finally {
      setModalLoading(false)
    }
  }

  const formatAge = (hours: number) => {
    if (hours < 24) {
      return `${Math.round(hours)}h`
    } else {
      return `${Math.round(hours / 24)}d`
    }
  }

  const getRiskBadgeClass = (band: string) => {
    return `risk-badge ${band.toLowerCase()}`
  }

  const getPipelineIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <AlertTriangle className="w-4 h-4 text-red-500" />
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />
    }
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">
          <p>Loading merge requests...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <div className="error">
          <p>{error}</p>
          <button onClick={fetchMRs}>Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1>MergeMind</h1>
            <p>AI-Powered Merge Request Analysis</p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button 
              onClick={() => setShowAIDashboard(true)}
              style={{
                background: '#7c3aed',
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.9em'
              }}
            >
              <Brain className="w-4 h-4" />
              AI Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* AI Analysis Overview Section */}
      <div className="ai-analysis-overview" style={{ marginTop: '2rem' }}>
        <div className="overview-header">
          <h2>AI Analysis Overview</h2>
          <p>Real-time insights into your merge request pipeline</p>
          <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.5rem' }}>Last sync: 2m ago</p>
        </div>
        <div className="overview-stats">
          <div className="stat-card active-mrs" title="Total number of active merge requests">
            <div className="stat-icon">
              <Brain className="w-6 h-6" />
            </div>
            <div className="stat-content">
              <div className="stat-number">{mrs.length}</div>
              <div className="stat-label">Active MRs</div>
              <div className="stat-sublabel">Currently open</div>
            </div>
          </div>
          <div className="stat-card high-risk" title="Merge requests with high risk assessment">
            <div className="stat-icon">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div className="stat-content">
              <div className="stat-number">{mrs.filter(mr => mr.risk_band === 'HIGH' || mr.risk_band === 'high').length}</div>
              <div className="stat-label">High Risk</div>
              <div className="stat-sublabel">Requires attention</div>
            </div>
          </div>
          <div className="stat-card passing-pipelines" title="Merge requests with successful pipeline runs">
            <div className="stat-icon">
              <CheckCircle className="w-6 h-6" />
            </div>
            <div className="stat-content">
              <div className="stat-number">{mrs.filter(mr => mr.pipeline_status === 'success').length}</div>
              <div className="stat-label">Passing Pipelines</div>
              <div className="stat-sublabel">Build successful</div>
            </div>
          </div>
          <div className="stat-card ready-to-merge" title="Merge requests ready for final approval">
            <div className="stat-icon">
              <User className="w-6 h-6" />
            </div>
            <div className="stat-content">
              <div className="stat-number">{mrs.filter(mr => mr.approvals_left === 0).length}</div>
              <div className="stat-label">Ready to Merge</div>
              <div className="stat-sublabel">All approvals received</div>
            </div>
          </div>
        </div>
      </div>

      <div className="table-container">
        <table className="table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Author</th>
            <th>Age</th>
            <th>Risk</th>
            <th>Pipeline</th>
            <th>Approvals</th>
            <th>Activity</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {mrs.map((mr) => (
            <tr key={mr.mr_id}>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <GitBranch className="w-4 h-4 text-gray-500" />
                  <span>{mr.title}</span>
                </div>
              </td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <User className="w-4 h-4 text-gray-500" />
                  <span>{mr.author}</span>
                </div>
              </td>
              <td>{formatAge(mr.age_hours)}</td>
              <td>
                <span className={`status-pill risk-${mr.risk_band.toLowerCase()}`} title={mr.risk_band === 'LOW' ? 'Safe to merge' : mr.risk_band === 'MEDIUM' ? 'Review recommended' : 'Requires attention'}>
                  {mr.risk_band === 'HIGH' && <AlertTriangle className="w-4 h-4" />}
                  {mr.risk_band === 'MEDIUM' && <Clock className="w-4 h-4" />}
                  {mr.risk_band === 'LOW' && <CheckCircle className="w-4 h-4" />}
                  {mr.risk_band}
                </span>
              </td>
              <td>
                <span className={`status-pill pipeline-${mr.pipeline_status}`} title={mr.pipeline_status === 'success' ? 'Build successful' : mr.pipeline_status === 'failed' ? 'Build failed' : mr.pipeline_status === 'running' ? 'Build in progress' : 'No data'}>
                  {getPipelineIcon(mr.pipeline_status)}
                  {mr.pipeline_status}
                </span>
              </td>
              <td>{mr.approvals_left}</td>
              <td>{mr.notes_count_24_h} notes</td>
              <td>
                <div className="action-group">
                  <button 
                    className="action-button summary"
                    onClick={() => handleSummaryClick(mr.mr_id)}
                    title="View summary"
                  >
                    Summary
                  </button>
                  <button 
                    className="action-button ai-insights"
                    onClick={() => setShowAIInsights(true)}
                    title="AI-generated insights"
                  >
                    <Brain className="w-3 h-3" />
                    AI Insights
                  </button>
                  <button 
                    className="action-button ai-recommendations"
                    onClick={() => setShowAIRecommendations(true)}
                    title="Recommended next steps"
                  >
                    <Target className="w-3 h-3" />
                    AI Recommendations
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal">
          <div className="modal-content">
            <div className="modal-header">
              <h2 className="modal-title">
                {selectedMR?.title || 'Merge Request Summary'}
              </h2>
              <button 
                className="close-button"
                onClick={() => setShowModal(false)}
              >
                ×
              </button>
            </div>

            {modalLoading ? (
              <div className="loading">
                <p>Loading summary...</p>
              </div>
            ) : (
              <>
                {selectedMR && (
                  <div className="summary-section">
                    <h3>Context</h3>
                    <p><strong>Author:</strong> {selectedMR.author.name}</p>
                    <p><strong>Age:</strong> {formatAge(selectedMR.age_hours)}</p>
                    <p><strong>Risk:</strong> 
                      <span className={getRiskBadgeClass(selectedMR.risk.band)}>
                        {selectedMR.risk.band} ({selectedMR.risk.score})
                      </span>
                    </p>
                    <p><strong>Pipeline:</strong> {selectedMR.last_pipeline.status}</p>
                    <p><strong>Approvals Left:</strong> {selectedMR.approvals_left}</p>
                    <p><strong>Changes:</strong> +{selectedMR.size.additions} / -{selectedMR.size.deletions}</p>
                    {selectedMR.labels.length > 0 && (
                      <p><strong>Labels:</strong> {selectedMR.labels.join(', ')}</p>
                    )}
                  </div>
                )}

                {summary && (
                  <div className="summary-section">
                    <h3>AI Summary</h3>
                    <ul className="summary-list">
                      {summary.summary.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {summary && summary.risks.length > 0 && (
                  <div className="summary-section">
                    <h3>Risks</h3>
                    <ul className="summary-list">
                      {summary.risks.map((risk, index) => (
                        <li key={index}>{risk}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {summary && summary.tests.length > 0 && (
                  <div className="summary-section">
                    <h3>Suggested Tests</h3>
                    <ul className="summary-list">
                      {summary.tests.map((test, index) => (
                        <li key={index}>{test}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {reviewers.length > 0 && (
                  <div className="summary-section">
                    <h3>Suggested Reviewers</h3>
                    <ul className="summary-list">
                      {reviewers.map((reviewer) => (
                        <li key={reviewer.user_id}>
                          <strong>{reviewer.name}</strong> - {reviewer.reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* AI Actions */}
                <div className="summary-section">
                  <h3>AI-Powered Analysis</h3>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <button 
                      onClick={() => {
                        setShowModal(false)
                        setShowAIInsights(true)
                      }}
                      style={{
                        background: '#7c3aed',
                        color: 'white',
                        border: 'none',
                        padding: '8px 16px',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '0.9em'
                      }}
                    >
                      <Brain className="w-4 h-4" />
                      AI Insights
                    </button>
                    <button 
                      onClick={() => {
                        setShowModal(false)
                        setShowAIRecommendations(true)
                      }}
                      style={{
                        background: '#28a745',
                        color: 'white',
                        border: 'none',
                        padding: '8px 16px',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '0.9em'
                      }}
                    >
                      <Target className="w-4 h-4" />
                      AI Recommendations
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* AI Insights Modal */}
      {showAIInsights && selectedMR && (
        <div className="modal">
          <div className="modal-content" style={{ maxWidth: '800px', maxHeight: '90vh', overflow: 'auto' }}>
            <div className="modal-header">
              <h2 className="modal-title">
                AI Insights - {selectedMR.title}
              </h2>
              <button 
                className="close-button"
                onClick={() => setShowAIInsights(false)}
              >
                ×
              </button>
            </div>
            <AIInsightsCard mrId={selectedMR.mr_id} onClose={() => setShowAIInsights(false)} />
          </div>
        </div>
      )}

      {/* AI Recommendations Modal */}
      {showAIRecommendations && selectedMR && (
        <div className="modal">
          <div className="modal-content" style={{ maxWidth: '800px', maxHeight: '90vh', overflow: 'auto' }}>
            <div className="modal-header">
              <h2 className="modal-title">
                AI Recommendations - {selectedMR.title}
              </h2>
              <button 
                className="close-button"
                onClick={() => setShowAIRecommendations(false)}
              >
                ×
              </button>
            </div>
            <AIRecommendationsCard mrId={selectedMR.mr_id} onClose={() => setShowAIRecommendations(false)} />
          </div>
        </div>
      )}

      {/* AI Dashboard Modal */}
      {showAIDashboard && (
        <div className="modal">
          <div className="modal-content" style={{ maxWidth: '900px', maxHeight: '90vh', overflow: 'auto' }}>
            <div className="modal-header">
              <h2 className="modal-title">
                AI Dashboard
              </h2>
              <button 
                className="close-button"
                onClick={() => setShowAIDashboard(false)}
              >
                ×
              </button>
            </div>
            <AIDashboardCard />
          </div>
        </div>
      )}
    </div>
  )
}

export default App
