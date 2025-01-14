
# YouTube Data Project

This project provides tools for creating and populating a database with YouTube data, including information about channels, videos, and comments. The purpose is to analyze YouTube activity for research or personal exploration in a structured way. 

## Overview

The project performs the following tasks:
1. **Database Creation**: Creates a SQLite database to store YouTube data.
2. **Data Ingestion**: Reads data from CSV files containing information about channels, videos, and comments, and populates the database.
3. **Data Analysis**: Enables querying the database to explore YouTube data, such as counting comments per channel or analyzing engagement metrics.

The entire workflow is designed to be straightforward and accessible, even for those with limited programming experience.

---

## Features

- **Structured Storage**: Stores YouTube channel, video, and comment data in a relational database.
- **Custom Queries**: Allows detailed analysis, such as counting comments across channels or videos.
- **CSV Integration**: Easily import data from CSV files into the database.
- **Reusable Database**: The database can be queried with SQL for custom insights.

---

## How It Works

### 1. Database Creation
The project initializes a SQLite database file (`youtube_data.db`) and creates the following tables:

- **`channels`**:
  Stores information about YouTube channels, including:
  - Channel ID
  - Title
  - Description
  - Published date
  - Subscriber count

- **`videos`**:
  Stores information about videos, such as:
  - Video ID
  - Associated channel ID
  - Video title
  - Published date
  - View count

- **`comments`**:
  Stores comments for videos, including:
  - Comment ID
  - Associated video ID
  - Comment text
  - Author channel ID
  - Published date

### 2. Populating the Database

#### Channels
CSV files containing channel information are loaded into the `channels` table. Example columns include:
- `id` (Channel ID)
- `title` (Channel Title)
- `description`
- `subscriberCount`

#### Videos
CSV files with video information populate the `videos` table. Example columns include:
- `id` (Video ID)
- `channelId` (Linked to `channels.id`)
- `title`
- `viewCount`

#### Comments
Comments data is imported into the `comments` table. Example columns include:
- `id` (Comment ID)
- `video_id` (Linked to `videos.id`)
- `author_channel_id`
- `text`

### 3. Querying the Database
Once populated, the database supports queries for insights. Example queries:

- Total comments for a specific channel:
  ```sql
  SELECT ch.id AS channel_id, ch.title AS channel_title, COUNT(c.id) AS total_comments
  FROM channels ch
  JOIN videos v ON ch.id = v.channelId
  JOIN comments c ON v.videoId = c.video_id
  WHERE ch.id = 'specific_channel_id'
  GROUP BY ch.id;
  ```

- Total comments across all channels:
  ```sql
  SELECT ch.id AS channel_id, ch.title AS channel_title, COUNT(c.id) AS total_comments
  FROM channels ch
  JOIN videos v ON ch.id = v.channelId
  JOIN comments c ON v.videoId = c.video_id
  GROUP BY ch.id
  ORDER BY total_comments DESC;
  ```

---

## Requirements

To run this project, you need:

1. **Python 3.x**
   - Libraries: `pandas`, `sqlite3`

2. **CSV Files**
   - Channel, video, and comment data in CSV format.

3. **DB Browser for SQLite (optional)**
   - For visual exploration of the database.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/youtube-data-project.git
   cd youtube-data-project
   ```

2. Install Python dependencies:
   ```bash
   pip install pandas
   ```

3. Prepare your data:
   - Place your channel, video, and comment CSV files in the corresponding folders (`channels/`, `videos/`, `comments/`).

---

## Usage

1. Run the script to create and populate the database:
   ```bash
   python capture_YT_comments.py
   ```

2. Use SQL to query the database:
   - Open the database file (`youtube_data.db`) in DB Browser for SQLite or any SQL tool.
   - Execute queries to explore data insights.

---

## Example Workflow

1. **Create the Database**:
   The script will create `youtube_data.db` with the necessary tables.

2. **Import Data**:
   Place your CSV files in the appropriate folders and run the script to populate the tables.

3. **Analyze**:
   Open the database in a SQL tool and run queries to extract insights.

---

## Contributing

Contributions are welcome! If you have ideas for improvement, feel free to open an issue or submit a pull request.

---

## License

This project is licensed under the MIT License.
