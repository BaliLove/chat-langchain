"""
Training Data Quality Report Generator

This script analyzes training data from Bubble.io and generates
a comprehensive quality report with actionable insights.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict

from dotenv import load_dotenv
from tabulate import tabulate

from backend.training_loader import load_enhanced_training_data

load_dotenv()


class TrainingDataAnalyzer:
    """Analyze training data quality and generate reports"""
    
    def __init__(self, documents: List[Any]):
        self.documents = documents
        self.analysis_results = {}
    
    def generate_full_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        
        print("Analyzing training data quality...")
        
        # Basic statistics
        self.analysis_results["basic_stats"] = self._analyze_basic_stats()
        
        # Content quality analysis
        self.analysis_results["content_quality"] = self._analyze_content_quality()
        
        # Metadata completeness
        self.analysis_results["metadata_completeness"] = self._analyze_metadata_completeness()
        
        # Content structure analysis
        self.analysis_results["content_structure"] = self._analyze_content_structure()
        
        # Topic analysis
        self.analysis_results["topic_analysis"] = self._analyze_topics()
        
        # Archive status
        self.analysis_results["archive_analysis"] = self._analyze_archive_status()
        
        # Training sessions analysis
        self.analysis_results["session_analysis"] = self._analyze_training_sessions()
        
        # Recommendations
        self.analysis_results["recommendations"] = self._generate_recommendations()
        
        return self.analysis_results
    
    def _analyze_basic_stats(self) -> Dict[str, Any]:
        """Analyze basic statistics"""
        total_docs = len(self.documents)
        
        if not total_docs:
            return {"total_documents": 0}
        
        # Word count statistics
        word_counts = [doc.metadata.get("word_count", 0) for doc in self.documents]
        
        # Reading time statistics
        reading_times = [doc.metadata.get("estimated_reading_time_minutes", 0) for doc in self.documents]
        
        return {
            "total_documents": total_docs,
            "word_count": {
                "total": sum(word_counts),
                "average": sum(word_counts) / total_docs,
                "min": min(word_counts),
                "max": max(word_counts),
                "distribution": {
                    "under_100": sum(1 for wc in word_counts if wc < 100),
                    "100_500": sum(1 for wc in word_counts if 100 <= wc < 500),
                    "500_1000": sum(1 for wc in word_counts if 500 <= wc < 1000),
                    "over_1000": sum(1 for wc in word_counts if wc >= 1000),
                }
            },
            "reading_time": {
                "average_minutes": sum(reading_times) / total_docs if total_docs else 0,
                "total_hours": sum(reading_times) / 60,
            }
        }
    
    def _analyze_content_quality(self) -> Dict[str, Any]:
        """Analyze content quality scores"""
        quality_scores = [doc.metadata.get("quality_score", 0) for doc in self.documents]
        
        # Collect all warnings
        all_warnings = []
        for doc in self.documents:
            warnings = doc.metadata.get("quality_warnings", [])
            all_warnings.extend(warnings)
        
        warning_counts = Counter(all_warnings)
        
        # Quality distribution
        quality_distribution = {
            "excellent": sum(1 for score in quality_scores if score >= 90),
            "good": sum(1 for score in quality_scores if 70 <= score < 90),
            "fair": sum(1 for score in quality_scores if 50 <= score < 70),
            "poor": sum(1 for score in quality_scores if score < 50),
        }
        
        return {
            "average_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "quality_distribution": quality_distribution,
            "common_warnings": dict(warning_counts.most_common(10)),
            "high_quality_percentage": (quality_distribution["excellent"] + quality_distribution["good"]) / len(self.documents) * 100 if self.documents else 0
        }
    
    def _analyze_metadata_completeness(self) -> Dict[str, Any]:
        """Analyze metadata field completeness"""
        field_completeness = defaultdict(int)
        important_fields = [
            "title", "qualifications", "responsibilities", "qualifiedToTrain",
            "training_order", "key_topics", "created_date", "modified_date"
        ]
        
        for doc in self.documents:
            for field in important_fields:
                value = doc.metadata.get(field)
                if value and (not isinstance(value, list) or len(value) > 0):
                    field_completeness[field] += 1
        
        completeness_percentages = {
            field: (count / len(self.documents) * 100) if self.documents else 0
            for field, count in field_completeness.items()
        }
        
        return {
            "field_completeness": completeness_percentages,
            "average_completeness": sum(completeness_percentages.values()) / len(completeness_percentages) if completeness_percentages else 0,
            "missing_critical_fields": {
                field: 100 - percentage 
                for field, percentage in completeness_percentages.items() 
                if percentage < 80 and field in ["title", "qualifications", "responsibilities"]
            }
        }
    
    def _analyze_content_structure(self) -> Dict[str, Any]:
        """Analyze content structure features"""
        structure_features = {
            "has_headers": 0,
            "has_lists": 0,
            "has_checklist": 0,
            "well_structured": 0  # Has multiple structure elements
        }
        
        for doc in self.documents:
            if doc.metadata.get("has_headers"):
                structure_features["has_headers"] += 1
            if doc.metadata.get("has_lists"):
                structure_features["has_lists"] += 1
            if doc.metadata.get("has_checklist"):
                structure_features["has_checklist"] += 1
            
            # Check if well-structured (has at least 2 structure elements)
            structure_count = sum([
                doc.metadata.get("has_headers", False),
                doc.metadata.get("has_lists", False),
                doc.metadata.get("has_checklist", False)
            ])
            if structure_count >= 2:
                structure_features["well_structured"] += 1
        
        return {
            "structure_percentages": {
                feature: (count / len(self.documents) * 100) if self.documents else 0
                for feature, count in structure_features.items()
            }
        }
    
    def _analyze_topics(self) -> Dict[str, Any]:
        """Analyze key topics across training materials"""
        all_topics = []
        topic_frequency = Counter()
        
        for doc in self.documents:
            topics = doc.metadata.get("key_topics", [])
            all_topics.extend(topics)
            topic_frequency.update(topics)
        
        return {
            "total_unique_topics": len(set(all_topics)),
            "top_topics": dict(topic_frequency.most_common(20)),
            "average_topics_per_doc": len(all_topics) / len(self.documents) if self.documents else 0
        }
    
    def _analyze_archive_status(self) -> Dict[str, Any]:
        """Analyze archive status of training materials"""
        archived_count = sum(1 for doc in self.documents if doc.metadata.get("is_archived", False))
        active_count = len(self.documents) - archived_count
        
        return {
            "active_trainings": active_count,
            "archived_trainings": archived_count,
            "archive_percentage": (archived_count / len(self.documents) * 100) if self.documents else 0
        }
    
    def _analyze_training_sessions(self) -> Dict[str, Any]:
        """Analyze training sessions data"""
        has_sessions = sum(1 for doc in self.documents if doc.metadata.get("has_sessions", False))
        total_sessions = sum(doc.metadata.get("session_count", 0) for doc in self.documents)
        
        session_distribution = Counter()
        for doc in self.documents:
            count = doc.metadata.get("session_count", 0)
            if count == 0:
                session_distribution["no_sessions"] += 1
            elif count == 1:
                session_distribution["one_session"] += 1
            elif count <= 5:
                session_distribution["2_5_sessions"] += 1
            else:
                session_distribution["over_5_sessions"] += 1
        
        return {
            "trainings_with_sessions": has_sessions,
            "total_sessions": total_sessions,
            "average_sessions_per_training": total_sessions / len(self.documents) if self.documents else 0,
            "session_distribution": dict(session_distribution)
        }
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Content quality recommendations
        quality_data = self.analysis_results.get("content_quality", {})
        if quality_data.get("average_quality_score", 0) < 70:
            recommendations.append({
                "priority": "HIGH",
                "category": "Content Quality",
                "issue": "Low average quality score",
                "recommendation": "Review and enhance training content, especially documents with quality scores below 70"
            })
        
        # Content length recommendations
        basic_stats = self.analysis_results.get("basic_stats", {})
        word_dist = basic_stats.get("word_count", {}).get("distribution", {})
        if word_dist.get("under_100", 0) > len(self.documents) * 0.2:
            recommendations.append({
                "priority": "HIGH",
                "category": "Content Length",
                "issue": "Many documents have insufficient content",
                "recommendation": "Expand content for training materials with less than 100 words"
            })
        
        # Metadata recommendations
        metadata_data = self.analysis_results.get("metadata_completeness", {})
        missing_fields = metadata_data.get("missing_critical_fields", {})
        for field, missing_pct in missing_fields.items():
            if missing_pct > 20:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Metadata",
                    "issue": f"{field} field missing in {missing_pct:.0f}% of documents",
                    "recommendation": f"Add {field} information to training materials"
                })
        
        # Structure recommendations
        structure_data = self.analysis_results.get("content_structure", {})
        structure_pcts = structure_data.get("structure_percentages", {})
        if structure_pcts.get("well_structured", 0) < 50:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Content Structure",
                "issue": "Most training materials lack good structure",
                "recommendation": "Add headers, lists, and checklists to improve content organization"
            })
        
        # Archive recommendations
        archive_data = self.analysis_results.get("archive_analysis", {})
        if archive_data.get("archive_percentage", 0) > 50:
            recommendations.append({
                "priority": "LOW",
                "category": "Content Management",
                "issue": "High percentage of archived training materials",
                "recommendation": "Review archived content and consider updating or removing outdated materials"
            })
        
        # Session recommendations
        session_data = self.analysis_results.get("session_analysis", {})
        if session_data.get("trainings_with_sessions", 0) < len(self.documents) * 0.3:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Training Sessions",
                "issue": "Few training materials have associated sessions",
                "recommendation": "Schedule training sessions for materials without sessions"
            })
        
        return sorted(recommendations, key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x["priority"], 3))


def print_quality_report(analysis_results: Dict[str, Any]):
    """Print formatted quality report"""
    print("\n" + "="*80)
    print("TRAINING DATA QUALITY REPORT")
    print("Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*80)
    
    # Basic Statistics
    basic_stats = analysis_results.get("basic_stats", {})
    print("\n## BASIC STATISTICS")
    print(f"Total Training Documents: {basic_stats.get('total_documents', 0)}")
    
    if basic_stats.get("total_documents", 0) > 0:
        word_stats = basic_stats.get("word_count", {})
        print(f"\nWord Count Statistics:")
        print(f"  - Total Words: {word_stats.get('total', 0):,}")
        print(f"  - Average per Document: {word_stats.get('average', 0):.0f}")
        print(f"  - Range: {word_stats.get('min', 0)} - {word_stats.get('max', 0)}")
        
        print(f"\nContent Length Distribution:")
        dist = word_stats.get("distribution", {})
        for range_name, count in dist.items():
            print(f"  - {range_name.replace('_', '-')}: {count} documents")
        
        reading = basic_stats.get("reading_time", {})
        print(f"\nEstimated Reading Time:")
        print(f"  - Average: {reading.get('average_minutes', 0):.1f} minutes per document")
        print(f"  - Total: {reading.get('total_hours', 0):.1f} hours for all content")
    
    # Content Quality
    quality_data = analysis_results.get("content_quality", {})
    print("\n## CONTENT QUALITY ANALYSIS")
    print(f"Average Quality Score: {quality_data.get('average_quality_score', 0):.1f}/100")
    print(f"High Quality Documents: {quality_data.get('high_quality_percentage', 0):.1f}%")
    
    print("\nQuality Distribution:")
    dist = quality_data.get("quality_distribution", {})
    for level, count in dist.items():
        print(f"  - {level.capitalize()}: {count} documents")
    
    warnings = quality_data.get("common_warnings", {})
    if warnings:
        print("\nCommon Quality Warnings:")
        for warning, count in list(warnings.items())[:5]:
            print(f"  - {warning}: {count} occurrences")
    
    # Metadata Completeness
    metadata_data = analysis_results.get("metadata_completeness", {})
    print("\n## METADATA COMPLETENESS")
    print(f"Average Field Completeness: {metadata_data.get('average_completeness', 0):.1f}%")
    
    missing = metadata_data.get("missing_critical_fields", {})
    if missing:
        print("\nCritical Fields with Missing Data:")
        for field, pct in missing.items():
            print(f"  - {field}: {pct:.0f}% missing")
    
    # Content Structure
    structure_data = analysis_results.get("content_structure", {})
    print("\n## CONTENT STRUCTURE")
    structure_pcts = structure_data.get("structure_percentages", {})
    print("Structure Features Usage:")
    for feature, pct in structure_pcts.items():
        feature_name = feature.replace("_", " ").title()
        print(f"  - {feature_name}: {pct:.1f}% of documents")
    
    # Topics
    topic_data = analysis_results.get("topic_analysis", {})
    print("\n## TOPIC ANALYSIS")
    print(f"Total Unique Topics: {topic_data.get('total_unique_topics', 0)}")
    print(f"Average Topics per Document: {topic_data.get('average_topics_per_doc', 0):.1f}")
    
    top_topics = topic_data.get("top_topics", {})
    if top_topics:
        print("\nMost Common Topics:")
        for i, (topic, count) in enumerate(list(top_topics.items())[:10], 1):
            print(f"  {i}. {topic} ({count} occurrences)")
    
    # Archive Status
    archive_data = analysis_results.get("archive_analysis", {})
    print("\n## ARCHIVE STATUS")
    print(f"Active Trainings: {archive_data.get('active_trainings', 0)}")
    print(f"Archived Trainings: {archive_data.get('archived_trainings', 0)} ({archive_data.get('archive_percentage', 0):.1f}%)")
    
    # Training Sessions
    session_data = analysis_results.get("session_analysis", {})
    print("\n## TRAINING SESSIONS")
    print(f"Trainings with Sessions: {session_data.get('trainings_with_sessions', 0)}")
    print(f"Total Sessions: {session_data.get('total_sessions', 0)}")
    print(f"Average Sessions per Training: {session_data.get('average_sessions_per_training', 0):.1f}")
    
    # Recommendations
    recommendations = analysis_results.get("recommendations", [])
    if recommendations:
        print("\n## RECOMMENDATIONS")
        
        # Group by priority
        by_priority = defaultdict(list)
        for rec in recommendations:
            by_priority[rec["priority"]].append(rec)
        
        for priority in ["HIGH", "MEDIUM", "LOW"]:
            if priority in by_priority:
                print(f"\n{priority} Priority:")
                for rec in by_priority[priority]:
                    print(f"\n  [{rec['category']}]")
                    print(f"  Issue: {rec['issue']}")
                    print(f"  Action: {rec['recommendation']}")
    
    print("\n" + "="*80)
    print("END OF REPORT")
    print("="*80)


def save_report_to_file(analysis_results: Dict[str, Any], filename: str = None):
    """Save the report to a JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_quality_report_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    print(f"\nReport saved to: {filename}")


def main():
    """Main function to generate training data quality report"""
    print("Loading training data...")
    
    # Load training documents
    documents = load_enhanced_training_data()
    
    if not documents:
        print("No training documents found!")
        return
    
    print(f"Loaded {len(documents)} training documents")
    
    # Analyze data
    analyzer = TrainingDataAnalyzer(documents)
    analysis_results = analyzer.generate_full_report()
    
    # Print report
    print_quality_report(analysis_results)
    
    # Save to file
    save_report_to_file(analysis_results)


if __name__ == "__main__":
    main()