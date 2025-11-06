"""
Unit and integration tests for review scheduler.

Tests decay-based mastery model, review priority computation,
and review outcome recording.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

from src.storage.db import Database, initialize_database
from src.models.base import Event, SkillState, TopicSummary
from src.scheduler.review import (
    ReviewItem,
    compute_decayed_mastery,
    compute_review_priority,
    get_next_reviews,
    record_review_outcome,
)


def create_test_database():
    """Create a test database with sample skills."""
    db_path = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path.close()
    db_path = Path(db_path.name)
    
    initialize_database(db_path)
    
    with Database(db_path) as db:
        # Create topic
        topic = TopicSummary(
            topic_id="calculus",
            summary="Introduction to calculus",
            parent_topic_id=None,
        )
        db.insert_topic_summary(topic)
        
        # Create skills with different mastery levels and recency
        now = datetime.utcnow()
        
        # Skill 1: High mastery, recent review (within grace period)
        skill1 = SkillState(
            skill_id="skill_high_recent",
            p_mastery=0.9,
            topic_id="calculus",
            last_evidence_at=now - timedelta(days=3),
            evidence_count=5,
        )
        db.insert_skill_state(skill1)
        
        # Skill 2: Medium mastery, old review (outside grace period)
        skill2 = SkillState(
            skill_id="skill_medium_old",
            p_mastery=0.5,
            topic_id="calculus",
            last_evidence_at=now - timedelta(days=20),
            evidence_count=3,
        )
        db.insert_skill_state(skill2)
        
        # Skill 3: Low mastery, very old review
        skill3 = SkillState(
            skill_id="skill_low_very_old",
            p_mastery=0.2,
            topic_id="calculus",
            last_evidence_at=now - timedelta(days=60),
            evidence_count=2,
        )
        db.insert_skill_state(skill3)
        
        # Skill 4: Medium mastery, no evidence yet
        skill4 = SkillState(
            skill_id="skill_no_evidence",
            p_mastery=0.5,
            topic_id="calculus",
            last_evidence_at=None,
            evidence_count=0,
        )
        db.insert_skill_state(skill4)
    
    return db_path


class TestDecayModel:
    """Tests for decay-based mastery model."""
    
    def test_no_decay_within_grace_period(self):
        """Test that mastery doesn't decay within grace period."""
        # 3 days since review, 7 day grace period
        decayed = compute_decayed_mastery(
            current_mastery=0.8,
            days_since_evidence=3.0,
            tau_days=30.0,
            grace_period_days=7.0,
        )
        
        assert decayed == 0.8  # No decay
    
    def test_no_decay_at_grace_period_boundary(self):
        """Test that mastery doesn't decay exactly at grace period."""
        # 7 days since review, 7 day grace period
        decayed = compute_decayed_mastery(
            current_mastery=0.8,
            days_since_evidence=7.0,
            tau_days=30.0,
            grace_period_days=7.0,
        )
        
        assert decayed == 0.8  # No decay
    
    def test_exponential_decay_after_grace_period(self):
        """Test exponential decay after grace period."""
        # 30 days since review (23 days after grace period)
        # tau = 30, effective days = 23, decay factor = e^(-23/30) ≈ 0.4647
        decayed = compute_decayed_mastery(
            current_mastery=0.8,
            days_since_evidence=30.0,
            tau_days=30.0,
            grace_period_days=7.0,
        )
        
        # Expected: 0.8 * e^(-23/30) ≈ 0.3718
        expected = 0.8 * 0.4647
        assert decayed == pytest.approx(expected, rel=1e-2)
    
    def test_decay_bounds(self):
        """Test that decayed mastery stays within bounds."""
        # Very old review (365 days)
        decayed = compute_decayed_mastery(
            current_mastery=0.5,
            days_since_evidence=365.0,
            tau_days=30.0,
            grace_period_days=7.0,
        )
        
        assert 0.0 <= decayed <= 1.0
        assert decayed < 0.5  # Should have decayed
    
    def test_zero_mastery_no_decay(self):
        """Test that zero mastery doesn't change with decay."""
        decayed = compute_decayed_mastery(
            current_mastery=0.0,
            days_since_evidence=100.0,
            tau_days=30.0,
            grace_period_days=7.0,
        )
        
        assert decayed == 0.0
    
    def test_one_mastery_decays(self):
        """Test that perfect mastery decays over time."""
        decayed = compute_decayed_mastery(
            current_mastery=1.0,
            days_since_evidence=30.0,
            tau_days=30.0,
            grace_period_days=7.0,
        )
        
        assert decayed < 1.0
        assert decayed > 0.0


