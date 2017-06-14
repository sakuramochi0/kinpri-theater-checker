import re
import zenhan


def normalize(text):
    return zenhan.z2h(text, mode=zenhan.DIGIT|zenhan.ASCII)


def is_title_kinpri(title):
    title = normalize(title)
    regex_kinpri = re.compile(r'king\sof\sprism|キンプリ|キンプラ', flags=re.I)
    return regex_kinpri.search(title)


def get_kinpri_types(title):
    types = []
    if re.search('(応援|おうえん)上映', title):
        types.append('cheering')
    elif re.search('通常上映', title):
        types.append('normal')

    if re.search('舞台挨拶', title):
        types.append('special')
        types.append('talkshow')
        if re.search('中継', title):
            types.append('liveviewing')
    elif re.search('おさらい', title):
        types.append('special')
        types.append('kinpri1')
        if re.search('大おさらい', title):
            types.append('rl')
    elif re.search('by PrettyRhythm', title):
        types.append('kinpri1')

    # set default
    if not types:
        types.append('normal')

    return types
