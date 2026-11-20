"""Single source of truth for the Q-matrix SLR final search strings.

Every database's query is rendered from the six term blocks below, so the searches differ only in
field tags, limit syntax and wildcard handling. Run this file to print the 2026-10-09 searches of
record, exactly as run and labelled with their IDs in `Group Project/Rerun Search Log.xlsx`:

    .venv/Scripts/python.exe tools/search_strings.py

Platform rules applied:
  wildcard  - Scopus, Web of Science, EBSCOhost (PsycInfo, ERIC), PubMed, IEEE Xplore: terms as written.
  acm       - ACM DL ignores wildcards inside quoted phrases, so phrases are spelled out; single-word
              wildcards are kept. ACM also applies plurals and stemming by default.
  explicit  - OpenAlex has no wildcards (it stems instead), so every wildcard is spelled out.
In the spelled-out forms, hyphenated phrases are also given without the hyphen, because not every
engine treats a hyphen as a space.
"""

P1A = ['"Q-matri*"', '"Q matri*"']
P1B = ['"cognitive diagnos*"', '"diagnostic classification*"', '"diagnostic assessment*"', 'DINA',
       'attribute*', 'skill*', '"knowledge component*"', 'assessment*']
P2A = ['"knowledge component*"', '"skill model*"', '"cognitive model discover*"',
       '"knowledge concept tagging"', '"skill tagging"', '"knowledge tagging"', '"item-skill"']
P2B = ['discover*', 'refin*', 'generat*', 'tagging', '"data driven"', '"learning factors analysis"',
       'automat*', 'extract*', 'attribution']
P3A = ['"cognitive diagnostic model*"', '"cognitive diagnosis model*"',
       '"diagnostic classification model*"', '"DINA model*"', '"G-DINA"',
       '"cognitive diagnostic assessment*"']
P3B = ['clinical', 'psychiatr*', 'psychopatholog*', '"mental health"', 'symptom*', 'DSM',
       'personality', 'disorder*', 'depress*', 'anxiety', '"non-cognitive"', 'noncognitive',
       '"socio-emotional"', '"social-emotional"']
# Added 2026-10-09: psychological constructs path 3 missed (children's emotional and behavioral
# problems, teamwork). Run with path 4 as one supplementary search; part of path 3 from then on.
P3B_ADD = ['emotion*', 'behavio*', 'teamwork', '"well-being"', 'wellbeing', 'motivation*', 'attitude*',
           'creativ*', '"self-regulat*"']
P3B_RUN1 = list(P3B)          # path 3 as run on 2026-10-08
P3B = P3B + P3B_ADD
# Path 4 (added 2026-10-09 after milestone 2 feedback): educational-measurement studies that apply a
# diagnostic model without using the term "Q-matrix". Same model names as path 3, education context.
# "test*" and "assessment*" are deliberately absent: "cognitive diagnostic assessment" contains
# "assessment", and "tested" appears in nearly every abstract.
P4A = P3A
P4B = ['student*', 'learner*', 'pupil*', 'examinee*', 'school*', 'educat*', 'classroom*', 'curricul*',
       'reading', 'mathematic*', 'exam', 'exams', 'examination*', '"language assessment*"',
       '"language test*"']
PATHS = [(P1A, P1B), (P2A, P2B), (P3A, P3B), (P4A, P4B)]

