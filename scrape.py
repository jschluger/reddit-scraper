import praw, convokit, prawcore, sys, datetime, os, requests
from convokit import Utterance, Conversation, Corpus, User
from apscheduler.schedulers.background import BackgroundScheduler
import show_corpus

############# CONFIGURATION #############

# cron is passed as kwargs to scheduler.add_job to set the timing of
# writing CORPUS to disk at regular intervals.
# See documentation for details at
# https://apscheduler.readthedocs.io/en/stable/modules/triggers/cron.html
cron = {'second': 0} # every time second == 0 (i.e., at the top of each minute)
# cron = {'minute': 0}   # every time minute == 0 (i.e., at the top of each hour)
# cron = {'hour': 0}   # every time   hour == 0 (i.e., at the start of each day)

# A downloaded subreddit will be stored at base_path/<subreddit name>.
base_path = 'corpora'

#############    GLOBALS    #############

reddit = praw.Reddit(client_id='sq6GgQR_4lri7A',
                     client_secret='dWes213OfQWpF7eCVxeImaHSbiw',
                     user_agent='jack')
CORPUS = None
FOLLOWING = []

#############     CODE      #############

def listen_subreddit(sub):
    """
    Listen to sub's comment stream forever, and add all incoming 
    comments and the posts they are on to global CORPUS.

    Params: sub (type praw.models.reddit.subreddit.Subreddit) 
              is the subreddit to listen to. 
    """
    global CORPUS
    while True:
        try:
            for comment in sub.stream.comments():
                utts = comment_to_utts(comment)
                if CORPUS == None:
                    CORPUS = Corpus(utterances=utts)
                else:
                    CORPUS = CORPUS.add_utterances(utts)
                    
        except prawcore.exceptions.RequestException as e:
            print(f'got error {e} from subreddit stream; restarting stream')


def submission_to_utt(submission):
    """
    Parse submission into an utterance.

    Params: submission (type praw.models.reddit.submission.Submission) 

    Returns: [utt] where utt is a convokit Utterance 
               representing submission.
    """
    meta = {'children': [],
            'depth': 0,
            'permalink': submission.permalink,
            'type': 'submission',
            'subreddit': sys.argv[1],
            'title': submission.title,
            'is_self': submission.is_self }
    
    if not submission.is_self:
        meta['link'] = submission.url

        r = requests.get(submission.url)
        meta['html'] = r.text

    for dup in submission.duplicates():
        # print(f'({submission.id}) {submission.title} also posted to {dup.subreddit.display_name} ({dup.id})')
        follow(dup)
        
    utt = Utterance(id=submission.id,
                    text=submission.selftext,
                    reply_to=None,
                    root=submission.id,
                    user=User(id=submission.author.name if submission.author is not None else "n/a"),
                    timestamp=submission.created_utc,
                    meta=meta)
    return [utt]
    
def comment_to_utts(comment):
    """
    Parse comment into an utterance, in addition to comment's 
    parents if they are not yet in CORPUS.

    Params: comment (type praw.models.reddit.comment.Comment) 

    Returns: [utt_1,utt_2,...,utt_n] where each utti is a convokit 
               Utterance. utt_n coresponds to comment, utt_(n-1)
               coresponds to comment's immediate parent ...
               n >= 1. 
    """
    global CORPUS
    pid = comment.parent_id.split('_')

    utts = []
    # add the parent comment/post if not yet in CORPUS
    if CORPUS == None or pid[1] not in CORPUS.utterances:
        if pid[0] == 't1':
            parent_comment = praw.models.Comment(reddit=reddit, id=pid[1])
            utts = comment_to_utts(parent_comment)
        else:
            assert pid[0] == 't3'
            submission = praw.models.Submission(reddit=reddit, id=pid[1])
            utts = submission_to_utt(submission)
        assert utts[-1].id == pid[1]

    # get&update parent utterance
    parent = utts[-1] if len(utts) > 0 else CORPUS.get_utterance(pid[1])
    parent.meta['children'].append(comment.id)

    # add the utterance to the CORPUS
    meta = {'children': [],
            'depth': parent.meta['depth'] + 1,
            'permalink': comment.permalink,
            'subreddit': sys.argv[1],
            'type': 'comment'}
    
    utt = Utterance(id=comment.id,
                    text=comment.body,
                    reply_to=pid[1],
                    root=parent.root,
                    user=User(id=comment.author.name if comment.author is not None else "n/a"),
                    timestamp=comment.created_utc,
                    meta=meta)

    utts.append(utt)
    return utts

def write_corpus():
    """
    Write CORPUS to disk at the location specified in global base_path.
    """
    global CORPUS, base_path
    assert CORPUS is not None
    t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    l = len(list(CORPUS.iter_utterances()))
    print(f'Dumping {sys.argv[1]} corpus at time {t}; contains {l} utterances.')
    CORPUS.dump(name=sys.argv[1],
                base_path=base_path,
                increment_version=False)
    
def follow(submission):
    """
    Add submission to list of additional posts to track, which must 
    be updated at regular intervals outside of the subreddit stream.

    Params: submission (type praw.models.reddit.submission.Submission) 
    """
    global FOLLOWING
    FOLLOWING.append(submission)
    following_update_single(submission)


def following_update_all():
    """
    Update CORPUS with new comments on all posts in FOLLOWING.
    """
    for followed in FOLLOWING:
        following.update_single(followed)


def following_update_single(submission):
    """
    Update CORPUS with new comments on submission.

    Params: submission (type praw.models.reddit.submission.Submission) 
    """
    # ToDo
    pass


    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Must specify subreddit name; e.g.:\n\t $ python scrape.py coronavirus')
        exit(1)
    else:
        if not os.path.isdir(base_path):
            os.makedirs(base_path)
        
        full_path = os.path.join(base_path, sys.argv[1])
        if os.path.isdir(full_path):
            print(f'Corpus already exists at {full_path}; loading corpus...')
            CORPUS = Corpus(filename=full_path)
            print('Done loading corpus!')
        else:
            print(f'No corpus exists at {full_path}; building new corpus from scratch')

        print(f'Scheduling corpus write to disk with cron {cron}')
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=following_update_all, trigger='cron', **cron)
        scheduler.add_job(func=write_corpus, trigger='cron', **cron) # ToDo: make these run on two seperate CRONS
        scheduler.start()

        
        print(f'Listening to {sys.argv[1]} subreddit stream')
        sub = reddit.subreddit(sys.argv[1])
        listen_subreddit(sub)
