import { useState, useEffect } from 'react'
import axios from 'axios'
import { API_BASE_URL } from '../utils/apiConfig'
import { renderComplexContent } from '../utils/contentRenderer'
import { AlertTriangle, Clock, CheckCircle, Star, Brain, TrendingUp } from 'lucide-react'

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

interface AIInsightsCardProps {
  mrId: number
  onClose?: () => void
}

export const AIInsightsCard = ({ mrId, onClose }: AIInsightsCardProps) => {
  const [insights, setInsights] = useState<AIInsightsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'insights' | 'trends' | 'predictions'>('insights')

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
                  <div style={{ margin: 0, fontSize: '0.9em', color: '#333' }}>
                    {renderComplexContent(insight.description, '#646cff')}
                  </div>
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
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {renderComplexContent(insights.predictions.raw_response || insights.predictions, '#646cff')}
            </div>
          ) : (
            <div style={{
              padding: '20px',
              textAlign: 'center',
              color: '#666',
              fontStyle: 'italic',
              background: '#f8f9fa',
              borderRadius: '6px',
              border: '1px dashed #dee2e6'
            }}>
              <Star className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p>No predictive insights available for this merge request.</p>
              <p style={{ fontSize: '0.8em', marginTop: '8px' }}>
                AI predictions are being generated based on historical patterns.
              </p>
            </div>
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
