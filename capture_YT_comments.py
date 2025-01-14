import os
import asyncio
import aiohttp
import time
import sqlite3
import pandas as pd
from googleapiclient.discovery import build
from dotenv import load_dotenv
import logging
import html
from tqdm import tqdm
import json

# Load configuration
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Constants from config
DATABASE_FILE = config["database_file"]
LOG_FILE = config["log_file"]
VIDEOS_CSV = config["videos_csv"]
RETRIES = config["retries"]
DELAY = config["delay"]
BATCH_SIZE = config["batch_size"]

# Load API key from .env file
load_dotenv(config["youtube_api_key"])
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Initialize YouTube API client
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Set up logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Fetch comments for a video with retry logic
def fetch_comments_with_retry(video_id):
    for attempt in range(RETRIES):
        try:
            return fetch_comments(video_id)
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed for video {video_id}: {e}")
            time.sleep(DELAY)
    logging.error(f"All {RETRIES} attempts failed for video {video_id}")
    return []

# Fetch top-level comments
async def fetch_comments(session, video_id):
    API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": 100,
        "textFormat": "plainText",
        "key": YOUTUBE_API_KEY,
    }
    async with session.get(API_URL, params=params) as response:
        if response.status == 403:
            # Parse error details from the response
            error_response = await response.json()
            reason = error_response.get("error", {}).get("errors", [{}])[0].get("reason", "")
            message = error_response.get("error", {}).get("message", "")

            if "commentsDisabled" in reason or "disabled comments" in message:
                logging.info(f"Comments are disabled for video {video_id}.")
            else:
                logging.error(f"403 Forbidden for video {video_id}. Reason: {reason}, Message: {message}")
            return []

        elif response.status != 200:
            logging.error(f"Failed to fetch comments for video {video_id}: HTTP {response.status}")
            return []

        # Process successful response
        data = await response.json()
        comments = []
        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comment = {
                "id": item["id"],
                "video_id": video_id,
                "reply_count": item["snippet"].get("totalReplyCount", 0),
                "like_count": snippet.get("likeCount", 0),
                "published_at": snippet["publishedAt"],
                "author_name": snippet["authorDisplayName"],
                "text": html.unescape(snippet["textDisplay"]),
                "author_channel_id": snippet.get("authorChannelId", {}).get("value"),
                "author_channel_url": snippet.get("authorChannelUrl"),
                "is_reply": False,
                "is_reply_to": None,
                "is_reply_to_name": None,
            }
            comments.append(comment)
        return comments

async def process_video_batch(video_ids):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_comments(session, video_id) for video_id in video_ids]
        results = await asyncio.gather(*tasks)  # Concurrently fetch comments for all videos
        return [comment for result in results for comment in result if result]

# Fetch replies for a comment
def fetch_replies(parent_id, video_id):
    replies = []
    request = youtube.comments().list(
        part="snippet",
        parentId=parent_id,
        maxResults=100,
        textFormat="plainText"
    )
    response = request.execute()
    for item in response.get("items", []):
        snippet = item["snippet"]
        reply = {
            "id": item["id"],
            "video_id": video_id,
            "reply_count": 0,
            "like_count": snippet.get("likeCount", 0),
            "published_at": snippet["publishedAt"],
            "author_name": snippet["authorDisplayName"],
            "text": html.unescape(snippet["textDisplay"]),
            "author_channel_id": snippet.get("authorChannelId", {}).get("value"),
            "author_channel_url": snippet.get("authorChannelUrl"),
            "is_reply": True,
            "is_reply_to": parent_id,
            "is_reply_to_name": None,
        }
        replies.append(reply)
    return replies

# Batch insert comments into the database
def insert_comments_batch(cursor, comments):
    cursor.executemany("""
    INSERT OR IGNORE INTO comments (
        id, video_id, reply_count, like_count, published_at,
        author_name, text, author_channel_id, author_channel_url,
        is_reply, is_reply_to, is_reply_to_name
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, [
        (
            comment["id"], comment["video_id"], comment["reply_count"],
            comment["like_count"], comment["published_at"],
            comment["author_name"], comment["text"],
            comment["author_channel_id"], comment["author_channel_url"],
            comment["is_reply"], comment["is_reply_to"], comment["is_reply_to_name"]
        ) for comment in comments
    ])

# Main function
def main():
    # Load video IDs from CSV
    videos_df = pd.read_csv(VIDEOS_CSV)
    video_ids = videos_df["videoId"]

    # Connect to the database
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()

        # Process each video ID
        for i in tqdm(range(0, len(video_ids), BATCH_SIZE), desc="Processing video batches"):
            batch = video_ids[i:i + BATCH_SIZE]
            comments = asyncio.run(process_video_batch(batch))
            if comments:
                insert_comments_batch(cursor, comments)
                conn.commit()
                logging.info(f"Inserted {len(comments)} comments for batch {i // BATCH_SIZE + 1}")

    logging.info("All comments processed successfully.")

if __name__ == "__main__":
    main()