class TestReviewPriority:
    """Tests for review priority computation."""
    
    def test_priority_higher_for_lower_mastery(self):
        """Test that lower mastery gets higher priority."""
        priority_low = compute_review_priority(0.2, 10.0)
        priority_high = compute_review_priority(0.8, 10.0)
        
        assert priority_low > priority_high
    
    def test_priority_higher_for_older_review(self):
        """Test that older reviews get higher priority."""
        priority_old = compute_review_priority(0.5, 60.0)
        priority_recent = compute_review_priority(0.5, 5.0)
        
        assert priority_old > priority_recent
    
    def test_priority_zero_mastery(self):
        """Test priority for zero mastery."""
        priority = compute_review_priority(0.0, 10.0)
        
        # Should be high priority (1.0 * (1 + 10/30) = 1.333...)
        assert priority == pytest.approx(1.333, rel=1e-3)
    
    def test_priority_one_mastery(self):
        """Test priority for perfect mastery."""
        priority = compute_review_priority(1.0, 10.0)
        
        # Should be low priority (0.0 * (1 + 10/30) = 0.0)
        assert priority == 0.0
    
    def test_priority_combined_factors(self):
        """Test that priority combines mastery and recency."""
        # Low mastery + old review = very high priority
        priority1 = compute_review_priority(0.2, 60.0)
        
        # High mastery + recent review = low priority
        priority2 = compute_review_priority(0.9, 5.0)
        
        assert priority1 > priority2


class TestGetNextReviews:
    """Tests for getting next reviews."""
    
    def test_get_all_reviews(self):
        """Test getting all reviews sorted by priority."""
        db_path = create_test_database()
        
        try:
            reviews = get_next_reviews(limit=10, db_path=db_path)
            
            assert len(reviews) > 0
            assert all(isinstance(r, ReviewItem) for r in reviews)
            
            # Should be sorted by priority (highest first)
            for i in range(len(reviews) - 1):
                assert reviews[i].priority_score >= reviews[i+1].priority_score
        
        finally:
            db_path.unlink()
    
    def test_get_reviews_with_limit(self):
        """Test limiting number of reviews."""
        db_path = create_test_database()
        
        try:
            reviews = get_next_reviews(limit=2, db_path=db_path)
            
            assert len(reviews) <= 2
        
        finally:
            db_path.unlink()
    
    def test_get_reviews_by_topic(self):
        """Test filtering reviews by topic."""
        db_path = create_test_database()
        
        try:
            reviews = get_next_reviews(limit=10, topic_id="calculus", db_path=db_path)
            
            assert len(reviews) > 0
            assert all(r.skill.topic_id == "calculus" for r in reviews)
        
        finally:
            db_path.unlink()
    
    def test_get_reviews_by_mastery_range(self):
        """Test filtering reviews by mastery range."""
        db_path = create_test_database()
        
        try:
            # Get skills with low mastery (0.0-0.3)
            reviews = get_next_reviews(
                limit=10,
                min_mastery=0.0,
                max_mastery=0.3,
                db_path=db_path,
            )
            
            assert len(reviews) > 0
            assert all(r.skill.p_mastery <= 0.3 for r in reviews)
        
        finally:
            db_path.unlink()
    
    def test_reviews_include_decay(self):
        """Test that reviews include decayed mastery."""
        db_path = create_test_database()
        
        try:
            reviews = get_next_reviews(limit=10, db_path=db_path)
            
            for review in reviews:
                # Decayed mastery should be <= current mastery
                assert review.decayed_mastery <= review.skill.p_mastery
                
                # For old reviews, decayed should be less
                if review.days_since_review > 7:
                    assert review.decayed_mastery < review.skill.p_mastery
    
        finally:
            db_path.unlink()
    
    def test_no_evidence_handled(self):
        """Test that skills with no evidence are handled correctly."""
        db_path = create_test_database()
        
        try:
            reviews = get_next_reviews(limit=10, db_path=db_path)
            
            # Skill with no evidence should have high days_since_review
            no_evidence_reviews = [
                r for r in reviews if r.skill.skill_id == "skill_no_evidence"
            ]
            
            if no_evidence_reviews:
                assert no_evidence_reviews[0].days_since_review > 100
    
        finally:
            db_path.unlink()


