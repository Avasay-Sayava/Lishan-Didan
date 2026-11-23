import yaml
import sys
import os
import re
import shutil
import subprocess
import unicodedata

TAB_LENGTH = 6.0

def superscript(text):
    return r"\textsuperscript{\textsubscript{" + text + r"}}\!"

def subscript(text):
    return r"\textsubscript{" + text + r"}"

def to_roman(n):
    val = [
        (1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'),
        (100, 'c'), (90, 'xc'), (50, 'l'), (40, 'xl'),
        (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')
    ]
    res = []
    for arabic, roman in val:
        count, n = divmod(n, arabic)
        res.append(roman * count)
    return "".join(res)

def format_latex(text, smallcaps=True):
    if not text:
        return ""

    import re
    # 1. Turn ALL CAPS abbreviations (like PRO, NV, 3M) into small caps
    if smallcaps:
        text = re.sub(r'(?<![A-Za-z0-9])(?=[A-Z0-9]{2,})(?=[A-Z0-9]*[A-Z])([A-Z0-9]+)(?![A-Za-z0-9])', lambda m: r"{\small \textnormal{\textsc{" + m.group(1).lower() + r"}}}", text)
    
    # 2. Turn _i into a subscript using the user's custom subscript format
    text = re.sub(r'_([a-zA-Z0-9]+)', lambda m: subscript(r"\textnormal{" + m.group(1) + r"}"), text)

    text = text.replace("&", r"\&")
    text = text.replace("~", r"\textasciitilde{}")
    text = text.replace("+", superscript("+"))
    text = text.replace("/∅", superscript("∅"))

    return text

POS_ABBREV = {
    "noun": "n.",
    "adjective": "adj.",
    "preposition": "prep.",
    "adverb": "adv.",
    "pronoun": "pron.",
    "conjunction": "conj.",
    "particle": "part.",
    "interjection": "interj.",
    "numeral": "num.",
    "expression": "expr.",
    "quantifier": "quant.",
}

GENDER_ABBREV = {
    "masculine": "m.",
    "feminine": "f.",
}

NUMBER_ABBREV = {
    "plural": "pl.",
    "singular": "sg.",
}

FORM_ABBREV = {
    "masculine_singular": "ms.",
    "feminine_singular": "fs.",
    "singular": "sg.",
    "plural": "pl.",
    "construct": "cstr.",
    "ms": "ms.",
    "fs": "fs.",
    "sg": "sg.",
    "pl": "pl.",
}

def format_pos(pos, gender="", number=""):
    p = POS_ABBREV.get(pos.strip().lower(), pos.strip()) if pos else ""
    n = NUMBER_ABBREV.get(number.strip().lower(), number.strip()) if number else ""
    if n == "pl.":
        return f"{p}{n}" if p else n
    g = GENDER_ABBREV.get(gender.strip().lower(), gender.strip()) if gender else ""
    if p and g:
        return f"{p}{g}"
    return p or g

def format_verb_label(entry):
    transitivity = entry.get('transitivity', '')
    telicity = entry.get('telicity', '')
    if transitivity == "transitive":
        return "(tr.)"
    elif transitivity == "intransitive":
        if telicity == "telic":
            return "(intr., tel.)"
        elif telicity == "atelic":
            return "(intr., atel.)"
        else:
            return "(intr.)"
    return ""

def format_idiom(idiom):
    ld = format_latex(idiom.get('lishan_didan', ''))
    meanings = idiom.get('meanings', [])
    if not meanings and idiom.get('meaning_en'):
        meanings = [idiom]
    m_strs = []
    for m in meanings:
        en = format_latex(m.get('meaning_en', '')).strip()
        if not en:
            continue
        label = format_verb_label(m)
        if label:
            m_strs.append(rf"\textbf{{{en} {label}}}")
        else:
            m_strs.append(rf"\textbf{{{en}}}")
    if m_strs:
        return rf"\textit{{{ld}}} " + "; ".join(m_strs)
    return rf"\textit{{{ld}}}"

def process_stem(stem):
    cls = stem.get('class', '')
    if cls == "Q":
        cls_str = r"\textbf{Q}"
    else:
        cls_str = rf"\textbf{{{cls}}}"
        
    pretendant = stem.get('pretendant')
    if pretendant:
        pretendant_str = rf"{{{format_latex(pretendant)}}}"
    else:
        pretendant_str = ""

    bases = stem.get('bases', {})
    realis = format_latex(bases.get('realis', ''))
    irrealis = format_latex(bases.get('irrealis', ''))
    past = format_latex(bases.get('past', ''))
    imperative = format_latex(bases.get('imperative', ''))
    
    forms_list = []
    if irrealis:
        forms_list.append(irrealis)
    if past:
        forms_list.append(past)
    if realis:
        forms_list.append(realis)
    if imperative:
        forms_list.append(imperative)
        
    if forms_list:
        forms_str = "(" + ", ".join([f"\\textit{{{f}}}" for f in forms_list]) + ")"
    else:
        forms_str = ""
    
    meanings = stem.get('meanings', [])
    if not meanings and stem.get('meaning_en'):
        meanings = [{
            'meaning_en': stem.get('meaning_en', ''),
            'meaning_he': stem.get('meaning_he', ''),
        }]

    meaning_strs = []
    for meaning_entry in meanings:
        meaning = format_latex(meaning_entry.get('meaning_en', '')).strip()
        if meaning and meaning != "to":
            if not meaning.startswith("to ") and not meaning.startswith("to"):
                meaning = "to " + meaning
            transitivity = meaning_entry.get('transitivity', '')
            telicity = meaning_entry.get('telicity', '')
            label = ""
            if transitivity == "transitive":
                label = "(tr.)"
            elif transitivity == "intransitive":
                if telicity == "telic":
                    label = "(intr., tel.)"
                elif telicity == "atelic":
                    label = "(intr., atel.)"
                else:
                    label = "(intr.)"
            if label:
                meaning_strs.append(rf"\textbf{{{meaning} {label}}}")
            else:
                meaning_strs.append(rf"\textbf{{{meaning}}}")
    
    parts = []
    if cls_str: parts.append(cls_str)
    if pretendant_str: parts.append(pretendant_str)
    if forms_str: parts.append(forms_str)
    if meaning_strs:
        parts.append("; ".join(meaning_strs))
    
    stem_out = " ".join(parts)

    idioms = stem.get('idioms', [])
    if idioms:
        idiom_parts = [format_idiom(idiom) for idiom in idioms]
        stem_out += r"\\[0.15em]" + "\n" + r"\hspace*{1em}$\Diamond$ " + "; ".join(idiom_parts)

    phrases = stem.get('phrases', [])
    if phrases:
        phrase_parts = []
        for phrase in phrases:
            ld = format_latex(phrase.get('lishan_didan', ''))
            en = format_latex(phrase.get('meaning_en', ''))
            phrase_parts.append(rf"\textit{{{ld}}} {en}")
        stem_out += r"\\[0.15em]" + "\n" + r"\hspace*{1em}$\circ$ " + "; ".join(phrase_parts)
    
    examples = stem.get('examples', [])
    if examples:
        ex_parts = []
        for ex in examples:
            ld = format_latex(ex.get('lishan_didan', ''))
            en = format_latex(ex.get('meaning_en', ''))
            ex_parts.append(rf"\textit{{{ld}}} {en}")
        stem_out += r"\\[0.15em]" + "\n" + r"\hspace*{1em}\textbar{} " + "; ".join(ex_parts)

    words = stem.get('words', [])
    if words:
        for word in words:
            forms = word.get('forms', {})
            headword = ""
            extra_forms = []
            if forms:
                if forms.get('ms'):
                    headword = format_latex(forms['ms'])
                    if forms.get('fs'):
                        extra_forms.append(rf"fs. \textit{{{format_latex(forms['fs'])}}}")
                    if forms.get('pl'):
                        extra_forms.append(rf"pl. \textit{{{format_latex(forms['pl'])}}}")
                elif forms.get('sg'):
                    headword = format_latex(forms['sg'])
                    if forms.get('pl'):
                        extra_forms.append(rf"pl. \textit{{{format_latex(forms['pl'])}}}")
                else:
                    for k, v in forms.items():
                        if not v:
                            continue
                        if not headword:
                            headword = format_latex(v)
                        else:
                            extra_forms.append(rf"{k}. \textit{{{format_latex(v)}}}")
            elif word.get('lishan_didan'):
                headword = format_latex(word.get('lishan_didan', ''))

            w_parts = []
            if headword:
                w_parts.append(rf"\textit{{{headword}}}")
            if extra_forms:
                w_parts.append("(" + ", ".join(extra_forms) + ")")
            pos = format_pos(word.get('pos', ''), word.get('gender', ''))
            if pos:
                w_parts.append(format_latex(pos))
            w_meanings = word.get('meanings', [])
            if not w_meanings and word.get('meaning_en'):
                w_meanings = [word]
            wm_strs = [rf"\textbf{{{format_latex(m.get('meaning_en', '')).strip()}}}" for m in w_meanings if m.get('meaning_en', '').strip()]
            if wm_strs:
                w_parts.append("; ".join(wm_strs))

            if w_parts:
                stem_out += r"\\[0.15em]" + "\n" + r"\hspace*{1em}-- " + " ".join(w_parts)

    return stem_out

VOWEL_BASE = str.maketrans('āēīōūáéíóúăĕĭŏŭ', 'aeiouaeiouaeiou')

def get_initial(root):
    clean = root.replace('\u0306', '').replace('\u0301', '').translate(VOWEL_BASE)
    if clean.startswith('+') and len(clean) > 1:
        return clean[0:2]
    elif len(clean) > 0:
        return clean[0]
    return ""

def main():
    with open('roots.yaml', 'r') as f:
        data = yaml.safe_load(f)
        
    def normalize_data(item):
        if isinstance(item, str):
            return unicodedata.normalize('NFC', item)
        elif isinstance(item, list):
            return [normalize_data(x) for x in item]
        elif isinstance(item, dict):
            return {normalize_data(k): normalize_data(v) for k, v in item.items()}
        return item
        
    data = normalize_data(data)

        
    preamble = [
        r"\documentclass[11pt]{article}",
        r"\usepackage{fontspec}",
        r"\usepackage{amssymb}",
        r"\setmainfont{Charis SIL}",
        r"\usepackage{parskip}",
        r"\usepackage{titlesec}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage{tabto}",
        r"",
        r"% Semantic styling for part and sections",
        r"\titleformat{\section}{\normalfont\Large\bfseries\itshape}{\thesection}{}{}",
        r"",
        r"% Semantic command for glossary entries",
        r"\linespread{1.15}\selectfont",
        r"\newlength{\headwd}",
        rf"\newcommand{{\glossentry}}[2]{{\par\hangindent={TAB_LENGTH}em\hangafter=1\noindent\settowidth{{\headwd}}{{#1}}\ifdim\headwd>{TAB_LENGTH - 0.5}em #1\hspace{{1em}}#2\else\makebox[{TAB_LENGTH}em][l]{{#1}}#2\fi\par\vspace{{0.7em}}}}",
        r"",
        r"\begin{document}",
        r"",
    ]

    roots_latex = list(preamble) + [
        r"\part*{GLOSSARY OF ROOTS}",
        r"",
        r"Entries are arranged by roots. The irrealis, past, realis and imperative base",
        r"forms are given for each stem, followed by derived words.",
        r""
    ]
    
    alphabet = [
        '∅', '+∅', 'a', '+a', 'b', '+b', 'c', '+c', 'č', '+č', 'd', '+d', 'e', '+e', 
        'ə', '+ə', 'f', '+f', 'g', '+g', 'ġ', '+ġ', 'h', '+h', 'i', '+i', 'j', '+j',
        'k', '+k', 'l', '+l', 'm', '+m', 'n', '+n', 'o', '+o', 'p', '+p', 'q', '+q',
        'r', '+r', 's', '+s', 'ṣ', '+ṣ', 'š', '+š', 't', '+t', 'u', '+u', 'v', '+v',
        'w', '+w', 'x', '+x', 'y', '+y', 'z', '+z', 'ž', '+ž'
    ]
    
    alpha_dict = {ch: idx for idx, ch in enumerate(alphabet)}
    
    tokens = sorted(alphabet, key=len, reverse=True)
    pattern = '|'.join(map(re.escape, tokens))
    regex = re.compile(f'({pattern}|.)')

    def sort_key(item):
        root = item.get('root', '').replace('\u0306', '').replace('\u0301', '').translate(VOWEL_BASE)
        res = []
        for match in regex.finditer(root):
            tok = match.group(1)
            if tok in alpha_dict:
                res.append(alpha_dict[tok])
            else:
                res.append(999 + ord(tok))
        return tuple(res)
        
    data.sort(key=sort_key)
    
    current_initial = None
    
    from collections import Counter
    root_counts = Counter(item.get('root', '') for item in data)
    root_seen = {}
    irrealis_entries = []
    
    words_data = []
    if os.path.exists('words.yaml'):
        with open('words.yaml', 'r', encoding='utf-8') as wf:
            words_data = yaml.safe_load(wf) or []
        words_data = normalize_data(words_data)

    def parse_root_ref(r_str):
        s = r_str.strip()
        cls = None
        m_cls = re.match(r'^(Q-III|Q-I|III|I)\s+(.+)$', s)
        if m_cls:
            cls, s = m_cls.group(1), m_cls.group(2).strip()
        rom = None
        m_rom = re.match(r'^(.*?)\s*\(([ivxlcdm]+)\)\s*$', s, re.I)
        if m_rom:
            s, rom = m_rom.group(1).strip(), m_rom.group(2).lower()
        return cls, s, rom

    words_by_root = {}
    for w_item in words_data:
        w_root = (w_item.get('root') or '').strip()
        if w_root:
            _, base_r, rom = parse_root_ref(w_root)
            words_by_root.setdefault((base_r, rom), []).append(w_item)

    for item in data:
        raw_root = item.get('root', '')
        root = format_latex(raw_root)
        
        initial = get_initial(raw_root)
        
        if initial != current_initial:
            current_initial = initial
            display_initial = format_latex(initial)
            roots_latex.append(rf"\section*{{{display_initial}}}")
        
        stems = item.get('stems', [])
        
        stem_strs = []
        for stem in stems:
            stem_strs.append(process_stem(stem))
            
        joined_stems = (r"\\[0.4em]" + "\n").join(stem_strs)

        root_seen[raw_root] = root_seen.get(raw_root, 0) + 1
        occ_roman = to_roman(root_seen[raw_root])

        matched_words = list(words_by_root.get((raw_root, occ_roman), []))
        if root_counts[raw_root] == 1:
            matched_words.extend(words_by_root.get((raw_root, None), []))
        elif root_seen[raw_root] == 1:
            matched_words.extend(words_by_root.get((raw_root, None), []))

        for dw in matched_words:
            dw_parts = []
            dw_ld = format_latex(dw.get('word', '')).strip()
            if dw_ld:
                dw_parts.append(rf"\textit{{{dw_ld}}}")
            dw_pos = format_pos(dw.get('pos', ''), dw.get('gender', ''), dw.get('number', ''))
            if dw_pos:
                dw_parts.append(format_latex(dw_pos))
            dw_ms = [rf"\textbf{{{format_latex(m.get('meaning_en', '')).strip()}}}" for m in dw.get('meanings', []) if m.get('meaning_en', '').strip()]
            if dw_ms:
                dw_parts.append("; ".join(dw_ms))
            if dw_parts:
                joined_stems += r"\\[0.15em]" + "\n" + r"\hspace*{1em}-- " + " ".join(dw_parts)
                
        if root_counts[raw_root] > 1:
            root_display = rf"{{$\sqrt{{\mbox{{{root}}}}}$}} ({occ_roman})"
        else:
            root_display = rf"{{$\sqrt{{\mbox{{{root}}}}}$}}"
            
        roots_latex.append(rf"\glossentry{{{root_display}}}{{{joined_stems}}}")

        for stem in stems:
            irr = stem.get('bases', {}).get('irrealis', '').strip()
            if irr:
                cls = stem.get('class', '')
                irrealis_entries.append((irr, cls, root_display))

    general_entries = []
    for w_item in words_data:
        general_entries.append(('word', w_item.get('word', ''), w_item))
    # for irr, cls, root_display in irrealis_entries:
    #     general_entries.append(('verb', irr, (cls, root_display)))

    general_latex = list(preamble) + [
        r"\part*{GENERAL GLOSSARY}",
        r"",
        r"Words and nominal idioms.",
        r""
    ]

    if general_entries:
        general_entries.sort(key=lambda it: (sort_key({'root': it[1]}), 0 if it[0] == 'word' else 1))
        word_counts = Counter(it[1] for it in general_entries)
        word_seen = {}

        word_initial = None
        for kind, raw_word, payload in general_entries:
            w_init = get_initial(raw_word)
            if w_init != word_initial:
                word_initial = w_init
                general_latex.append(rf"\section*{{{format_latex(w_init)}}}")

            word_seen[raw_word] = word_seen.get(raw_word, 0) + 1
            if word_counts[raw_word] > 1:
                word_display = rf"\textit{{{format_latex(raw_word)}}} ({to_roman(word_seen[raw_word])})"
            else:
                word_display = rf"\textit{{{format_latex(raw_word)}}}"

            if kind == 'verb':
                cls, rdisp = payload
                ref_str = rf"\textbf{{{cls}}} {rdisp}" if cls else rdisp
                body = r"v. $\rightarrow$ " + ref_str
                general_latex.append(rf"\glossentry{{{word_display}}}{{{body}}}")
                continue

            w_item = payload
            top_pos = w_item.get('pos', '')
            top_gender = w_item.get('gender', '')
            top_number = w_item.get('number', '')

            w_forms = w_item.get('forms', {})
            top_forms_str = ""
            if isinstance(w_forms, dict) and w_forms:
                f_bits = []
                ordered_keys = ('masculine_singular', 'ms', 'feminine_singular', 'fs', 'singular', 'sg', 'plural', 'pl', 'construct')
                for fk in ordered_keys:
                    if w_forms.get(fk):
                        f_val = format_latex(w_forms[fk])
                        if fk == 'construct' and not f_val.endswith('-'):
                            f_val += '-'
                        f_bits.append(rf"{FORM_ABBREV[fk]} \textit{{{f_val}}}")
                for fk, fv in w_forms.items():
                    if fk not in ordered_keys and fv:
                        f_bits.append(rf"{fk}. \textit{{{format_latex(fv)}}}")
                if f_bits:
                    top_forms_str = "(" + ", ".join(f_bits) + ")"

            meanings = w_item.get('meanings', [])
            groups = []
            group_index = {}
            for m in meanings:
                en = format_latex(m.get('meaning_en', '')).strip()
                if not en:
                    continue
                m_pos = m.get('pos', top_pos)
                m_gender = m.get('gender', top_gender if m_pos == top_pos else '')
                m_number = m.get('number', top_number if m_pos == top_pos else '')
                key = (m_pos, m_gender, m_number)
                if key not in group_index:
                    group_index[key] = len(groups)
                    groups.append({'pos': m_pos, 'gender': m_gender, 'number': m_number, 'meanings': []})
                groups[group_index[key]]['meanings'].append(rf"\textbf{{{en}}}")

            if not groups:
                head_parts = []
                pos_str = format_pos(top_pos, top_gender, top_number)
                if pos_str:
                    head_parts.append(format_latex(pos_str))
                if top_forms_str:
                    head_parts.append(top_forms_str)
                body = " ".join(head_parts)
            else:
                group_lines = []
                for idx, g in enumerate(groups):
                    g_parts = []
                    pos_str = format_pos(g['pos'], g['gender'], g['number'])
                    if pos_str:
                        g_parts.append(format_latex(pos_str))
                    if idx == 0 and top_forms_str:
                        g_parts.append(top_forms_str)
                    g_parts.append("; ".join(g['meanings']))
                    group_lines.append(" ".join(g_parts))
                body = (r"\\[0.4em]" + "\n").join(group_lines)

            w_root = (w_item.get('root') or '').strip()
            w_pattern = (w_item.get('pattern') or '').strip()
            if w_root:
                r_cls, base_r, rom = parse_root_ref(w_root)
                r_tex = rf"$\sqrt{{\mbox{{{format_latex(base_r, smallcaps=False)}}}}}$"
                if r_cls:
                    r_tex = rf"\textbf{{{r_cls}}} " + r_tex
                if rom:
                    r_tex += f" ({rom})"
                if w_pattern:
                    body += rf" ({r_tex}, \textit{{{format_latex(w_pattern, smallcaps=False)}}})"
                else:
                    body += rf" ({r_tex})"
            elif w_pattern:
                body += rf" (\textit{{{format_latex(w_pattern, smallcaps=False)}}})"

            w_from = (w_item.get('from') or '').strip()
            if w_from:
                body += rf" ($<$ \textit{{{format_latex(w_from, smallcaps=False)}}})"

            for form in w_item.get('derived', []):
                f_parts = []
                f_ld = format_latex(form.get('lishan_didan', '')).strip()
                if f_ld:
                    f_parts.append(rf"\textit{{{f_ld}}}")
                f_pos = format_pos(form.get('pos', ''), form.get('gender', ''), form.get('number', ''))
                if f_pos:
                    f_parts.append(format_latex(f_pos))
                f_meanings = form.get('meanings', [])
                if not f_meanings and form.get('meaning_en'):
                    f_meanings = [form]
                fm_strs = [rf"\textbf{{{format_latex(m.get('meaning_en', '')).strip()}}}" for m in f_meanings if m.get('meaning_en', '').strip()]
                if fm_strs:
                    f_parts.append("; ".join(fm_strs))
                if f_parts:
                    body += r"\\[0.15em]" + "\n" + r"\hspace*{1em}-- " + " ".join(f_parts)

            idioms = w_item.get('idioms', [])
            if idioms:
                idiom_parts = [format_idiom(id_it) for id_it in idioms]
                body += r"\\[0.15em]" + "\n" + r"\hspace*{1em}$\Diamond$ " + "; ".join(idiom_parts)

            phrases = w_item.get('phrases', [])
            if phrases:
                phrase_parts = [
                    rf"\textit{{{format_latex(ph.get('lishan_didan', ''))}}} {format_latex(ph.get('meaning_en', ''))}"
                    for ph in phrases
                ]
                body += r"\\[0.15em]" + "\n" + r"\hspace*{1em}$\circ$ " + "; ".join(phrase_parts)

            examples = w_item.get('examples', [])
            if examples:
                ex_parts = [
                    rf"\textit{{{format_latex(ex.get('lishan_didan', ''))}}} {format_latex(ex.get('meaning_en', ''))}"
                    for ex in examples
                ]
                body += r"\\[0.15em]" + "\n" + r"\hspace*{1em}\textbar{} " + "; ".join(ex_parts)

            general_latex.append(rf"\glossentry{{{word_display}}}{{{body}}}")

    roots_latex.append(r"\end{document}")
    general_latex.append(r"\end{document}")

    targets = [
        ('roots-glossary', roots_latex),
        ('general-glossary', general_latex),
    ]

    for stem_name, content in targets:
        tex_file = f'{stem_name}.tex'
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(content))

    if shutil.which('xelatex'):
        for stem_name, _ in targets:
            subprocess.run(['xelatex', '-interaction=nonstopmode', f'{stem_name}.tex'], stdin=subprocess.DEVNULL, check=True)
            for ext in ('.aux', '.log', '.tex'):
                aux_file = f'{stem_name}{ext}'
                if os.path.exists(aux_file):
                    os.remove(aux_file)
    else:
        print("Warning: xelatex not found in PATH; generated roots-glossary.tex and general-glossary.tex only.", file=sys.stderr)

if __name__ == '__main__':
    main()
