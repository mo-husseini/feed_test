from collections import Counter
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/xrpc/app.bsky.feed.getFeedSkeleton', methods=['GET'])
def get_feed_skeleton():
    """Handle the Bluesky `getFeedSkeleton` request."""
    feed = [
        {"post": "at://did:example:alice/post/1"},
        {"post": "at://did:example:alice/post/2"},
        {"post": "at://did:example:bob/post/3"},
    ]
    # Respond with the feed
    return jsonify({"feed": feed})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

def generate_feed(posts, user_follows, interaction_history, trending_hashtags, format_preferences):
    """
    Generate a custom feed that factors in engagement, hashtags, interaction frequency, recency, diversity, virality, and content preferences.

    Args:
    - posts (list): List of dictionaries containing post data (author, likes, reposts, comments, quotes, hashtags, content_format, engaged_by_followers, timestamp).
    - user_follows (set): Set of users the feed owner follows.
    - interaction_history (dict): Interaction frequency with specific authors {'author': count}.
    - trending_hashtags (set): Set of hashtags currently trending.
    - format_preferences (dict): Preferences for content formats {'text': 1, 'image': 2, 'video': 3, etc.}.

    Returns:
    - list: A sorted list of posts for the feed.
    """

    def engagement_score(post):
        """Calculate engagement score based on likes, reposts, comments, and quotes."""
        return (
            post['likes'] * 1.8 +         # Likes are lightweight engagements.
            post['reposts'] * 1.4 +       # Reposts spread content virally.
            post['comments'] * 3 +        # Comments drive active discussion.
            post['quotes'] * 4.5          # Quotes represent high-effort engagement.
        )

    def virality_bonus(post):
        """Add a boost if multiple followers engage with the post."""
        return post.get('engaged_by_followers', 0) * 2  # Higher engagement from your network = higher score.

    def hashtag_bonus(post):
        """Calculate bonus points for using trending hashtags."""
        post_hashtags = set(post['hashtags'])
        matching_hashtags = post_hashtags & trending_hashtags
        return len(matching_hashtags) * 3  # Lowered hashtag boost to avoid dominance.

    def interaction_bonus(post):
        """Add bonus points for frequent interactions with the author."""
        return interaction_history.get(post['author'], 0) * 2  # Strong boost for users you engage with.

    def content_format_bonus(post):
        """Boost posts based on preferred content formats."""
        format_weight = format_preferences.get(post['content_format'], 1)
        return format_weight * 2  # Amplify preferred formats.

    def time_decay(post):
        """Apply a time-decay factor to prioritize recent posts."""
        current_time = time.time()
        hours_since_post = (current_time - post['timestamp']) / 3600
        return 1 / (1 + hours_since_post ** 1.2)  # Slightly faster decay to mimic Twitter's freshness focus.

    def diversity_penalty(post, author_frequency):
        """
        Penalize authors who appear too frequently to encourage feed diversity.
        This is a very light penalty: 2% per additional post.
        """
        penalty_factor = 1 - (author_frequency.get(post['author'], 0) * 0.02)
        return max(penalty_factor, 0.9)  # Ensure penalty is minimal but meaningful.

    # Count author appearances
    author_frequency = Counter(post['author'] for post in posts)

    # Filter posts to include only those by followed users
    relevant_posts = [post for post in posts if post['author'] in user_follows]

    # Rank posts with weighted scoring
    for post in relevant_posts:
        post['final_score'] = (
            (engagement_score(post)
            + virality_bonus(post)
            + hashtag_bonus(post)
            + interaction_bonus(post)
            + content_format_bonus(post))
            * time_decay(post)
            * diversity_penalty(post, author_frequency)
        )

    # Sort posts by final score
    return sorted(relevant_posts, key=lambda x: x['final_score'], reverse=True)


# Example usage
posts = [
    {'author': 'user1', 'likes': 10, 'reposts': 5, 'comments': 2, 'quotes': 3, 'hashtags': ['#AI', '#Bluesky'], 'content_format': 'text', 'engaged_by_followers': 2, 'timestamp': time.time() - 7200},
    {'author': 'user1', 'likes': 5, 'reposts': 2, 'comments': 1, 'quotes': 0, 'hashtags': ['#Design'], 'content_format': 'image', 'engaged_by_followers': 1, 'timestamp': time.time() - 3600},
    {'author': 'user2', 'likes': 20, 'reposts': 3, 'comments': 10, 'quotes': 1, 'hashtags': ['#Tech', '#AI'], 'content_format': 'video', 'engaged_by_followers': 5, 'timestamp': time.time() - 1800},
    {'author': 'user3', 'likes': 15, 'reposts': 7, 'comments': 5, 'quotes': 2, 'hashtags': ['#AI', '#Future'], 'content_format': 'text', 'engaged_by_followers': 3, 'timestamp': time.time() - 300},
]
user_follows = {'user1', 'user2', 'user3'}
interaction_history = {'user1': 10, 'user2': 5, 'user3': 2}  # Interaction frequency.
trending_hashtags = {'#AI', '#Bluesky'}
format_preferences = {'text': 1, 'image': 2, 'video': 3}  # Higher preference for videos and images.

custom_feed = generate_feed(posts, user_follows, interaction_history, trending_hashtags, format_preferences)
