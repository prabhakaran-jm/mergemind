import { useState, useEffect } from 'react'
import { GitBranch, AlertTriangle, CheckCircle, Clock, User } from 'lucide-react'
import axios from 'axios'

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
  notes_count_24h: number
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

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8080/api/v1'

function App() {
  const [mrs, setMrs] = useState<MRItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedMR, setSelectedMR] = useState<MRContext | null>(null)
  const [summary, setSummary] = useState<MRSummary | null>(null)
  const [reviewers, setReviewers] = useState<Reviewer[]>([])
  const [showModal, setShowModal] = useState(false)
  const [modalLoading, setModalLoading] = useState(false)

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
        <h1>MergeMind</h1>
        <p>AI-Powered Merge Request Analysis</p>
      </div>

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
                <span className={getRiskBadgeClass(mr.risk_band)}>
                  {mr.risk_band} ({mr.risk_score})
                </span>
              </td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {getPipelineIcon(mr.pipeline_status)}
                  <span>{mr.pipeline_status}</span>
                </div>
              </td>
              <td>{mr.approvals_left}</td>
              <td>{mr.notes_count_24h} notes</td>
              <td>
                <button onClick={() => handleSummaryClick(mr.mr_id)}>
                  Summary
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

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
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
