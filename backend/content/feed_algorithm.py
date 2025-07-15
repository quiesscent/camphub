"""
This module contains the core logic for the personalized content feed algorithm.
It uses a combination of content-based filtering (TF-IDF for text), collaborative
filtering (user interaction history), and a scoring model to rank posts.
The algorithm is designed to be adaptable, with a simple scoring system for
new users or small datasets, and a more advanced ML-driven approach as the
dataset grows.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from django.utils import timezone
from datetime import timedelta
import random

from .models import Post, UserInteraction
from users.models import UserProfile

class FeedAlgorithm:
    """
    Handles the logic for ranking and personalizing the user's content feed.
    """
    def __init__(self, user):
        self.user = user
        self.user_profile, _ = UserProfile.objects.get_or_create(user=self.user)
        # Initialize vectorizer and scaler
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        self.scaler = MinMaxScaler()

    def get_post_features(self, posts):
        """
        Extracts and scales numerical features from a list of posts.
        Features include text content (TF-IDF), recency, author influence, and engagement.
        """
        if not posts:
            return np.array([])

        # 1. Text Features (TF-IDF)
        post_contents = [post.content for post in posts]
        tfidf_matrix = self.vectorizer.fit_transform(post_contents)

        # 2. Temporal Features (Recency)
        now = timezone.now()
        recency = np.array([(now - post.created_at).total_seconds() for post in posts]).reshape(-1, 1)
        # Log-transform to handle outliers, then scale. Newer posts get higher scores (1 - scaled).
        scaled_recency = 1 - self.scaler.fit_transform(np.log1p(recency))

        # 3. Engagement Features
        likes = np.array([post.likes.count() for post in posts]).reshape(-1, 1)
        comments = np.array([post.comments.count() for post in posts]).reshape(-1, 1)
        shares = np.array([post.shares.count() for post in posts]).reshape(-1, 1)
        
        scaled_likes = self.scaler.fit_transform(likes)
        scaled_comments = self.scaler.fit_transform(comments)
        scaled_shares = self.scaler.fit_transform(shares)

        # 4. Author Influence (Placeholder)
        # This could be based on followers, avg engagement, etc.
        # For now, a simple placeholder.
        author_influence = np.zeros((len(posts), 1)) # Placeholder

        # Combine all features into a single matrix
        features = np.hstack([
            tfidf_matrix.toarray(),
            scaled_recency,
            scaled_likes,
            scaled_comments,
            scaled_shares,
            author_influence
        ])
        
        return features

    def get_user_interest_vector(self):
        """
        Generates a user interest vector based on their interaction history.
        This vector represents the user's preferences in the same TF-IDF feature space as the posts.
        """
        # Fetch recent, meaningful interactions
        interactions = UserInteraction.objects.filter(
            user=self.user,
            interaction_type__in=['like', 'comment', 'share', 'view']
        ).select_related('post').order_by('-timestamp')[:100]

        if not interactions:
            # For new users, return a generic vector (or could be based on onboarding interests)
            return np.zeros(self.vectorizer.max_features)

        # Weight interactions to give more importance to active engagement
        interaction_weights = {'view': 0.2, 'like': 1.0, 'comment': 1.5, 'share': 2.0}
        
        post_contents = []
        weights = []
        for interaction in interactions:
            if interaction.post and interaction.post.content:
                post_contents.append(interaction.post.content)
                weights.append(interaction_weights.get(interaction.interaction_type, 0.1))

        if not post_contents:
            return np.zeros(self.vectorizer.max_features)

        # Fit the vectorizer on the user's interacted content to create TF-IDF vectors
        tfidf_matrix = self.vectorizer.fit_transform(post_contents)
        
        # Calculate the weighted average of these vectors to create the user's interest profile
        user_vector = np.dot(np.array(weights), tfidf_matrix.toarray()) / sum(weights)
        
        return user_vector

    def calculate_relevance_scores(self, posts):
        """
        Calculates a relevance score for each post based on the user's interest vector.
        This is the core of the content-based filtering.
        """
        if not posts:
            return []
            
        post_contents = [post.content for post in posts]
        post_vectors = self.vectorizer.fit_transform(post_contents)
        
        user_vector = self.get_user_interest_vector().reshape(1, -1)
        
        # Compute cosine similarity between the user's interest and each post
        relevance_scores = cosine_similarity(post_vectors, user_vector).flatten()
        
        return relevance_scores

    def simple_scoring(self, posts):
        """
        A simple, non-ML scoring system for smaller datasets or new users.
        It ranks posts based on a weighted sum of recency and engagement.
        """
        scores = {}
        now = timezone.now()
        for post in posts:
            # Recency score (decays over 7 days)
            age_in_hours = (now - post.created_at).total_seconds() / 3600
            recency_score = max(0, 1 - (age_in_hours / (24 * 7)))
            
            # Engagement score
            engagement_score = (
                post.likes.count() * 0.4 +
                post.comments.count() * 0.3 +
                post.shares.count() * 0.3
            )
            
            # Final score is a combination of recency and engagement
            scores[post.id] = (0.6 * recency_score) + (0.4 * engagement_score)
            
        return scores

    def diversify_feed(self, ranked_posts, diversity_level=0.3):
        """
        Re-ranks the feed to introduce diversity and prevent filter bubbles.
        It penalizes showing too many posts from the same author or with the same tags in a row.
        """
        if not ranked_posts:
            return []

        final_feed = []
        author_counts = {}
        tag_counts = {}
        
        # Convert QuerySet to list to allow removal
        ranked_posts = list(ranked_posts)

        while ranked_posts:
            best_post = None
            max_score = -1

            for post in ranked_posts:
                # Get the original score from the post object (set in rank_feed)
                score = post.score 
                
                # Apply penalties
                author_penalty = author_counts.get(post.author_id, 0) * 0.2
                
                # Calculate tag penalty
                tag_penalty = 0
                if post.tags:
                    tag_penalty = sum(tag_counts.get(tag, 0) for tag in post.tags) * 0.1
                
                diversified_score = score * (1 - author_penalty) * (1 - tag_penalty)

                if diversified_score > max_score:
                    max_score = diversified_score
                    best_post = post
            
            if best_post:
                final_feed.append(best_post)
                ranked_posts.remove(best_post)

                # Update counts to apply penalties for subsequent selections
                author_counts[best_post.author_id] = author_counts.get(best_post.author_id, 0) + 1
                if best_post.tags:
                    for tag in best_post.tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            else:
                # Break if no post can be selected
                break
                
        return final_feed


    def rank_feed(self, posts_queryset, use_ml=True):
        """
        Main method to rank the feed.
        It decides whether to use the simple or ML-based approach.
        """
        posts = list(posts_queryset)
        if not posts:
            return []

        # Heuristic to decide when to switch to ML-based ranking
        # Requires a minimum number of posts and user interactions
        min_interactions = 20
        min_posts_for_ml = 50
        user_interaction_count = UserInteraction.objects.filter(user=self.user).count()

        if use_ml and len(posts) >= min_posts_for_ml and user_interaction_count >= min_interactions:
            # Advanced ML-based scoring
            relevance_scores = self.calculate_relevance_scores(posts)
            
            # For now, we'll just use relevance. A true ML model would be trained here.
            # e.g., model.predict(post_features)
            # Let's combine relevance with simple scores for a hybrid approach
            simple_scores = self.simple_scoring(posts)

            for i, post in enumerate(posts):
                relevance_weight = 0.7
                simple_score_weight = 0.3
                post.score = (relevance_weight * relevance_scores[i]) + (simple_score_weight * simple_scores.get(post.id, 0))
        else:
            # Simple scoring for new users or small datasets
            scores = self.simple_scoring(posts)
            for post in posts:
                post.score = scores.get(post.id, 0)

        # Sort posts by the calculated score in descending order
        ranked_posts = sorted(posts, key=lambda p: p.score, reverse=True)
        
        # Apply diversification to the ranked list
        diversified_feed = self.diversify_feed(ranked_posts)

        return diversified_feed
