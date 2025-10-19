/**
 * API Configuration Utility
 * 
 * This utility determines the correct API base URL based on the environment.
 * It supports:
 * 1. Environment variables (for build-time configuration)
 * 2. Dynamic detection for Cloud Run deployments
 * 3. Local development fallback
 */

export const getApiBaseUrl = (): string => {
  // Check for environment variable first (for build-time configuration)
  const envApiUrl = (import.meta as any).env?.VITE_API_BASE_URL;
  if (envApiUrl && envApiUrl !== 'undefined') {
    return envApiUrl;
  }

  // If we're running on Cloud Run, try to construct API URL dynamically
  if (window.location.hostname.includes('run.app')) {
    // Extract service name pattern: mergemind-ui-{project}-{region}.run.app
    // Convert to API URL: mergemind-api-{project}-{region}.run.app
    const hostname = window.location.hostname;
    const apiHostname = hostname.replace('mergemind-ui-', 'mergemind-api-');
    return `https://${apiHostname}/api/v1`;
  }

  // Handle custom domain (mergemind.co.uk → api.mergemind.co.uk)
  if (window.location.hostname === 'mergemind.co.uk' || window.location.hostname === 'www.mergemind.co.uk') {
    return 'https://api.mergemind.co.uk/api/v1';
  }

  // Fallback to same-origin /api for local development
  return `${window.location.origin}/api/v1`;
};

// Export the configured API base URL
export const API_BASE_URL = getApiBaseUrl();
