# ai-news-summarizer

python3 -m venv venv

### to run locally:
```
source venv/bin/activate
python3.13 -m pip install -r requirements.txt
```
then
```
flask --app summarizer run --debug
http://127.0.0.1:5000
```
OR
```
uwsgi uwsgi.ini
http://127.0.0.1:1024
```

For config values, create a file `summarizer/config.py` (see `config.example.py`).
