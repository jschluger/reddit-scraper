# reddit-scraper
This code was develped with Python 3.7.3.

## Usage:
```
$ pip install requirements.txt
...
$ python scrape.py coronavirus
No corpus exists at corpora/coronavirus; building new corpus from scratch
Scheduling corpus write to disk with cron {'minute': 0}
Listening to coronavirus subreddit stream
dumping coronavirus corpus at time 2020-04-03 14:00:00; contains 1000 utterances
dumping coronavirus corpus at time 2020-04-03 15:00:00; contains 2000 utterances (these numbers are made up)
...
$ python show_corpus.py coronavirus
```
Replace `coronavirus` with the name of any subreddit you want to follow. To use this tool to follow multiple subreddits, use the tool on each subreddit individually and then merge the resulting corpora.

### See scrape.py for configuration options.
