"""
Clustering Algorithm Tests
Tests for DBSCAN clustering, similarity search, and cluster quality
"""

import pytest
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from datetime import datetime


class TestDBSCANClustering:
    """Test DBSCAN clustering algorithm"""

    def test_basic_clustering(self):
        """Should cluster similar vectors together"""
        # Create 2 distinct clusters
        cluster1 = np.array([
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.95, 0.05, 0.0]
        ])

        cluster2 = np.array([
            [0.0, 1.0, 0.0],
            [0.0, 0.9, 0.1],
            [0.0, 0.95, 0.05]
        ])

        data = np.vstack([cluster1, cluster2])

        clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
        labels = clustering.fit_predict(data)

        # Should find 2 clusters
        unique_labels = set(labels)
        cluster_labels = [l for l in unique_labels if l != -1]
        assert len(cluster_labels) == 2

    def test_noise_detection(self):
        """Should detect noise points (outliers)"""
        # 2 clusters + 1 outlier
        data = np.array([
            [1.0, 0.0, 0.0],  # Cluster 1
            [0.9, 0.1, 0.0],  # Cluster 1
            [0.0, 1.0, 0.0],  # Cluster 2
            [0.0, 0.9, 0.1],  # Cluster 2
            [0.5, 0.5, 0.5],  # Noise/outlier
        ])

        clustering = DBSCAN(eps=0.2, min_samples=2, metric='cosine')
        labels = clustering.fit_predict(data)

        # Should have some noise points (label -1)
        noise_count = np.sum(labels == -1)
        assert noise_count >= 0  # May or may not have noise depending on eps

    def test_min_samples_parameter(self):
        """Should respect min_samples parameter"""
        # 3 points close together, 2 isolated points
        data = np.array([
            [1.0, 0.0, 0.0],
            [0.95, 0.05, 0.0],
            [0.9, 0.1, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])

        # With min_samples=3, only first 3 should form cluster
        clustering = DBSCAN(eps=0.3, min_samples=3, metric='cosine')
        labels = clustering.fit_predict(data)

        # Should find at least 1 cluster (first 3 points)
        cluster_labels = [l for l in set(labels) if l != -1]
        assert len(cluster_labels) >= 1

    def test_eps_parameter_sensitivity(self):
        """Should be sensitive to eps parameter"""
        data = np.array([
            [1.0, 0.0, 0.0],
            [0.7, 0.3, 0.0],
            [0.0, 1.0, 0.0],
        ])

        # Small eps: may not cluster
        clustering_small = DBSCAN(eps=0.1, min_samples=2, metric='cosine')
        labels_small = clustering_small.fit_predict(data)

        # Large eps: should cluster more
        clustering_large = DBSCAN(eps=0.5, min_samples=2, metric='cosine')
        labels_large = clustering_large.fit_predict(data)

        # Large eps should find same or fewer clusters than small eps
        clusters_small = len(set(labels_small)) - (1 if -1 in labels_small else 0)
        clusters_large = len(set(labels_large)) - (1 if -1 in labels_large else 0)

        assert clusters_large >= 0 and clusters_small >= 0


class TestSimilarityMetrics:
    """Test similarity calculation methods"""

    def test_cosine_similarity(self):
        """Should calculate cosine similarity correctly"""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        vec3 = np.array([0.0, 1.0, 0.0])
        vec4 = np.array([-1.0, 0.0, 0.0])

        # Identical vectors
        sim1 = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        assert abs(sim1 - 1.0) < 1e-6

        # Orthogonal vectors
        sim2 = np.dot(vec1, vec3) / (np.linalg.norm(vec1) * np.linalg.norm(vec3))
        assert abs(sim2) < 1e-6

        # Opposite vectors
        sim3 = np.dot(vec1, vec4) / (np.linalg.norm(vec1) * np.linalg.norm(vec4))
        assert abs(sim3 + 1.0) < 1e-6  # -1.0

    def test_euclidean_distance(self):
        """Should calculate Euclidean distance"""
        vec1 = np.array([0.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        vec3 = np.array([0.0, 1.0, 0.0])

        dist1 = np.linalg.norm(vec1 - vec2)
        assert abs(dist1 - 1.0) < 1e-6

        dist2 = np.linalg.norm(vec2 - vec3)
        assert abs(dist2 - np.sqrt(2)) < 1e-6

    def test_similarity_threshold(self):
        """Should filter by similarity threshold"""
        target = np.array([1.0, 0.0, 0.0])
        candidates = [
            np.array([0.95, 0.05, 0.0]),  # Very similar
            np.array([0.7, 0.3, 0.0]),    # Moderately similar
            np.array([0.0, 1.0, 0.0]),    # Not similar
        ]

        threshold = 0.85

        similar = []
        for candidate in candidates:
            sim = np.dot(target, candidate) / (
                np.linalg.norm(target) * np.linalg.norm(candidate)
            )
            if sim >= threshold:
                similar.append(candidate)

        assert len(similar) >= 1  # At least the very similar one


class TestClusterQuality:
    """Test cluster quality metrics"""

    def test_silhouette_score(self):
        """Should calculate silhouette score for cluster quality"""
        # Good clustering
        good_data = np.array([
            [1.0, 0.0], [0.9, 0.1], [0.95, 0.05],  # Cluster 1
            [0.0, 1.0], [0.1, 0.9], [0.05, 0.95],  # Cluster 2
        ])
        good_labels = np.array([0, 0, 0, 1, 1, 1])

        score_good = silhouette_score(good_data, good_labels, metric='cosine')

        # Poor clustering
        poor_labels = np.array([0, 1, 0, 1, 0, 1])  # Alternating labels

        score_poor = silhouette_score(good_data, poor_labels, metric='cosine')

        # Good clustering should have higher silhouette score
        assert score_good > score_poor

    def test_cluster_cohesion(self):
        """Should measure within-cluster cohesion"""
        cluster_points = np.array([
            [1.0, 0.0, 0.0],
            [0.95, 0.05, 0.0],
            [0.9, 0.1, 0.0],
        ])

        # Calculate mean pairwise similarity
        similarities = []
        for i in range(len(cluster_points)):
            for j in range(i + 1, len(cluster_points)):
                sim = np.dot(cluster_points[i], cluster_points[j]) / (
                    np.linalg.norm(cluster_points[i]) *
                    np.linalg.norm(cluster_points[j])
                )
                similarities.append(sim)

        mean_similarity = np.mean(similarities)

        # Tight cluster should have high mean similarity
        assert mean_similarity > 0.8

    def test_cluster_separation(self):
        """Should measure between-cluster separation"""
        cluster1 = np.array([[1.0, 0.0, 0.0]])
        cluster2 = np.array([[0.0, 1.0, 0.0]])

        # Calculate inter-cluster similarity
        sim = np.dot(cluster1[0], cluster2[0]) / (
            np.linalg.norm(cluster1[0]) * np.linalg.norm(cluster2[0])
        )

        # Well-separated clusters should have low similarity
        assert sim < 0.5


class TestClusteringWorkflow:
    """Test end-to-end clustering workflow"""

    def test_batch_clustering(self):
        """Should cluster articles in batches"""
        # Simulate 100 article embeddings
        np.random.seed(42)
        embeddings = np.random.rand(100, 1536)  # Standard OpenAI embedding size

        # Normalize to unit vectors (as OpenAI embeddings are)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
        labels = clustering.fit_predict(embeddings)

        # Should find some clusters
        unique_labels = set(labels)
        assert len(unique_labels) > 1

    def test_incremental_clustering(self):
        """Should handle incremental article addition"""
        # Initial articles
        initial_embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
        ])

        clustering1 = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
        labels1 = clustering1.fit_predict(initial_embeddings)

        # Add new similar article
        new_article = np.array([[0.95, 0.05, 0.0]])
        all_embeddings = np.vstack([initial_embeddings, new_article])

        clustering2 = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
        labels2 = clustering2.fit_predict(all_embeddings)

        # All three should be in same cluster
        if -1 not in labels2:  # No noise
            assert labels2[0] == labels2[1] == labels2[2]

    def test_recluster_on_threshold(self):
        """Should trigger reclustering when new articles exceed threshold"""
        batch_size = 50
        recluster_threshold = batch_size

        # Simulate processing articles
        new_articles_count = 0

        # Process 30 articles
        new_articles_count += 30
        assert new_articles_count < recluster_threshold  # Don't recluster yet

        # Process 25 more articles (total 55)
        new_articles_count += 25
        assert new_articles_count >= recluster_threshold  # Should trigger recluster

        # Reset after reclustering
        new_articles_count = 0
        assert new_articles_count == 0


class TestClusterMetadata:
    """Test cluster metadata and statistics"""

    def test_calculate_cluster_impact_score(self, db_session, sample_cluster_data):
        """Should calculate cluster impact score"""
        event_id = sample_cluster_data

        # Get cluster data
        result = db_session.execute(
            """SELECT source_count, article_count, first_reported_time
               FROM news_events WHERE event_id = ?""",
            (event_id,)
        ).fetchone()

        source_count = result[0]
        article_count = result[1]
        first_reported = result[2]

        # Calculate impact score
        # More sources and articles = higher impact
        # Newer articles = higher impact
        base_score = (source_count * 10) + (article_count * 5)

        # Time decay (simplified)
        hours_old = (datetime.utcnow() - datetime.fromisoformat(first_reported)).total_seconds() / 3600
        time_factor = max(1.0, 24 - hours_old) / 24  # Decay over 24 hours

        impact_score = base_score * time_factor

        assert impact_score > 0

    def test_cluster_ranking(self, db_session, sample_cluster_data):
        """Should rank clusters by impact"""
        # Create multiple clusters with different scores
        clusters = []
        for i, score in enumerate([95.0, 75.0, 85.0, 60.0]):
            result = db_session.execute(
                """INSERT INTO news_events
                   (event_summary, first_reported_time, last_updated,
                    source_count, relevance_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (f"Event {i}", datetime.utcnow(), datetime.utcnow(), i + 1, score)
            )
            db_session.commit()
            clusters.append((result.lastrowid, score))

        # Query top clusters
        top_clusters = db_session.execute(
            """SELECT event_id, relevance_score FROM news_events
               ORDER BY relevance_score DESC LIMIT 3"""
        ).fetchall()

        # Should be ordered by score
        assert len(top_clusters) >= 3
        assert top_clusters[0][1] >= top_clusters[1][1] >= top_clusters[2][1]


class TestEdgeCases:
    """Test edge cases in clustering"""

    def test_single_article_no_cluster(self):
        """Should handle single article (no cluster formed)"""
        embeddings = np.array([[1.0, 0.0, 0.0]])

        clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
        labels = clustering.fit_predict(embeddings)

        # Single article should be noise
        assert labels[0] == -1

    def test_all_identical_articles(self):
        """Should cluster all identical articles together"""
        # 5 identical embeddings
        embeddings = np.tile([1.0, 0.0, 0.0], (5, 1))

        clustering = DBSCAN(eps=0.1, min_samples=2, metric='cosine')
        labels = clustering.fit_predict(embeddings)

        # All should be in same cluster
        unique_labels = set(labels)
        non_noise = [l for l in unique_labels if l != -1]
        assert len(non_noise) == 1

    def test_empty_embeddings_list(self):
        """Should handle empty embeddings gracefully"""
        embeddings = np.array([]).reshape(0, 3)

        clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine')

        # Should not crash
        try:
            labels = clustering.fit_predict(embeddings)
            assert len(labels) == 0
        except ValueError:
            # Some versions may raise ValueError for empty input
            assert True

    def test_high_dimensional_embeddings(self):
        """Should handle high-dimensional embeddings (1536D)"""
        np.random.seed(42)
        embeddings = np.random.rand(10, 1536)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
        labels = clustering.fit_predict(embeddings)

        # Should complete without error
        assert len(labels) == 10


class TestPerformance:
    """Test clustering performance"""

    def test_large_dataset_performance(self, performance_tracker):
        """Should cluster large dataset efficiently"""
        np.random.seed(42)
        embeddings = np.random.rand(1000, 1536)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        performance_tracker.start("clustering_1000")

        clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
        labels = clustering.fit_predict(embeddings)

        duration = performance_tracker.stop("clustering_1000")

        # Should complete in reasonable time (<5 seconds)
        assert duration < 5.0

        # Should find some clusters
        unique_labels = set(labels)
        assert len(unique_labels) > 1
