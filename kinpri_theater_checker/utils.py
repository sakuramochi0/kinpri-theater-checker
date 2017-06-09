import re


regex_kinpri = re.compile(r'king of prism|キンプリ|キンプラ', flags=re.I)


def get_kinpri_types(title):
    types = []
    if re.search('(応援|おうえん)上映', title):
        types.append('cheering')
    elif re.search('通常上映', title):
        types.append('normal')
    elif re.search('舞台挨拶', title):
        types.append('special')
        types.append('talkshow')
        if re.search('中継', title):
            types.append('liveviewing')
    elif re.search('おさらい', title):
        types.append('special')
        types.append('kinpri1')
        if re.search('大おさらい', title):
            types.append('rl')

    # set default
    if not types:
        types.append('normal')

    return types
