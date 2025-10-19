import React from 'react';

/**
 * Simple JSON parser that handles markdown-wrapped JSON
 */
export const parseJsonContent = (content: string): any | null => {
  if (!content || typeof content !== 'string') {
    return null;
  }

  let textToParse = content;

  // If it starts with a markdown fence, strip it.
  if (textToParse.trim().startsWith('```')) {
    textToParse = textToParse.replace(/```(json)?\s*/, '');
  }

  // Attempt to parse what's left. If truncated, this will fail, which is expected.
  if (textToParse.trim().startsWith('{') || textToParse.trim().startsWith('[')) {
    try {
      return JSON.parse(textToParse);
    } catch (e) {
      // Not valid JSON
    }
  }

  return null;
};

/**
 * Renders structured JSON data as human-readable React components
 */
export const renderStructuredJson = (data: any, accentColor: string = '#646cff'): React.ReactNode => {
  if (!data || typeof data !== 'object') {
    return <div style={{ lineHeight: '1.6', color: '#333' }}>{String(data)}</div>;
  }

  // Handle arrays
  if (Array.isArray(data)) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {data.map((item, index) => (
          <div key={index} style={{
            padding: '10px',
            background: '#f8f9fa',
            borderRadius: '6px',
            borderLeft: `3px solid ${accentColor}`
          }}>
            {typeof item === 'object' ? renderStructuredJson(item, accentColor) : String(item)}
          </div>
        ))}
      </div>
    );
  }

  // Handle objects
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      fontSize: '0.95em'
    }}>
      {Object.entries(data).map(([key, value]) => (
        <div key={key} style={{
          padding: '12px',
          background: '#f8f9fa',
          borderRadius: '6px',
          borderLeft: `4px solid ${accentColor}`,
          transition: 'all 0.2s ease'
        }}>
          <div style={{
            fontWeight: '600',
            color: '#1a1a1a',
            marginBottom: '6px',
            fontSize: '0.95em',
            textTransform: 'capitalize',
            letterSpacing: '0.3px'
          }}>
            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </div>
          <div style={{ color: '#4a4a4a', lineHeight: '1.6' }}>
            {typeof value === 'object' && value !== null ? (
              <div style={{
                paddingLeft: '12px',
                borderLeft: '2px solid #e0e0e0',
                marginTop: '8px'
              }}>
                {Array.isArray(value) ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {value.map((item, idx) => (
                      <div key={idx} style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '8px'
                      }}>
                        <span style={{ color: accentColor, fontWeight: 'bold', minWidth: '8px' }}>•</span>
                        <span>{String(item)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  Object.entries(value).map(([subKey, subValue]) => (
                    <div key={subKey} style={{ marginBottom: '8px' }}>
                      <span style={{
                        fontWeight: '500',
                        color: '#666',
                        fontSize: '0.9em'
                      }}>
                        {subKey.replace(/_/g, ' ')}:
                      </span>{' '}
                      <span style={{ color: '#333' }}>{String(subValue)}</span>
                    </div>
                  ))
                )}
              </div>
            ) : (
              <span>{String(value)}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * Cleans markdown artifacts from text content
 */
export const cleanMarkdownArtifacts = (text: string): string => {
  if (!text || typeof text !== 'string') {
    return '';
  }

  let cleanedText = text;

  // Handle truncated code blocks by removing the opening fence if it exists.
  if (cleanedText.trim().startsWith('```')) {
    cleanedText = cleanedText.replace(/```(json)?\s*/, '');
  }

  // This regex is now simpler because we are not trying to capture content,
  // just remove the fences. The primary goal is to clean up truncated input.
  return cleanedText
    .replace(/```/g, '') // Remove any remaining fences
    // Remove bold markdown
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    // Remove italic markdown (single asterisks)
    .replace(/\*([^*]+)\*/g, '$1')
    // Remove heading markdown
    .replace(/^##\s+/gm, '')
    .replace(/^#\s+/gm, '')
    // Reduce excessive newlines (3+ to 2)
    .replace(/\n\s*\n\s*\n+/g, '\n\n')
    // Trim whitespace
    .trim();
};

/**
 * Renders text content with proper formatting for lists and paragraphs
 */
export const renderFormattedText = (text: string, accentColor: string = '#646cff'): React.ReactNode => {
  if (!text || typeof text !== 'string') {
    return null;
  }

  let cleanedText = cleanMarkdownArtifacts(text);

  // If the content appears to be a JSON string, apply basic formatting to make it readable.
  if (cleanedText.trim().startsWith('{')) {
    cleanedText = cleanedText
      .replace(/[\{\}]/g, '') // Remove all curly braces
      .replace(/"([^"]+)":\s*("([^"]*)"|[\w\s.-]+)/g, (_match, key, value) => {
        const cleanValue = value.replace(/"/g, '').trim();
        const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());
        return `\n**${formattedKey}**\n- ${cleanValue}\n`;
      })
      .replace(/,/g, '') // Remove commas
      .trim();
  }
  
  const lines = cleanedText.split('\n').filter(line => line.trim());

  return (
    <div style={{ lineHeight: '1.7', color: '#333', fontSize: '0.95em' }}>
      {lines.map((line, index) => {
        const trimmedLine = line.trim();

        // Handle bolded keys from our JSON formatting
        if (trimmedLine.startsWith('**') && trimmedLine.endsWith('**')) {
          const content = trimmedLine.replace(/\*\*/g, '');
          return (
            <div key={index} style={{
              fontWeight: '600',
              color: accentColor,
              marginTop: '12px',
              marginBottom: '4px',
              fontSize: '0.9em'
            }}>
              {content}
            </div>
          );
        }

        // Handle values as bullet points
        if (trimmedLine.startsWith('-')) {
          const content = trimmedLine.substring(1).trim();
          return (
            <div key={index} style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              marginBottom: '10px',
              paddingLeft: '12px',
              borderLeft: `2px solid ${accentColor}20`,
            }}>
              <span style={{
                color: accentColor,
                fontWeight: 'bold',
                fontSize: '1.2em',
                lineHeight: '1.2',
                minWidth: '10px'
              }}>•</span>
              <span style={{ flex: 1, fontStyle: content ? 'normal' : 'italic', color: content ? '#555' : '#999' }}>
                {content || 'No information available'}
              </span>
            </div>
          );
        }

        // Regular paragraph
        return (
          <div key={index} style={{ marginBottom: '12px' }}>
            {trimmedLine}
          </div>
        );
      })}
    </div>
  );
};

/**
 * Main content renderer that handles JSON, markdown, and plain text
 */
export const renderComplexContent = (
  content: any,
  accentColor: string = '#646cff'
): React.ReactNode => {
  
  // Handle null/undefined
  if (content === null || content === undefined) {
    return <div style={{ color: '#999', fontStyle: 'italic' }}>No content available</div>;
  }

  // Handle non-string content (already an object)
  if (typeof content !== 'string') {
    if (typeof content === 'object') {
      return renderStructuredJson(content, accentColor);
    }
    return <div>{String(content)}</div>;
  }

  // Attempt to parse the content as JSON (handles markdown-wrapped and raw)
  const parsedJson = parseJsonContent(content);
  if (parsedJson) {
    return renderStructuredJson(parsedJson, accentColor);
  }

  // If it's not JSON, render it as formatted text (which handles other markdown)
  return renderFormattedText(content, accentColor);
};

// Named exports for specific use cases
export default renderComplexContent;