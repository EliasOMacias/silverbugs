import praw
import time
import os
import json
from datetime import datetime
import psycopg
from sqlalchemy import create_engine
import io

# uses praw api to scrape posts
def scrape_posts():
    # reddit api access
    reddit_creds = praw.Reddit(client_id='GemgQF90kR7V1F75su4t7g',
                        client_secret = 'IAePy0shvSac6ZY_GUXSkqBLp-AQsw',
                        username='its_lit_in_here_huh',
                        password='chillpassword420',
                        user_agent='pms scraping bot by /u/its_lit_in_here_bot (academic use)')

    subreddit = reddit_creds.subreddit('Pmsforsale')

    # pulls posts in json format
    posts = []
    for post in subreddit.new(limit=999):
        posts.append({
            'id': post.id,
            'title': post.title,
            'created_utc': post.created_utc,
            'score': post.score,
            'num_comments': post.num_comments,
            'url': post.url,
            'selftext': post.selftext
        })

    return posts

posts = scrape_posts()

# Uses psycopg to create table in postgreSQL
def push_posts():
    with psycopg.connect(dbname="silverbugs",
        user="silver_bug",
        password="Th1s1s4p0stgresql",
        host="localhost",  
        port=5432) as conn:
        
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS post_data (
                    id text PRIMARY KEY,
                    url varchar(255),
                    title text,
                    selftext text,
                    created_utc float,
                    num_comments int,
                    score int);
                """)

                conn.commit()

    # converts time stamps from unix for insertion into postgres table
    for post in posts:
        post["created_utc"] = datetime.utcfromtimestamp(post["created_utc"])        


    # Pushes posts to table
    with psycopg.connect(
        dbname="silverbugs",
        user="silver_bug",
        password="Th1s1s4p0stgresql",
        host="localhost",  # or your cloud host
        port=5432
    ) as conn:


        with conn.cursor() as cur:
            insert_query = """
            INSERT INTO post_data (id, url, title, selftext, created_utc, num_comments, score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
            """
        
            for post in posts:
                cur.execute(
                    insert_query,
                    (
                        post["id"],
                        post["url"],
                        post["title"],
                        post["selftext"],
                        post["created_utc"],
                        post["num_comments"],
                        post["score"]
                    )
                )
            conn.commit()


def main():
    scrape_posts()
    push_posts()

if __name__ == "__main__":
    main()