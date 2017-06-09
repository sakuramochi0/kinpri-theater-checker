import re


regex_kinpri = re.compile(r'king of prism|キンプリ|キンプラ', flags=re.I)


def get_kinpri_types():
    types = []
    if re.search('(応援|おうえん)上映'):
        types.append('cheering')
    elif re.search('通常上映'):
        types.append('normal')
    elif re.search('おさらい'):
        types.append('normal')
        types.append('kinpri1')
        types.append('rl')
    return types
