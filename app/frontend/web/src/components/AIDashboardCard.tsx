import { useState, useEffect } from 'react'
import { Brain, TrendingUp, Target, AlertTriangle, CheckCircle, Clock, BarChart3 } from 'lucide-react'
import axios from 'axios'
import { API_BASE_URL } from '../utils/apiConfig'

interface AIInsightsOverview {
  total_mrs_analyzed: number
  high_risk_mrs: number
  recommendations_generated: number
  avg_confidence_score: number
  last_updated: string
}

interface ProjectInsight {
  project_id: number
  insights: {
    message: string
    features: string[]
  }
  timestamp: string
}

interface TeamInsight {
  insights: {
    message: string
    features: string[]
  }
  timestamp: string
}

export const AIDashboardCard = () => {
  const [overview, setOverview] = useState<AIInsightsOverview | null>(null)
  const [projectInsights, setProjectInsights] = useState<ProjectInsight | null>(null)
  const [teamInsights, setTeamInsights] = useState<TeamInsight | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'projects' | 'team'>('overview')

  useEffect(() => {
    fetchAIDashboard()
  }, [])

  const fetchAIDashboard = async () => {
    try {
      setLoading(true)
      
      // Fetch project insights (using project ID 1 as example)
      const projectResponse = await axios.get(`${API_BASE_URL}/ai/analytics/project/1/insights`)
      setProjectInsights(projectResponse.data.data)
      
      // Fetch team insights
      const teamResponse = await axios.get(`${API_BASE_URL}/ai/analytics/team/insights`)
      setTeamInsights(teamResponse.data.data)
      
      // Mock overview data (since we don't have a dedicated endpoint yet)
      setOverview({
        total_mrs_analyzed: 42,
        high_risk_mrs: 8,
        recommendations_generated: 156,
        avg_confidence_score: 0.87,
        last_updated: new Date().toISOString()
      })
      
      setError(null)
    } catch (err) {
      setError('Failed to fetch AI dashboard data')
      console.error('Error fetching AI dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatConfidence = (score: number) => {
    return `${Math.round(score * 100)}%`
  }

  if (loading) {
    return (
      <div style={{ 
        background: 'white', 
        borderRadius: '8px', 
        padding: '20px', 
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        marginBottom: '20px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '15px' }}>
          <Brain className="w-5 h-5 text-purple-500" />
          <h3 style={{ margin: 0, color: '#333' }}>AI Dashboard</h3>
        </div>
        <p>Loading AI dashboard...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ 
        background: 'white', 
        borderRadius: '8px', 
        padding: '20px', 
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        marginBottom: '20px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '15px' }}>
          <Brain className="w-5 h-5 text-purple-500" />
          <h3 style={{ margin: 0, color: '#333' }}>AI Dashboard</h3>
        </div>
        <p style={{ color: '#dc3545' }}>{error}</p>
        <button onClick={fetchAIDashboard} style={{
          background: '#646cff',
          color: 'white',
          border: 'none',
          padding: '8px 16px',
          borderRadius: '4px',
          cursor: 'pointer',
          marginTop: '10px'
        }}>
          Retry
        </button>
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
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '15px' }}>
        <Brain className="w-5 h-5 text-purple-500" />
        <h3 style={{ margin: 0, color: '#333' }}>AI Dashboard</h3>
        <span style={{ 
          background: '#f3e8ff', 
          color: '#7c3aed', 
          padding: '2px 8px', 
          borderRadius: '12px', 
          fontSize: '0.8em',
          fontWeight: '500'
        }}>
          Beta
        </span>
      </div>

      {/* Tab Navigation */}
      <div style={{ 
        display: 'flex', 
        gap: '10px', 
        marginBottom: '20px',
        borderBottom: '1px solid #e0e0e0',
        paddingBottom: '10px'
      }}>
        {[
          { key: 'overview', label: 'Overview', icon: BarChart3 },
          { key: 'projects', label: 'Projects', icon: TrendingUp },
          { key: 'team', label: 'Team', icon: Target }
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key as any)}
            style={{
              background: activeTab === key ? '#7c3aed' : 'transparent',
              color: activeTab === key ? 'white' : '#666',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '4px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.9em'
            }}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && overview && (
        <div>
          <h4 style={{ margin: '0 0 15px 0', color: '#333' }}>AI Analysis Overview</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
            <div style={{ 
              padding: '15px', 
              background: '#f8f9fa', 
              borderRadius: '6px',
              border: '1px solid #e0e0e0'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <BarChart3 className="w-4 h-4 text-blue-500" />
                <span style={{ fontSize: '0.8em', fontWeight: '600', color: '#666' }}>Total MRs Analyzed</span>
              </div>
              <div style={{ fontSize: '1.5em', fontWeight: '700', color: '#333' }}>
                {overview.total_mrs_analyzed}
              </div>
            </div>

            <div style={{ 
              padding: '15px', 
              background: '#f8f9fa', 
              borderRadius: '6px',
              border: '1px solid #e0e0e0'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <span style={{ fontSize: '0.8em', fontWeight: '600', color: '#666' }}>High Risk MRs</span>
              </div>
              <div style={{ fontSize: '1.5em', fontWeight: '700', color: '#dc3545' }}>
                {overview.high_risk_mrs}
              </div>
            </div>

            <div style={{ 
              padding: '15px', 
              background: '#f8f9fa', 
              borderRadius: '6px',
              border: '1px solid #e0e0e0'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Target className="w-4 h-4 text-green-500" />
                <span style={{ fontSize: '0.8em', fontWeight: '600', color: '#666' }}>Recommendations</span>
              </div>
              <div style={{ fontSize: '1.5em', fontWeight: '700', color: '#28a745' }}>
                {overview.recommendations_generated}
              </div>
            </div>

            <div style={{ 
              padding: '15px', 
              background: '#f8f9fa', 
              borderRadius: '6px',
              border: '1px solid #e0e0e0'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <CheckCircle className="w-4 h-4 text-purple-500" />
                <span style={{ fontSize: '0.8em', fontWeight: '600', color: '#666' }}>Avg Confidence</span>
              </div>
              <div style={{ fontSize: '1.5em', fontWeight: '700', color: '#7c3aed' }}>
                {formatConfidence(overview.avg_confidence_score)}
              </div>
            </div>
          </div>

          <div style={{ 
            marginTop: '20px', 
            padding: '15px', 
            background: '#e3f2fd', 
            borderRadius: '6px',
            border: '1px solid #bbdefb'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Clock className="w-4 h-4 text-blue-500" />
              <span style={{ fontSize: '0.8em', fontWeight: '600', color: '#1976d2' }}>Last Updated</span>
            </div>
            <p style={{ margin: 0, fontSize: '0.9em', color: '#1976d2' }}>
              {new Date(overview.last_updated).toLocaleString()}
            </p>
          </div>
        </div>
      )}

      {activeTab === 'projects' && projectInsights && (
        <div>
          <h4 style={{ margin: '0 0 15px 0', color: '#333' }}>Project-Level Insights</h4>
          <div style={{ 
            padding: '15px', 
            background: '#f8f9fa', 
            borderRadius: '6px',
            border: '1px solid #e0e0e0'
          }}>
            <p style={{ margin: '0 0 10px 0', fontSize: '0.9em', color: '#333' }}>
              {projectInsights.insights.message}
            </p>
            <div>
              <p style={{ margin: '0 0 8px 0', fontSize: '0.8em', fontWeight: '600', color: '#666' }}>
                Available Features:
              </p>
              <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.8em', color: '#666' }}>
                {projectInsights.insights.features.map((feature, index) => (
                  <li key={index}>{feature}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'team' && teamInsights && (
        <div>
          <h4 style={{ margin: '0 0 15px 0', color: '#333' }}>Team-Level Insights</h4>
          <div style={{ 
            padding: '15px', 
            background: '#f8f9fa', 
            borderRadius: '6px',
            border: '1px solid #e0e0e0'
          }}>
            <p style={{ margin: '0 0 10px 0', fontSize: '0.9em', color: '#333' }}>
              {teamInsights.insights.message}
            </p>
            <div>
              <p style={{ margin: '0 0 8px 0', fontSize: '0.8em', fontWeight: '600', color: '#666' }}>
                Available Features:
              </p>
              <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.8em', color: '#666' }}>
                {teamInsights.insights.features.map((feature, index) => (
                  <li key={index}>{feature}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      <div style={{ 
        marginTop: '20px', 
        paddingTop: '15px', 
        borderTop: '1px solid #e0e0e0',
        fontSize: '0.8em',
        color: '#666',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span>AI Dashboard • Powered by Gemini AI</span>
        <button 
          onClick={fetchAIDashboard}
          style={{
            background: '#7c3aed',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '0.8em',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}
        >
          <Brain className="w-3 h-3" />
          Refresh
        </button>
      </div>
    </div>
  )
}