class TestRecordReviewOutcome:
    """Tests for recording review outcomes."""
    
    def test_record_mastered_outcome(self):
        """Test recording a mastered review outcome."""
        db_path = create_test_database()
        
        try:
            # Record outcome
            event = record_review_outcome(
                skill_id="skill_medium_old",
                mastered=True,
                review_content="Student demonstrated mastery of derivatives",
                db_path=db_path,
            )
            
            # Check event
            assert event.event_type == "assessment"
            assert event.actor == "student"
            assert "skill_medium_old" in event.skills
            assert event.metadata["review_outcome"] == "mastered"
            assert event.metadata["skill_id"] == "skill_medium_old"
            
            # Check skill state updated
            with Database(db_path) as db:
                skill = db.get_skill_state_by_id("skill_medium_old")
                assert skill is not None
                assert skill.p_mastery > 0.5  # Should have increased
                assert skill.evidence_count > 3  # Should have increased
                assert skill.last_evidence_at is not None
        
        finally:
            db_path.unlink()
    
    def test_record_not_mastered_outcome(self):
        """Test recording a not-mastered review outcome."""
        db_path = create_test_database()
        
        try:
            # Record outcome
            event = record_review_outcome(
                skill_id="skill_high_recent",
                mastered=False,
                review_content="Student struggled with concept",
                db_path=db_path,
            )
            
            # Check event
            assert event.event_type == "assessment"
            assert event.actor == "student"
            assert event.metadata["review_outcome"] == "not_mastered"
            
            # Check skill state updated
            with Database(db_path) as db:
                skill = db.get_skill_state_by_id("skill_high_recent")
                assert skill is not None
                assert skill.p_mastery < 0.9  # Should have decreased
                assert skill.evidence_count > 5  # Should have increased
        
        finally:
            db_path.unlink()
    
    def test_record_outcome_updates_metadata(self):
        """Test that review outcome includes mastery deltas."""
        db_path = create_test_database()
        
        try:
            # Get initial mastery
            with Database(db_path) as db:
                initial_skill = db.get_skill_state_by_id("skill_medium_old")
                initial_mastery = initial_skill.p_mastery
            
            # Record outcome
            event = record_review_outcome(
                skill_id="skill_medium_old",
                mastered=True,
                db_path=db_path,
            )
            
            # Check metadata includes before/after
            assert "p_mastery_before" in event.metadata
            assert "p_mastery_after" in event.metadata
            assert event.metadata["p_mastery_before"] == initial_mastery
            assert event.metadata["p_mastery_after"] > initial_mastery
        
        finally:
            db_path.unlink()
    
    def test_record_outcome_nonexistent_skill(self):
        """Test that recording outcome for nonexistent skill raises error."""
        db_path = create_test_database()
        
        try:
            with pytest.raises(ValueError, match="Skill not found"):
                record_review_outcome(
                    skill_id="nonexistent_skill",
                    mastered=True,
                    db_path=db_path,
                )
        
        finally:
            db_path.unlink()


class TestReviewItem:
    """Tests for ReviewItem class."""
    
    def test_review_item_creation(self):
        """Test creating a ReviewItem."""
        skill = SkillState(
            skill_id="test_skill",
            p_mastery=0.5,
            topic_id="test_topic",
        )
        
        item = ReviewItem(
            skill=skill,
            priority_score=1.5,
            days_since_review=10.0,
            decayed_mastery=0.4,
        )
        
        assert item.skill == skill
        assert item.priority_score == 1.5
        assert item.days_since_review == 10.0
        assert item.decayed_mastery == 0.4