# Spelled-out forms of every wildcard term, for engines that can't truncate.
EXPAND = {
    '"Q-matri*"': ['"Q-matrix"', '"Q-matrices"'],
    '"Q matri*"': ['"Q matrix"', '"Q matrices"'],
    '"cognitive diagnos*"': ['"cognitive diagnosis"', '"cognitive diagnoses"', '"cognitive diagnostic"'],
    '"diagnostic classification*"': ['"diagnostic classification"', '"diagnostic classifications"'],
    '"diagnostic assessment*"': ['"diagnostic assessment"', '"diagnostic assessments"'],
    'attribute*': ['attribute', 'attributes'],
    'skill*': ['skill', 'skills'],
    '"knowledge component*"': ['"knowledge component"', '"knowledge components"'],
    'assessment*': ['assessment', 'assessments'],
    '"skill model*"': ['"skill model"', '"skill models"', '"skill modeling"', '"skill modelling"'],
    '"cognitive model discover*"': ['"cognitive model discovery"'],
    '"item-skill"': ['"item-skill"', '"item skill"'],
    'discover*': ['discover', 'discovers', 'discovered', 'discovering', 'discovery'],
    'refin*': ['refine', 'refines', 'refined', 'refining', 'refinement'],
    'generat*': ['generate', 'generates', 'generated', 'generating', 'generation', 'generative'],
    '"data driven"': ['"data driven"', '"data-driven"'],
    'automat*': ['automate', 'automated', 'automatic', 'automatically', 'automating', 'automation'],
    'extract*': ['extract', 'extracts', 'extracted', 'extracting', 'extraction'],
    '"cognitive diagnostic model*"': ['"cognitive diagnostic model"', '"cognitive diagnostic models"',
                                      '"cognitive diagnostic modeling"', '"cognitive diagnostic modelling"'],
    '"cognitive diagnosis model*"': ['"cognitive diagnosis model"', '"cognitive diagnosis models"',
                                     '"cognitive diagnosis modeling"', '"cognitive diagnosis modelling"'],
    '"diagnostic classification model*"': ['"diagnostic classification model"',
                                           '"diagnostic classification models"',
                                           '"diagnostic classification modeling"',
                                           '"diagnostic classification modelling"'],
    '"DINA model*"': ['"DINA model"', '"DINA models"'],
    '"cognitive diagnostic assessment*"': ['"cognitive diagnostic assessment"',
                                           '"cognitive diagnostic assessments"'],
    'psychiatr*': ['psychiatric', 'psychiatry'],
    'psychopatholog*': ['psychopathology', 'psychopathological'],
    'symptom*': ['symptom', 'symptoms'],
    'disorder*': ['disorder', 'disorders'],
    'depress*': ['depression', 'depressive', 'depressed'],
    '"non-cognitive"': ['"non-cognitive"', '"non cognitive"'],
    '"socio-emotional"': ['"socio-emotional"', '"socio emotional"'],
    'student*': ['student', 'students'],
    'learner*': ['learner', 'learners'],
    'pupil*': ['pupil', 'pupils'],
    'examinee*': ['examinee', 'examinees'],
    'school*': ['school', 'schools', 'schooling'],
    'educat*': ['education', 'educational', 'educators'],
    'classroom*': ['classroom', 'classrooms'],
    'curricul*': ['curriculum', 'curricula', 'curricular'],
    'mathematic*': ['mathematics', 'mathematical'],
    'examination*': ['examination', 'examinations'],
    '"language assessment*"': ['"language assessment"', '"language assessments"'],
    '"language test*"': ['"language test"', '"language tests"', '"language testing"'],
    'emotion*': ['emotion', 'emotions', 'emotional'],
    'behavio*': ['behavior', 'behaviors', 'behavioral', 'behaviour', 'behaviours', 'behavioural'],
    'motivation*': ['motivation', 'motivational'],
    'attitude*': ['attitude', 'attitudes'],
    'creativ*': ['creative', 'creativity'],
    '"self-regulat*"': ['"self-regulated"', '"self-regulation"', '"self-regulatory"'],
    '"social-emotional"': ['"social-emotional"', '"social emotional"'],
}


def terms(block, mode):
    out = []
    for t in block:
        if mode == 'wildcard':
            out.append(t)
        elif mode == 'acm' and not t.startswith('"'):
            out.append(t)                        # single-word wildcards work in ACM
        else:
            out.extend(EXPAND.get(t, [t]))
    return out


def ors(block, mode='wildcard', tag=''):
    return ' OR '.join(f'{t}{tag}' for t in terms(block, mode))


