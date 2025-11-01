#!/usr/bin/env python3
"""
Scaled Data Generation Script for Social Media Platform
Generates 10k+ users, 5k+ creators, and 50k+ content items
"""

import psycopg2
import random
import time
from datetime import datetime, timedelta
from faker import Faker
import sys

# Database configuration
DB_CONFIG = {
    'host': 'postgres-service',
    'port': 5432,
    'database': 'socialmedia',
    'user': 'socialmedia',
    'password': 'socialmedia123'
}

# Configuration
NUM_CREATORS = 5000
NUM_USERS = 10000
NUM_CONTENT_ITEMS = 50000
NUM_ACTIVITIES = 100000
BATCH_SIZE = 1000

fake = Faker()

CONTENT_TYPES = ["video", "image", "article", "audio", "story"]
CREATOR_CATEGORIES = ["technology", "fitness", "food", "gaming", "music", "education", "entertainment", "travel"]
USER_TYPES = ["regular", "premium", "pro"]
AGE_GROUPS = ["13-17", "18-24", "25-34", "35-44", "45-54", "55+"]
LOCATIONS = ["US", "UK", "CA", "AU", "DE", "FR", "JP", "BR", "IN", "MX"]
ACTIVITY_TYPES = ["view", "like", "comment", "share"]

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Database connection established")
        return conn
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        sys.exit(1)

def generate_creators(conn, num_creators):
    """Generate content creators"""
    print(f"\n📝 Generating {num_creators} content creators...")
    cursor = conn.cursor()

    creators = []
    for i in range(num_creators):
        creator_id = f'creator_{int(time.time() * 1000000) % 1000000000}_{i}'
        name = fake.name()
        bio = fake.text(max_nb_chars=200)
        followers = random.randint(100, 1000000)
        verified = followers > 50000
        category = random.choice(CREATOR_CATEGORIES)

        creators.append((creator_id, name, bio, followers, verified, category))

        # Insert in batches
        if len(creators) >= BATCH_SIZE:
            cursor.executemany(
                """
                INSERT INTO content_creators (creator_id, name, bio, followers, verified, category)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (creator_id) DO NOTHING
                """,
                creators
            )
            conn.commit()
            print(f"  ✓ Inserted {i+1}/{num_creators} creators")
            creators = []

    # Insert remaining
    if creators:
        cursor.executemany(
            """
            INSERT INTO content_creators (creator_id, name, bio, followers, verified, category)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (creator_id) DO NOTHING
            """,
            creators
        )
        conn.commit()

    cursor.close()
    print(f"✓ Created {num_creators} content creators")

def generate_users(conn, num_users):
    """Generate users"""
    print(f"\n👥 Generating {num_users} users...")
    cursor = conn.cursor()

    users = []
    for i in range(num_users):
        user_id = f'user_{int(time.time() * 1000000) % 1000000000}_{i}'
        username = fake.user_name() + str(random.randint(100, 9999))
        email = fake.email()
        user_type = random.choices(USER_TYPES, weights=[70, 20, 10])[0]
        age_group = random.choice(AGE_GROUPS)
        location = random.choice(LOCATIONS)
        is_active = random.random() > 0.1  # 90% active

        users.append((user_id, username, email, user_type, age_group, location, is_active))

        # Insert in batches
        if len(users) >= BATCH_SIZE:
            cursor.executemany(
                """
                INSERT INTO users (user_id, username, email, user_type, age_group, location, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
                """,
                users
            )
            conn.commit()
            print(f"  ✓ Inserted {i+1}/{num_users} users")
            users = []

    # Insert remaining
    if users:
        cursor.executemany(
            """
            INSERT INTO users (user_id, username, email, user_type, age_group, location, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING
            """,
            users
        )
        conn.commit()

    cursor.close()
    print(f"✓ Created {num_users} users")

