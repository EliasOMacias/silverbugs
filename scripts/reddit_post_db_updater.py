import psycopg
import praw
import re
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


# Define regex patterns and keywords for labeling spot and silver related posts
spot_pattern = re.compile(r'\b(under|below|at|@)\s+(melt|spot)\b', re.IGNORECASE)
silver_keywords = ['silver','libertad', 'slv', 'ag', 'benjies', 'asw', '90 percent', '90%', 'dime','dimes', 'quarter','quarters','barber','barbers','junk', 'silver eagles', 
                   'constitutional', 'liberties', 'walkers', 'mercs', 'mercuries', 'franklins', 
                   'washingtons', 'washies', '.900', 'ASE', 'ASEs', 'roosevelts']
silver_pattern = re.compile(r'\b(?:' + '|'.join(re.escape(word) for word in silver_keywords) + r')\b', re.IGNORECASE)

#labels silver related posts
def label_silver_posts(text):
    return 1 if silver_pattern.search(text) else 0

#labels silver related spot deals
def label_spot_deal(text, silver_label):
    return 1 if silver_label == 1 and spot_pattern.search(text) else 0



with psycopg.connect(
    dbname="silverbugs_db",
    user="elias_m",
    password="KSefPQeAhZJZM2x7jTdDHFT8i2gwGcnC",
    host="dpg-d1rfk1emcj7s73e3689g-a.oregon-postgres.render.com", 
    port=5432
) as conn:


    with conn.cursor() as cur:
        insert_query = """
        INSERT INTO post_data (id, url, title, selftext, created_utc, num_comments, score, label, spot_deal,silver_post)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """
    
        for post in new_posts:
            # labels posts as WTS or WTB
            label = 'WTS' if '[WTS]' in post['title'].upper() else 'WTB' if '[WTB]' in post['title'].upper() else None
            #combines title and text for silver and spot leable regex 
            title_text = f"{post['title'] or ''} {post['selftext'] or ''}"
            silver_post = label_silver_posts(title_text)
            spot_deal = label_spot_deal(title_text,silver_post)

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
                    label,
                    spot_deal,
                    silver_post
                )
            )

            
        conn.commit()

