import { useState, useEffect } from 'react'
import { AlertTriangle, Clock, User, GitBranch } from 'lucide-react'
import axios from 'axios'
import { API_BASE_URL } from '../utils/apiConfig'

interface Blocker {
  mr_id: number
  project_id: number
  title: string
  author: string
  age_hours: number
  risk_band: string
  risk_score: number
  blocking_reason: string
  pipeline_status: string
  approvals_left: number
  notes_count_24h: number
}

export const BlockersCard = () => {
  const [blockers, setBlockers] = useState<Blocker[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchBlockers()
  }, [])

  const fetchBlockers = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE_URL}/blockers/top?limit=5`)
      setBlockers(response.data)
      setError(null)
    } catch (err) {
      setError('Failed to fetch blockers')
      console.error('Error fetching blockers:', err)
    } finally {
      setLoading(false)
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

  const getBlockingIcon = (reason: string) => {
    if (reason.includes('Pipeline failed')) {
      return <AlertTriangle className="w-4 h-4 text-red-500" />
    } else {
      return <Clock className="w-4 h-4 text-yellow-500" />
    }
  }

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Loading blockers...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#dc3545' }}>
        <p>{error}</p>
        <button onClick={fetchBlockers}>Retry</button>
      </div>
    )
  }

  if (blockers.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>No blocking merge requests found!</p>
      </div>
    )
  }

  return (
    <div style={{ 
      background: 'white', 
      borderRadius: '8px', 
      padding: '20px', 
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      marginBottom: '20px'
    }}>
      <h3 style={{ margin: '0 0 15px 0', color: '#333' }}>
        Top Blocking Merge Requests
      </h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {blockers.map((blocker) => (
          <div 
            key={blocker.mr_id}
            style={{ 
              padding: '12px', 
              border: '1px solid #e0e0e0', 
              borderRadius: '6px',
              backgroundColor: '#f9f9f9'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <GitBranch className="w-4 h-4 text-gray-500" />
              <span style={{ fontWeight: '600', fontSize: '0.9em' }}>
                MR #{blocker.mr_id}
              </span>
              <span className={getRiskBadgeClass(blocker.risk_band)}>
                {blocker.risk_band}
              </span>
            </div>
            
            <p style={{ margin: '0 0 8px 0', fontSize: '0.9em', color: '#333' }}>
              {blocker.title}
            </p>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.8em', color: '#666' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <User className="w-3 h-3" />
                <span>{blocker.author}</span>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock className="w-3 h-3" />
                <span>{formatAge(blocker.age_hours)}</span>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                {getBlockingIcon(blocker.blocking_reason)}
                <span>{blocker.blocking_reason}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div style={{ marginTop: '15px', textAlign: 'center' }}>
        <button 
          onClick={fetchBlockers}
          style={{ 
            background: '#646cff', 
            color: 'white', 
            border: 'none', 
            padding: '8px 16px', 
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Refresh
        </button>
      </div>
    </div>
  )
}