def path(a, b, mode='wildcard', tag=''):
    return f'({ors(a, mode, tag)}) AND ({ors(b, mode, tag)})'


def scopus():
    core = ' OR '.join(f'TITLE-ABS-KEY( {path(a, b)} )' for a, b in PATHS)
    return f'( {core} ) AND PUBYEAR > 2020 AND PUBYEAR < 2028 AND LANGUAGE(english)'


def scopus_core():
    return ' OR '.join(f'TITLE-ABS-KEY( {path(a, b)} )' for a, b in PATHS)


def wos():
    core = ' OR '.join(f'TS=({path(a, b)})' for a, b in PATHS)
    return f'({core}) AND PY=(2021-2027) AND LA=(English)'


def wos_core():
    return ' OR '.join(f'TS=({path(a, b)})' for a, b in PATHS)


def ebsco(i):
    """One EBSCOhost search per path; title, abstract and author keywords."""
    a, b = PATHS[i]
    def fields(block):
        x = ors(block)
        return f'(TI ({x}) OR AB ({x}) OR KW ({x}))'
    return f'{fields(a)} AND {fields(b)}'


def pubmed():
    core = ' OR '.join(f'({path(a, b, tag="[tiab]")})' for a, b in PATHS)
    return f'({core}) AND ("2021/01/01"[dp] : "2027/12/31"[dp]) AND english[la]'


def ieee(i):
    return path(*PATHS[i])


def acm(i):
    return path(*PATHS[i], mode='acm')


def openalex(i):
    a, b = PATHS[i]
    return f'({path(a, b, mode="explicit")})'


def scopus_path(i):
    a, b = PATHS[i]
    return f'TITLE-ABS-KEY( {path(a, b)} ) AND PUBYEAR > 2020 AND PUBYEAR < 2028 AND LANGUAGE(english)'


def wos_path(i):
    a, b = PATHS[i]
    return f'TS=({path(a, b)}) AND PY=(2021-2027) AND LA=(English)'


def pubmed_path(i):
    a, b = PATHS[i]
    return f'({path(a, b, tag="[tiab]")}) AND ("2021/01/01"[dp] : "2027/12/31"[dp]) AND english[la]'


# The supplementary search (2026-10-09): model names AND (new path 3 terms OR path 4's education
# terms). Together with the 2026-10-08 run it equals paths 1-4 with the final path 3.
SUPP_B = P3B_ADD + P4B


def supp_core(mode='wildcard', tag=''):
    return path(P4A, SUPP_B, mode, tag)


def scopus_supp():
    return f'TITLE-ABS-KEY( {supp_core()} ) AND PUBYEAR > 2020 AND PUBYEAR < 2028 AND LANGUAGE(english)'


def wos_supp():
    return f'TS=({supp_core()}) AND PY=(2021-2027) AND LA=(English)'


def ebsco_supp():
    def fields(block):
        x = ors(block)
        return f'(TI ({x}) OR AB ({x}) OR KW ({x}))'
    return f'{fields(P4A)} AND {fields(SUPP_B)}'


def pubmed_supp():
    return f'({supp_core(tag="[tiab]")}) AND ("2021/01/01"[dp] : "2027/12/31"[dp]) AND english[la]'


def acm_supp():
    return supp_core(mode='acm')


