import psycopg
import praw
from datetime import datetime

with psycopg.connect(dbname="silverbugs_db",
    user="elias_m",
    password="KSefPQeAhZJZM2x7jTdDHFT8i2gwGcnC",
    host="dpg-d1rfk1emcj7s73e3689g-a.oregon-postgres.render.com", 
    port=5432
) as conn:

    with conn.cursor() as cur:
        cur.execute("SELECT MAX(created_utc) FROM post_data;")
        last_timestamp = cur.fetchone()[0].timestamp()

reddit_creds = praw.Reddit(client_id='GemgQF90kR7V1F75su4t7g',
                     client_secret = 'IAePy0shvSac6ZY_GUXSkqBLp-AQsw',
                     username='its_lit_in_here_huh',
                     password='chillpassword420',
                     user_agent='pms scraping bot by /u/its_lit_in_here_bot (academic use)')

subreddit = reddit_creds.subreddit('Pmsforsale')



new_posts = []
for post in subreddit.new(limit=999):
    if post.created_utc > last_timestamp-30000:
        new_posts.append({
            'id': post.id,
            'title': post.title,
            'created_utc': post.created_utc,
            'score': post.score,
            'num_comments': post.num_comments,
            'url': post.url,
            'selftext': post.selftext,
        })

print(f"Collected {len(new_posts)} posts")


for post in new_posts:
    post["created_utc"] = datetime.utcfromtimestamp(post["created_utc"])


with psycopg.connect(
    dbname="silverbugs_db",
    user="elias_m",
    password="KSefPQeAhZJZM2x7jTdDHFT8i2gwGcnC",
    host="dpg-d1rfk1emcj7s73e3689g-a.oregon-postgres.render.com", 
    port=5432
) as conn:


    with conn.cursor() as cur:
        insert_query = """
        INSERT INTO post_data (id, url, title, selftext, created_utc, num_comments, score, label)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """
    
        for post in new_posts:
            label = 'WTS' if '[WTS]' in post['title'].upper() else 'WTB' if '[WTB]' in post['title'].upper() else None
            cur.execute(
                insert_query,
                (
                    post["id"],
                    post["url"],
                    post["title"],
                    post["selftext"],
                    post["created_utc"],
                    post["num_comments"],
                    post["score"],
                    label
                )
            )

            
        conn.commit()

