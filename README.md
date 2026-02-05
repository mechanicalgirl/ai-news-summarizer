# ai-news-summarizer

python3 -m venv venv

### to run locally:
```
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

Usage:

### Single URL
`python3 digest.py --url https://example.com/article`

### From file
`python3 digest.py --file my-reading-list.txt`

### Default news sources (for cron)
`python3 digest.py`