def generate_content(conn, num_content):
    """Generate content items"""
    print(f"\n🎬 Generating {num_content} content items...")
    cursor = conn.cursor()

    # Get all creator IDs
    cursor.execute("SELECT creator_id FROM content_creators")
    creator_ids = [row[0] for row in cursor.fetchall()]

    if not creator_ids:
        print("✗ No creators found. Generate creators first.")
        return

    content_items = []
    for i in range(num_content):
        content_id = f'content_{int(time.time() * 1000000) % 1000000000}_{i}'
        creator_id = random.choice(creator_ids)
        content_type = random.choice(CONTENT_TYPES)
        title = fake.sentence(nb_words=random.randint(3, 10))
        description = fake.text(max_nb_chars=300)

        # Add realistic metadata
        duration_seconds = random.randint(30, 3600) if content_type in ['video', 'audio'] else None
        file_size_mb = round(random.uniform(1.0, 2000.0), 2)
        views = random.randint(0, 1000000)
        likes = int(views * random.uniform(0.01, 0.15))  # 1-15% like rate
        comments_count = int(views * random.uniform(0.001, 0.05))  # 0.1-5% comment rate
        shares_count = int(views * random.uniform(0.001, 0.03))  # 0.1-3% share rate

        # Random creation time within last 6 months
        days_ago = random.randint(0, 180)
        created_at = datetime.now() - timedelta(days=days_ago)

        content_items.append((
            content_id, creator_id, content_type, title, description,
            duration_seconds, file_size_mb, views, likes, comments_count, shares_count,
            created_at
        ))

        # Insert in batches
        if len(content_items) >= BATCH_SIZE:
            cursor.executemany(
                """
                INSERT INTO content_items (
                    content_id, creator_id, type, title, description,
                    duration_seconds, file_size_mb, views, likes, comments_count, shares_count,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (content_id) DO NOTHING
                """,
                content_items
            )
            conn.commit()
            print(f"  ✓ Inserted {i+1}/{num_content} content items")
            content_items = []

    # Insert remaining
    if content_items:
        cursor.executemany(
            """
            INSERT INTO content_items (
                content_id, creator_id, type, title, description,
                duration_seconds, file_size_mb, views, likes, comments_count, shares_count,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (content_id) DO NOTHING
            """,
            content_items
        )
        conn.commit()

    # Update creator content counts
    print("  Updating creator content counts...")
    cursor.execute("""
        UPDATE content_creators cc
        SET total_content = (
            SELECT COUNT(*) FROM content_items ci
            WHERE ci.creator_id = cc.creator_id
        )
    """)
    conn.commit()

    cursor.close()
    print(f"✓ Created {num_content} content items")

