ai-news-summarizer
===============

To run locally:

- Run this one time to create the virtualenv:

```sh
python3 -m venv venv
```

- Activate the virtualenv at the beginning of every session:

```sh
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

To run the summarizer, make sure that you have an API key set locally:
```sh
export ANTHROPIC_API_KEY=my-key-value
```

- Usage - single URL

```sh
python3 digest.py --url https://example.com/article
```

- Usage - from file

```sh
python3 digest.py --file my-reading-list.txt
```

- Default news sources (for cron)
```sh
python3 digest.py
```
