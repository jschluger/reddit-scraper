import convokit, textwrap, sys, os
from convokit import Corpus
import scrape

def show_corpus(corpus):
    pid = None
    for convo in corpus.iter_conversations():
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
    print(f'done viewing corpus {corpus}')

def indent(text, n=0):
    print(textwrap.indent(textwrap.fill(text), '   ' * n + '| '))
            

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Must specify subreddit name; e.g.:\n\t $ python show_corpus.py coronavirus')
        exit(1)
    else:
        full_path = os.path.join(scrape.base_path, sys.argv[1])
        if not os.path.isdir(full_path):
            print(f'Cannot find corpus at path {full_path} \n\t(path constructed using scrape.base_path)')
            full_path = sys.argv[1]
            if not os.path.isdir(full_path):
                print(f'Also cannot find corpus at path {full_path}')
                exit(1)
            else:
                print(f'Found corpus at path {full_path}')
        else:
            print(f'Found corpus at path {full_path}')
            
        corpus = Corpus(filename=full_path)
        show_corpus(corpus)
