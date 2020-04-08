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

## Data Format
This tool generates a convokit corpus, with a convokit utterance for each reddit submission and comment the tool encounters. It may be helpful to consult the Praw documentation for [Submission](https://praw.readthedocs.io/en/latest/code_overview/models/submission.html) and [Comment](https://praw.readthedocs.io/en/latest/code_overview/models/comment.html]) for uttmost clarity.

If `utt` is an convokit Utterance representing praw Submission `submission`, then:
- `utt.id = submission.id`
- `utt.text = submission.selftext`
- `utt.reply_to = None`
- `utt.root = submission.id`
- `utt.author = submission.author.name`
- `utt.timestamp = submission.created_utc`
- 
```
utt.meta = {'children': <list of ids of top level comments on submission>,
  	    'depth': 0,	     
	    'permalink': submission.permalink,
            'type': 'submission',
            'subreddit': submission.subreddit.display_name,
            'title': submission.title,
            'is_self': submission.is_self } 
```
- Additionally, if `submission.is_self==False` (i.e., submission is a link), then `meta['link'] = submission.url` and `meta['html']` is the response from a get request to `submission.url`, or None if that request fails.

If `utt` is a convokit Utterance representing praw Comment `comment`, then:
- `utt.id = comment.id`
- `utt.text = comment.body`
- `utt.reply_to = <id of comment's parent>`
- `utt.root = <id of the submission comment is a comment on>`
- `utt.author = comment.author.name`
- `utt.timestamp = comment.created_utc`
- 
```
utt.meta = {'children': <list of ids of comments directly replying to comment>,
    	    'depth': <comment's depth in the comment forrest>,	     
	    'permalink': comment.permalink,
            'type': 'comment',
            'subreddit': comment.subreddit.display_name }
