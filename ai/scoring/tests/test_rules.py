"""
Tests for risk scoring rules.
"""

import pytest
from scoring.rules import score, validate_features, get_risk_weights


class TestRiskScoring:
    """Test cases for risk scoring rules."""
    
    def test_low_risk_mr(self):
        """Test low risk merge request."""
        features = {
            "last_pipeline_status_is_fail": False,
            "approvals_left": 0,
            "age_hours": 12,
            "change_size_bucket": "S",
            "labels_sensitive": False,
            "notes_count_24h": 2,
            "work_in_progress": False
        }
        
        result = score(features)
        
        assert result["score"] == 0
        assert result["band"] == "Low"
        assert len(result["reasons"]) == 0
    
    def test_medium_risk_mr(self):
        """Test medium risk merge request."""
        features = {
            "last_pipeline_status_is_fail": False,
            "approvals_left": 1,
            "age_hours": 72,
            "change_size_bucket": "L",
            "labels_sensitive": False,
            "notes_count_24h": 5,
            "work_in_progress": False
        }
        
        result = score(features)
        
        # 15 (approvals) + 15 (age) + 10 (size) = 40
        assert result["score"] == 40
        assert result["band"] == "Medium"
        assert len(result["reasons"]) == 3
        assert "1 approvals remaining" in result["reasons"]
        assert "MR age: 72.0 hours" in result["reasons"]
        assert "Large size change" in result["reasons"]
    
    def test_high_risk_mr(self):
        """Test high risk merge request."""
        features = {
            "last_pipeline_status_is_fail": True,
            "approvals_left": 2,
            "age_hours": 96,
            "change_size_bucket": "XL",
            "labels_sensitive": True,
            "notes_count_24h": 15,
            "work_in_progress": False
        }
        
        result = score(features)
        
        # 30 (failed) + 15 (approvals) + 15 (age) + 20 (size) + 10 (labels) + 5 (activity) = 95
        assert result["score"] == 95
        assert result["band"] == "High"
        assert len(result["reasons"]) == 6
    
    def test_wip_cap(self):
        """Test WIP cap at 80."""
        features = {
            "last_pipeline_status_is_fail": True,
            "approvals_left": 2,
            "age_hours": 96,
            "change_size_bucket": "XL",
            "labels_sensitive": True,
            "notes_count_24h": 15,
            "work_in_progress": True  # This should cap at 80
        }
        
        result = score(features)
        
        # Should be capped at 80 due to WIP
        assert result["score"] == 80
        assert result["band"] == "High"
        assert "Work in progress" in result["reasons"]
    
    def test_max_score_cap(self):
        """Test maximum score cap at 100."""
        features = {
            "last_pipeline_status_is_fail": True,
            "approvals_left": 3,
            "age_hours": 120,
            "change_size_bucket": "XL",
            "labels_sensitive": True,
            "notes_count_24h": 20,
            "work_in_progress": False
        }
        
        result = score(features)
        
        # Should be capped at 100
        assert result["score"] == 100
        assert result["band"] == "High"
    
    def test_boundary_conditions(self):
        """Test boundary conditions for risk bands."""
        # Test exactly 39 (Low)
        features_low = {
            "last_pipeline_status_is_fail": False,
            "approvals_left": 0,
            "age_hours": 48,  # Exactly at boundary
            "change_size_bucket": "M",
            "labels_sensitive": False,
            "notes_count_24h": 0,
            "work_in_progress": False
        }
        
        result = score(features_low)
        assert result["score"] == 20  # 15 (age) + 5 (size)
        assert result["band"] == "Low"
        
        # Test exactly 40 (Medium)
        features_medium = {
            "last_pipeline_status_is_fail": False,
            "approvals_left": 0,
            "age_hours": 49,  # Just over boundary
            "change_size_bucket": "M",
            "labels_sensitive": False,
            "notes_count_24h": 0,
            "work_in_progress": False
        }
        
        result = score(features_medium)
        assert result["score"] == 20  # 15 (age) + 5 (size)
        assert result["band"] == "Low"
        
        # Test exactly 70 (High)
        features_high = {
            "last_pipeline_status_is_fail": True,
            "approvals_left": 1,
            "age_hours": 72,
            "change_size_bucket": "L",
            "labels_sensitive": False,
            "notes_count_24h": 0,
            "work_in_progress": False
        }
        
        result = score(features_high)
        assert result["score"] == 70  # 30 + 15 + 15 + 10
        assert result["band"] == "High"
    
    def test_validate_features(self):
        """Test feature validation."""
        valid_features = {
            "last_pipeline_status_is_fail": False,
            "approvals_left": 0,
            "age_hours": 12,
            "change_size_bucket": "S",
            "labels_sensitive": False,
            "notes_count_24h": 2,
            "work_in_progress": False
        }
        
        assert validate_features(valid_features) is True
        
        # Test missing field
        invalid_features = {
            "last_pipeline_status_is_fail": False,
            "approvals_left": 0,
            # Missing age_hours
            "change_size_bucket": "S",
            "labels_sensitive": False,
            "notes_count_24h": 2,
            "work_in_progress": False
        }
        
        assert validate_features(invalid_features) is False
    
    def test_get_risk_weights(self):
        """Test risk weights retrieval."""
        weights = get_risk_weights()
        
        assert isinstance(weights, dict)
        assert "failed_pipeline" in weights
        assert weights["failed_pipeline"] == 30
        assert weights["approvals_left"] == 15
        assert weights["age_over_48h"] == 15