def ieee_supp_split(max_terms=25):
    """IEEE allows 10 wildcards and 25 terms per clause: keep the 6 model-name terms (5 wildcards) and
    spell out the context terms, split into as many searches as needed."""
    ctx = terms(SUPP_B, 'explicit')
    room = max_terms - len(P4A)
    n = -(-len(ctx) // room)
    size = -(-len(ctx) // n)
    return [f'({ors(P4A)}) AND ({" OR ".join(ctx[k:k + size])})' for k in range(0, len(ctx), size)]


def ieee_split(i, max_wildcards=10, max_terms=25):
    """IEEE renders of path i: the path as written if it fits IEEE's limits (10 wildcards per search,
    25 terms per clause); otherwise the first block keeps its wildcards, the second is spelled out and
    split into as few searches as fit."""
    a, b = PATHS[i]
    q = ieee(i)
    if wildcard_count(q) <= max_wildcards and len(terms(a, 'wildcard')) + len(terms(b, 'wildcard')) <= max_terms:
        return [q]
    ctx = terms(b, 'explicit')
    room = max_terms - len(a)
    n = -(-len(ctx) // room)
    size = -(-len(ctx) // n)
    return [f'({ors(a)}) AND ({" OR ".join(ctx[k:k + size])})' for k in range(0, len(ctx), size)]


def wildcard_count(s):
    return s.count('*')


def searches_of_record():
    """The 2026-10-09 searches of record, labelled with their IDs in `Rerun Search Log.xlsx`, as
    (database, search ID, query, fields, limits applied outside the query)."""
    out = [('Scopus', 'SCOPUS', scopus(), 'Title, abstract, keywords', 'in query'),
           ('Web of Science Core Collection', 'WOS', wos(), 'Topic (TS=)', 'in query')]
    for db in ('APA PsycInfo (EBSCOhost)', 'ERIC (EBSCOhost)'):
        for i in range(4):
            out.append((db, f'S{i + 1}', ebsco(i), 'TI, AB, KW', 'none'))
        out.append((db, 'S5', 'S1 OR S2 OR S3 OR S4', 'TI, AB, KW',
                    'date 2021-2027 and English (EBSCOhost limiters)'))
    out.append(('PubMed', 'PUBMED', pubmed(), '[tiab]', 'in query'))
    for i in range(4):
        parts = ieee_split(i)
        for k, q in enumerate(parts):
            sid = f'I-P{i + 1}' + ('abcdefgh'[k] if len(parts) > 1 else '')
            out.append(('IEEE Xplore', sid, q, 'All Metadata', 'year 2021-2027 (sidebar filter)'))
    for i in range(4):
        out.append(('ACM Digital Library', f'A{i + 1}', acm(i), 'Abstract',
                    'publication date 2021-2027; Full-Text Collection'))
    return out


def latex_appendix():
    """The searches of record as LaTeX listings (style `query`, defined in the paper's preamble),
    one subsection per database. PsycInfo and ERIC ran identical EBSCOhost searches, so they share
    one subsection."""
    groups = {}
    for db, sid, q, fields, limits in searches_of_record():
        key = 'APA PsycInfo and ERIC (EBSCOhost)' if 'EBSCOhost' in db else db
        group = groups.setdefault(key, [])
        if sid not in [g[0] for g in group]:
            group.append((sid, q, fields, limits))
    out = []
    for db, searches in groups.items():
        out.append(f'\\subsection{{{db}}}\n')
        fields = {f for _, _, f, _ in searches}
        out.append(f'Fields searched: {", ".join(sorted(fields))}.\n')
        for sid, q, _, limits in searches:
            title = sid if limits in ('in query', 'none') else f'{sid} (limits set outside the query: {limits})'
            out.append(f'\\begin{{lstlisting}}[style=query,title={{{title}}}]\n{q}\n'
                       '\\end{lstlisting}\n')
    return '\n'.join(out)


if __name__ == '__main__':
    # Prints the queries exactly as run on 2026-10-09 (the searches of record). The 8 Oct
    # supplementary functions (*_supp) and openalex() are kept for the record but were not part of
    # the final search; OpenAlex was dropped by team decision.
    # With --latex, prints them as the paper's appendix listings instead.
    import sys
    if '--latex' in sys.argv:
        print('% Generated by tools/search_strings.py --latex. Do not edit by hand.\n')
        print(latex_appendix())
    else:
        for db, sid, q, fields, limits in searches_of_record():
            print(f'{db} - {sid}\nFields: {fields}. Limits outside the query: {limits}.\n{q}\n')
