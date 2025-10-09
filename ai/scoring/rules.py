"""
Risk scoring rules for merge requests.
Implements deterministic scoring based on SRS weights.
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def score(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate risk score based on merge request features.
    
    Args:
        features: Dictionary containing MR features
        
    Returns:
        Dictionary with score, band, and reasons
        
    Scoring rules:
    - failed pipeline: +30
    - approvals_left > 0: +15
    - age_hours > 48: +15
    - size bucket: M:+5, L:+10, XL:+20
    - labels_sensitive: +10
    - notes_count_24h > 10: +5
    - WIP in title: +10 and cap 80
    - cap final at 100; bands: Low 0–39, Medium 40–69, High 70–100
    """
    score_value = 0
    reasons = []
    
    # Failed pipeline check
    if features.get("last_pipeline_status_is_fail", False):
        score_value += 30
        reasons.append("Pipeline failed")
    
    # Approvals left check
    approvals_left = features.get("approvals_left", 0)
    if approvals_left > 0:
        score_value += 15
        reasons.append(f"{approvals_left} approvals remaining")
    
    # Age check
    age_hours = features.get("age_hours", 0)
    if age_hours > 48:
        score_value += 15
        reasons.append(f"MR age: {age_hours:.1f} hours")
    
    # Size bucket check
    change_size_bucket = features.get("change_size_bucket", "S")
    if change_size_bucket == "M":
        score_value += 5
        reasons.append("Medium size change")
    elif change_size_bucket == "L":
        score_value += 10
        reasons.append("Large size change")
    elif change_size_bucket == "XL":
        score_value += 20
        reasons.append("Extra large size change")
    
    # Sensitive labels check
    if features.get("labels_sensitive", False):
        score_value += 10
        reasons.append("Sensitive labels detected")
    
    # Recent activity check
    notes_count_24h = features.get("notes_count_24h", 0)
    if notes_count_24h > 10:
        score_value += 5
        reasons.append(f"High activity: {notes_count_24h} notes in 24h")
    
    # WIP check (with cap)
    if features.get("work_in_progress", False):
        score_value += 10
        reasons.append("Work in progress")
        # Cap at 80 if WIP
        if score_value > 80:
            score_value = 80
    
    # Final cap at 100
    if score_value > 100:
        score_value = 100
    
    # Determine risk band
    if score_value <= 39:
        band = "Low"
    elif score_value <= 69:
        band = "Medium"
    else:
        band = "High"
    
    result = {
        "score": score_value,
        "band": band,
        "reasons": reasons
    }
    
    logger.debug(f"Risk scoring result: {result}")
    return result


def get_risk_weights() -> Dict[str, int]:
    """
    Get the risk scoring weights for reference.
    
    Returns:
        Dictionary of risk factors and their weights
    """
    return {
        "failed_pipeline": 30,
        "approvals_left": 15,
        "age_over_48h": 15,
        "size_medium": 5,
        "size_large": 10,
        "size_xl": 20,
        "sensitive_labels": 10,
        "high_activity": 5,
        "work_in_progress": 10
    }


def validate_features(features: Dict[str, Any]) -> bool:
    """
    Validate that required features are present.
    
    Args:
        features: Dictionary containing MR features
        
    Returns:
        True if features are valid, False otherwise
    """
    required_fields = [
        "last_pipeline_status_is_fail",
        "approvals_left",
        "age_hours",
        "change_size_bucket",
        "labels_sensitive",
        "notes_count_24h",
        "work_in_progress"
    ]
    
    for field in required_fields:
        if field not in features:
            logger.warning(f"Missing required feature: {field}")
            return False
    
    return True
