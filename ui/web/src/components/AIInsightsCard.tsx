import { useState, useEffect } from 'react'
import { Brain, TrendingUp, AlertTriangle, CheckCircle, Clock, Star, Target } from 'lucide-react'
import axios from 'axios'

interface AIInsight {
  type: string
  title: string
  description: string
  confidence: number
  priority: 'high' | 'medium' | 'low'
}

interface AIRecommendation {
  type: string
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  actions: string[]
}

interface AITrend {
  scope: 'project' | 'author'
  trends: Array<{
    date: string
    mr_count: number
    avg_cycle_time: number
    avg_risk_score: number
  }>
}

interface AIInsightsData {
  mr_id: number
  timestamp: string
  ai_insights: AIInsight[]
  recommendations: AIRecommendation[]
  trends: AITrend[]
  predictions: any
  data_freshness: string
  confidence_score: number
}

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8080/api/v1'

interface AIInsightsCardProps {
  mrId: number
  onClose?: () => void
}

export const AIInsightsCard = ({ mrId, onClose }: AIInsightsCardProps) => {
  const [insights, setInsights] = useState<AIInsightsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'insights' | 'recommendations' | 'trends' | 'predictions'>('insights')

  useEffect(() => {
    fetchAIInsights()
  }, [mrId])

  const fetchAIInsights = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE_URL}/ai/mr/${mrId}/insights`)
      setInsights(response.data.data)
      setError(null)
    } catch (err) {
      setError('Failed to fetch AI insights')
      console.error('Error fetching AI insights:', err)
    } finally {
      setLoading(false)
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return '#dc3545'
      case 'medium':
        return '#ffc107'
      case 'low':
        return '#28a745'
      default:
        return '#6c757d'
    }
  }

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <AlertTriangle className="w-4 h-4" />
      case 'medium':
        return <Clock className="w-4 h-4" />
      case 'low':
        return <CheckCircle className="w-4 h-4" />
      default:
        return <Star className="w-4 h-4" />
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
          <Brain className="w-5 h-5 text-blue-500" />
          <h3 style={{ margin: 0, color: '#333' }}>AI Insights</h3>
        </div>
        <p>Loading AI insights...</p>
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
          <Brain className="w-5 h-5 text-blue-500" />
          <h3 style={{ margin: 0, color: '#333' }}>AI Insights</h3>
        </div>
        <p style={{ color: '#dc3545' }}>{error}</p>
        <button onClick={fetchAIInsights} style={{
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

  if (!insights) {
    return null
  }

  return (
    <div style={{ 
      background: 'white', 
      borderRadius: '8px', 
      padding: '20px', 
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      marginBottom: '20px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '15px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Brain className="w-5 h-5 text-blue-500" />
          <h3 style={{ margin: 0, color: '#333' }}>AI Insights</h3>
          <span style={{ 
            background: '#e3f2fd', 
            color: '#1976d2', 
            padding: '2px 8px', 
            borderRadius: '12px', 
            fontSize: '0.8em',
            fontWeight: '500'
          }}>
            {formatConfidence(insights.confidence_score)} confidence
          </span>
        </div>
        {onClose && (
          <button 
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5em',
              cursor: 'pointer',
              color: '#666'
            }}
          >
            ×
          </button>
        )}
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
          { key: 'insights', label: 'Insights', icon: Brain },
          { key: 'recommendations', label: 'Recommendations', icon: Target },
          { key: 'trends', label: 'Trends', icon: TrendingUp },
          { key: 'predictions', label: 'Predictions', icon: Star }
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key as any)}
            style={{
              background: activeTab === key ? '#646cff' : 'transparent',
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
      {activeTab === 'insights' && (
        <div>
          <h4 style={{ margin: '0 0 15px 0', color: '#333' }}>AI-Powered Analysis</h4>
          {insights.ai_insights && insights.ai_insights.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {insights.ai_insights.map((insight, index) => (
                <div 
                  key={index}
                  style={{ 
                    padding: '12px', 
                    border: '1px solid #e0e0e0', 
                    borderRadius: '6px',
                    backgroundColor: '#f9f9f9'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    {getPriorityIcon(insight.priority)}
                    <span style={{ fontWeight: '600', fontSize: '0.9em' }}>
                      {insight.title}
                    </span>
                    <span style={{ 
                      background: getPriorityColor(insight.priority),
                      color: 'white',
                      padding: '2px 6px',
                      borderRadius: '10px',
                      fontSize: '0.7em',
                      fontWeight: '500'
                    }}>
                      {insight.priority}
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.9em', color: '#333' }}>
                    {insight.description}
                  </p>
                  <div style={{ 
                    marginTop: '8px', 
                    fontSize: '0.8em', 
                    color: '#666',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    <span>Confidence: {formatConfidence(insight.confidence)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: '#666', fontStyle: 'italic' }}>
              No AI insights available for this merge request.
            </p>
          )}
        </div>
      )}

      {activeTab === 'recommendations' && (
        <div>
          <h4 style={{ margin: '0 0 15px 0', color: '#333' }}>Actionable Recommendations</h4>
          {insights.recommendations && insights.recommendations.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {insights.recommendations.map((rec, index) => (
                <div 
                  key={index}
                  style={{ 
                    padding: '12px', 
                    border: '1px solid #e0e0e0', 
                    borderRadius: '6px',
                    backgroundColor: '#f9f9f9'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    {getPriorityIcon(rec.priority)}
                    <span style={{ fontWeight: '600', fontSize: '0.9em' }}>
                      {rec.title}
                    </span>
                    <span style={{ 
                      background: getPriorityColor(rec.priority),
                      color: 'white',
                      padding: '2px 6px',
                      borderRadius: '10px',
                      fontSize: '0.7em',
                      fontWeight: '500'
                    }}>
                      {rec.priority}
                    </span>
                  </div>
                  <p style={{ margin: '0 0 8px 0', fontSize: '0.9em', color: '#333' }}>
                    {rec.description}
                  </p>
                  {rec.actions && rec.actions.length > 0 && (
                    <div>
                      <p style={{ margin: '8px 0 4px 0', fontSize: '0.8em', fontWeight: '600', color: '#666' }}>
                        Actions:
                      </p>
                      <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.8em', color: '#666' }}>
                        {rec.actions.map((action, actionIndex) => (
                          <li key={actionIndex}>{action}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: '#666', fontStyle: 'italic' }}>
              No recommendations available for this merge request.
            </p>
          )}
        </div>
      )}

      {activeTab === 'trends' && (
        <div>
          <h4 style={{ margin: '0 0 15px 0', color: '#333' }}>Trend Analysis</h4>
          {insights.trends && Object.keys(insights.trends).length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {Object.entries(insights.trends).map(([scope, trendData]) => (
                <div key={scope} style={{ 
                  padding: '12px', 
                  border: '1px solid #e0e0e0', 
                  borderRadius: '6px',
                  backgroundColor: '#f9f9f9'
                }}>
                  <h5 style={{ margin: '0 0 10px 0', color: '#333', textTransform: 'capitalize' }}>
                    {scope} Trends
                  </h5>
                  {trendData.trends && trendData.trends.length > 0 ? (
                    <div style={{ fontSize: '0.8em', color: '#666' }}>
                      <p>Recent activity: {trendData.trends.length} data points</p>
                      <p>Average cycle time: {trendData.trends.reduce((acc, t) => acc + t.avg_cycle_time, 0) / trendData.trends.length} hours</p>
                      <p>Average risk score: {trendData.trends.reduce((acc, t) => acc + t.avg_risk_score, 0) / trendData.trends.length}</p>
                    </div>
                  ) : (
                    <p style={{ color: '#666', fontStyle: 'italic' }}>
                      No trend data available for {scope}.
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: '#666', fontStyle: 'italic' }}>
              No trend analysis available for this merge request.
            </p>
          )}
        </div>
      )}

      {activeTab === 'predictions' && (
        <div>
          <h4 style={{ margin: '0 0 15px 0', color: '#333' }}>Predictive Insights</h4>
          {insights.predictions && !insights.predictions.error ? (
            <div style={{ 
              padding: '12px', 
              border: '1px solid #e0e0e0', 
              borderRadius: '6px',
              backgroundColor: '#f9f9f9'
            }}>
              <p style={{ margin: 0, fontSize: '0.9em', color: '#333' }}>
                {insights.predictions.raw_response || 'Predictive insights are being generated...'}
              </p>
            </div>
          ) : (
            <p style={{ color: '#666', fontStyle: 'italic' }}>
              No predictive insights available for this merge request.
            </p>
          )}
        </div>
      )}

      <div style={{ 
        marginTop: '15px', 
        paddingTop: '15px', 
        borderTop: '1px solid #e0e0e0',
        fontSize: '0.8em',
        color: '#666',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span>Generated: {new Date(insights.timestamp).toLocaleString()}</span>
        <button 
          onClick={fetchAIInsights}
          style={{
            background: '#646cff',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '0.8em'
          }}
        >
          Refresh
        </button>
      </div>
    </div>
  )
}
