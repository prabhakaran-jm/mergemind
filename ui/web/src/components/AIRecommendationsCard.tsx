import { useState, useEffect } from 'react'
import { Target, AlertTriangle, Clock, Star, Zap } from 'lucide-react'
import axios from 'axios'
import { API_BASE_URL } from '../utils/apiConfig'

interface AIRecommendation {
  type: string
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  actions: string[]
}

interface AIRecommendationsData {
  mr_id: number
  recommendations: AIRecommendation[]
  total_count: number
  high_priority_count: number
  timestamp: string
}

interface AIRecommendationsCardProps {
  mrId: number
  onClose?: () => void
}

export const AIRecommendationsCard = ({ mrId, onClose }: AIRecommendationsCardProps) => {
  const [recommendations, setRecommendations] = useState<AIRecommendationsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchRecommendations()
  }, [mrId])

  const fetchRecommendations = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE_URL}/ai/mr/${mrId}/recommendations`)
      setRecommendations(response.data.data)
      setError(null)
    } catch (err) {
      setError('Failed to fetch AI recommendations')
      console.error('Error fetching AI recommendations:', err)
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

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'risk_mitigation':
        return <AlertTriangle className="w-4 h-4 text-red-500" />
      case 'pipeline_fix':
        return <Zap className="w-4 h-4 text-yellow-500" />
      case 'stale_mr':
        return <Clock className="w-4 h-4 text-orange-500" />
      case 'large_change':
        return <Target className="w-4 h-4 text-blue-500" />
      default:
        return <Star className="w-4 h-4 text-gray-500" />
    }
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
          <Target className="w-5 h-5 text-green-500" />
          <h3 style={{ margin: 0, color: '#333' }}>AI Recommendations</h3>
        </div>
        <p>Loading AI recommendations...</p>
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
          <Target className="w-5 h-5 text-green-500" />
          <h3 style={{ margin: 0, color: '#333' }}>AI Recommendations</h3>
        </div>
        <p style={{ color: '#dc3545' }}>{error}</p>
        <button onClick={fetchRecommendations} style={{
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

  if (!recommendations) {
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
          <Target className="w-5 h-5 text-green-500" />
          <h3 style={{ margin: 0, color: '#333' }}>AI Recommendations</h3>
          <span style={{ 
            background: '#e8f5e8', 
            color: '#28a745', 
            padding: '2px 8px', 
            borderRadius: '12px', 
            fontSize: '0.8em',
            fontWeight: '500'
          }}>
            {recommendations.total_count} total
          </span>
          {recommendations.high_priority_count > 0 && (
            <span style={{ 
              background: '#f8d7da', 
              color: '#dc3545', 
              padding: '2px 8px', 
              borderRadius: '12px', 
              fontSize: '0.8em',
              fontWeight: '500'
            }}>
              {recommendations.high_priority_count} high priority
            </span>
          )}
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

      {recommendations.recommendations && recommendations.recommendations.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {recommendations.recommendations.map((rec, index) => (
            <div 
              key={index}
              style={{ 
                padding: '15px', 
                border: '1px solid #e0e0e0', 
                borderRadius: '8px',
                backgroundColor: '#f9f9f9',
                borderLeft: `4px solid ${getPriorityColor(rec.priority)}`
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                {getTypeIcon(rec.type)}
                <span style={{ fontWeight: '600', fontSize: '1em', color: '#333' }}>
                  {rec.title}
                </span>
                <span style={{ 
                  background: getPriorityColor(rec.priority),
                  color: 'white',
                  padding: '3px 8px',
                  borderRadius: '12px',
                  fontSize: '0.7em',
                  fontWeight: '600',
                  textTransform: 'uppercase'
                }}>
                  {rec.priority}
                </span>
              </div>
              
              <p style={{ margin: '0 0 12px 0', fontSize: '0.9em', color: '#555', lineHeight: '1.4' }}>
                {rec.description}
              </p>
              
              {rec.actions && rec.actions.length > 0 && (
                <div>
                  <p style={{ 
                    margin: '0 0 8px 0', 
                    fontSize: '0.8em', 
                    fontWeight: '600', 
                    color: '#666',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  }}>
                    Recommended Actions:
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {rec.actions.map((action, actionIndex) => (
                      <div 
                        key={actionIndex}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          padding: '6px 10px',
                          background: 'white',
                          borderRadius: '4px',
                          border: '1px solid #e0e0e0',
                          fontSize: '0.85em',
                          color: '#333'
                        }}
                      >
                        <div style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          background: getPriorityColor(rec.priority)
                        }} />
                        <span>{action}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
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
          <Target className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p>No recommendations available for this merge request.</p>
          <p style={{ fontSize: '0.8em', marginTop: '8px' }}>
            The AI analysis suggests this MR is in good shape!
          </p>
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
        <span>Generated: {new Date(recommendations.timestamp).toLocaleString()}</span>
        <button 
          onClick={fetchRecommendations}
          style={{
            background: '#28a745',
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
          <Target className="w-3 h-3" />
          Refresh
        </button>
      </div>
    </div>
  )
}
