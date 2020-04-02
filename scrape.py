import praw, convokit, prawcore, textwrap
from convokit import Utterance, Conversation, Corpus, User

reddit = praw.Reddit(client_id='sq6GgQR_4lri7A',
                     client_secret='dWes213OfQWpF7eCVxeImaHSbiw',
                     user_agent='jack')

CORPUS = None

def listen_subreddit(sub_name=None):
    c=0
    while True:
        try:
            for comment in reddit.subreddit(sub_name).stream.comments():
                add_comment(comment)
                c+=1
                print(f'({c})\tadded comment {comment} to CORPUS')
                if c % 100 == 0:
                    show_corpus()
        
        except prawcore.exceptions.RequestException as e:
            print(f'got error {e} from subreddit stream; restarting stream')


def add_submission(submission):
    global CORPUS

    meta = {'children': [],
            'depth': 0,
            'permalink': submission.permalink,
            'type': 'submission',
            'title': submission.title}
    
    utt = Utterance(id=submission.id,
                    text=submission.selftext,
                    reply_to=None,
                    root=submission.id,
                    user=User(id=submission.author.name if submission.author is not None else "n/a"),
                    timestamp=submission.created_utc,
                    meta=meta)
    
    if CORPUS == None:
        CORPUS = Corpus(utterances=[utt])
    else:
        CORPUS = CORPUS.add_utterances([utt])


    
def add_comment(comment):
    global CORPUS
    pid = comment.parent_id.split('_')

    # add the parent comment/post if not yet in CORPUS
    if CORPUS == None or pid[1] not in CORPUS.utterances:
        if pid[0] == 't1':
            parent_comment = praw.models.Comment(reddit=reddit, id=pid[1])
            add_comment(parent_comment)
        else:
            assert pid[0] == 't3'
            submission = praw.models.Submission(reddit=reddit, id=pid[1])
            add_submission(submission)
            
    # get&update parent utterance
    parent = CORPUS.get_utterance(pid[1])
    parent.meta['children'].append(comment.id)

    # add the utterance to the CORPUS
    meta = {'children': [],
            'depth': parent.meta['depth'] + 1,
            'permalink': comment.permalink,
            'type': 'comment'}
    
    utt = Utterance(id=comment.id,
                    text=comment.body,
                    reply_to=pid[1],
                    root=parent.root,
                    user=User(id=comment.author.name if comment.author is not None else "n/a"),
                    timestamp=comment.created_utc,
                    meta=meta)

    if CORPUS == None:
        CORPUS = Corpus(utterances=[utt])
    else:
        CORPUS = CORPUS.add_utterances([utt])


def show_corpus():
    global CORPUS
    pid = None
    for convo in CORPUS.iter_conversations():
        for utt in convo.traverse('dfs'):
            if utt.meta['type'] == 'comment':
                text = f'(id={utt.id}) (reply_to={utt.reply_to})({utt.user.id}): \n{utt.text}' # ~ {utt.meta}'
            else:
                assert utt.meta['type'] == 'submission'
                text = f'(id={utt.id}) (reply_to={utt.reply_to})({utt.user.id}): !{utt.meta["title"]}! \n{utt.text}'#  ~ {utt.meta}'
            indent(text, utt.meta['depth'])
            if utt.meta['depth'] == 0:
                pid = utt.id
            else:
                try:
                    assert pid == utt.root
                except AssertionError as e:
                    print(f'pid={pid} != utt.root={utt.root}')
                    raise e
            
def indent(text, n=0):
    print(textwrap.indent(textwrap.fill(text), '   ' * n + '| '))
            
if __name__ == '__main__':
    # listen_subreddit('coronavirus')
    listen_subreddit('cornell')