def generate_user_activities(conn, num_activities):
    """Generate user activities"""
    print(f"\n⚡ Generating {num_activities} user activities...")
    cursor = conn.cursor()

    # Get sample of user and content IDs
    cursor.execute("SELECT user_id FROM users LIMIT 5000")
    user_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT content_id, type FROM content_items LIMIT 10000")
    content_data = cursor.fetchall()

    if not user_ids or not content_data:
        print("✗ No users or content found. Generate them first.")
        return

    activities = []
    for i in range(num_activities):
        user_id = random.choice(user_ids)
        content_id, content_type = random.choice(content_data)
        activity_type = random.choices(
            ACTIVITY_TYPES,
            weights=[60, 25, 10, 5]  # views > likes > comments > shares
        )[0]

        watch_duration = random.randint(10, 300) if activity_type == 'view' else None
        engagement_score = round(random.uniform(0.1, 1.0), 2)

        # Random activity time within last 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 24)
        created_at = datetime.now() - timedelta(days=days_ago, hours=hours_ago)

        activities.append((
            user_id, content_id, activity_type, watch_duration, engagement_score, created_at
        ))

        # Insert in batches
        if len(activities) >= BATCH_SIZE:
            cursor.executemany(
                """
                INSERT INTO user_activities (
                    user_id, content_id, activity_type, watch_duration_seconds, engagement_score, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                activities
            )
            conn.commit()
            print(f"  ✓ Inserted {i+1}/{num_activities} activities")
            activities = []

    # Insert remaining
    if activities:
        cursor.executemany(
            """
            INSERT INTO user_activities (
                user_id, content_id, activity_type, watch_duration_seconds, engagement_score, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            activities
        )
        conn.commit()

    cursor.close()
    print(f"✓ Created {num_activities} user activities")

def generate_user_follows(conn):
    """Generate user follows"""
    print(f"\n💙 Generating user follows...")
    cursor = conn.cursor()

    # Get active users and popular creators
    cursor.execute("SELECT user_id FROM users WHERE is_active = TRUE LIMIT 5000")
    user_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT creator_id FROM content_creators ORDER BY followers DESC LIMIT 2000")
    creator_ids = [row[0] for row in cursor.fetchall()]

    follows = []
    total_follows = 0

    for user_id in user_ids:
        # Each user follows 1-20 creators
        num_follows = random.randint(1, 20)
        followed_creators = random.sample(creator_ids, min(num_follows, len(creator_ids)))

        for creator_id in followed_creators:
            days_ago = random.randint(0, 90)
            followed_at = datetime.now() - timedelta(days=days_ago)
            follows.append((user_id, creator_id, followed_at))
            total_follows += 1

            if len(follows) >= BATCH_SIZE:
                cursor.executemany(
                    """
                    INSERT INTO user_follows (user_id, creator_id, followed_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, creator_id) DO NOTHING
                    """,
                    follows
                )
                conn.commit()
                print(f"  ✓ Inserted {total_follows} follows")
                follows = []

    # Insert remaining
    if follows:
        cursor.executemany(
            """
            INSERT INTO user_follows (user_id, creator_id, followed_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, creator_id) DO NOTHING
            """,
            follows
        )
        conn.commit()

    cursor.close()
    print(f"✓ Created {total_follows} user follows")

def print_statistics(conn):
    """Print database statistics"""
    print("\n" + "="*60)
    print("📊 DATABASE STATISTICS")
    print("="*60)

    cursor = conn.cursor()

    # Content creators
    cursor.execute("SELECT COUNT(*), AVG(followers), MAX(followers) FROM content_creators")
    creator_count, avg_followers, max_followers = cursor.fetchone()
    print(f"\n👨‍💼 Content Creators: {creator_count:,}")
    print(f"   Average followers: {int(avg_followers):,}")
    print(f"   Max followers: {int(max_followers):,}")

    # Users
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN is_active THEN 1 ELSE 0 END) FROM users")
    user_count, active_users = cursor.fetchone()
    print(f"\n👥 Users: {user_count:,}")
    print(f"   Active users: {active_users:,}")

    # Content
    cursor.execute("""
        SELECT COUNT(*), SUM(views), SUM(likes), AVG(views)
        FROM content_items
    """)
    content_count, total_views, total_likes, avg_views = cursor.fetchone()
    print(f"\n🎬 Content Items: {content_count:,}")
    print(f"   Total views: {int(total_views):,}")
    print(f"   Total likes: {int(total_likes):,}")
    print(f"   Average views per content: {int(avg_views):,}")

    # Content by type
    cursor.execute("""
        SELECT type, COUNT(*), SUM(views)
        FROM content_items
        GROUP BY type
        ORDER BY COUNT(*) DESC
    """)
    print(f"\n📈 Content by Type:")
    for content_type, count, views in cursor.fetchall():
        print(f"   {content_type.capitalize():12} {count:>7,} items ({int(views):>12,} views)")

    # Activities
    cursor.execute("SELECT COUNT(*) FROM user_activities")
    activity_count = cursor.fetchone()[0]
    print(f"\n⚡ User Activities: {activity_count:,}")

    # Follows
    cursor.execute("SELECT COUNT(*) FROM user_follows")
    follows_count = cursor.fetchone()[0]
    print(f"💙 User Follows: {follows_count:,}")

    cursor.close()
    print("\n" + "="*60)

def main():
    """Main execution"""
    print("="*60)
    print("🚀 SOCIAL MEDIA PLATFORM - SCALED DATA GENERATOR")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  Content Creators: {NUM_CREATORS:,}")
    print(f"  Users: {NUM_USERS:,}")
    print(f"  Content Items: {NUM_CONTENT_ITEMS:,}")
    print(f"  User Activities: {NUM_ACTIVITIES:,}")
    print(f"\nThis will generate data for a large-scale social media platform.")
    print("The process may take several minutes...")

    input("\nPress Enter to continue or Ctrl+C to cancel...")

    start_time = time.time()

    # Connect to database
    conn = get_db_connection()

    try:
        # Generate data
        generate_creators(conn, NUM_CREATORS)
        generate_users(conn, NUM_USERS)
        generate_content(conn, NUM_CONTENT_ITEMS)
        generate_user_activities(conn, NUM_ACTIVITIES)
        generate_user_follows(conn)

        # Print statistics
        print_statistics(conn)

        elapsed = time.time() - start_time
        print(f"\n✓ Data generation completed in {elapsed:.2f} seconds")
        print(f"✓ Average rate: {(NUM_CREATORS + NUM_USERS + NUM_CONTENT_ITEMS + NUM_ACTIVITIES) / elapsed:.0f} records/second")

    except Exception as e:
        print(f"\n✗ Error during data generation: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\n✓ Database connection closed")

if __name__ == '__main__':
    main()
