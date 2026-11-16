import yaml
import sys
import os
import re
import shutil
import subprocess
import unicodedata

TAB_LENGTH = 5.5

def superscript(text):
    return r"\textsuperscript{\textsubscript{" + text + r"}}\!"

def subscript(text):
    return r"\textsubscript{" + text + r"}"

def format_latex(text):
    if not text:
        return ""

    import re
    # 1. Turn ALL CAPS abbreviations (like PRO, NV, 3M) into small caps
    text = re.sub(r'\b([A-Z0-9]{2,})\b', lambda m: r"{\small \textnormal{\textsc{" + m.group(1).lower() + r"}}}", text)
    
    # 2. Turn _i into a subscript using the user's custom subscript format
    text = re.sub(r'_([a-zA-Z0-9]+)', lambda m: subscript(r"\textnormal{" + m.group(1) + r"}"), text)

    text = text.replace("&", r"\&")
    text = text.replace("~", r"\textasciitilde{}")
    text = text.replace("+", superscript("+"))
    text = text.replace("/∅", superscript("∅"))

    return text

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
                label = "(tr.) "
            elif transitivity == "intransitive":
                if telicity == "telic":
                    label = "(intr., tel.) "
                elif telicity == "atelic":
                    label = "(intr., atel.) "
                else:
                    label = "(intr.) "
            meaning_strs.append(rf"{label}\textbf{{{meaning}}}")
    
    parts = []
    if cls_str: parts.append(cls_str)
    if pretendant_str: parts.append(pretendant_str)
    if forms_str: parts.append(forms_str)
    if meaning_strs:
        parts.append("; ".join(meaning_strs))
    
    stem_out = " ".join(parts)

    idioms = stem.get('idioms', [])
    if idioms:
        idiom_parts = []
        for idiom in idioms:
            ld = format_latex(idiom.get('lishan_didan', ''))
            en = format_latex(idiom.get('meaning_en', ''))
            idiom_parts.append(rf"\textit{{{ld}}} \textbf{{{en}}}")
        stem_out += r" $\Diamond$ " + "; ".join(idiom_parts)

    phrases = stem.get('phrases', [])
    if phrases:
        phrase_parts = []
        for phrase in phrases:
            ld = format_latex(phrase.get('lishan_didan', ''))
            en = format_latex(phrase.get('meaning_en', ''))
            phrase_parts.append(rf"\textit{{{ld}}} {en}")
        stem_out += r" $\circ$ " + "; ".join(phrase_parts)
    
    examples = stem.get('examples', [])
    if examples:
        ex_parts = []
        for ex in examples:
            ld = format_latex(ex.get('lishan_didan', ''))
            en = format_latex(ex.get('meaning_en', ''))
            ex_parts.append(rf"\textit{{{ld}}} {en}")
        stem_out += r" \textbar{} " + "; ".join(ex_parts)

    return stem_out

def get_initial(root):
    if root.startswith('+') and len(root) > 1:
        return root[0:2]
    elif len(root) > 0:
        return root[0]
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

        
    latex_out = [
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
        rf"\newcommand{{\entry}}[1]{{\par\hangindent={TAB_LENGTH}em\hangafter=1\noindent#1\par\vspace{{0.4em}}}}",
        r"",
        r"\begin{document}",
        r"",
        r"\part*{GLOSSARY OF VERBS}",
        r"",
        r"Verbs are arranged by roots. The irrealis, past, realis and imperative base",
        r"forms are given for each root.",
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
        root = item.get('root', '')
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
    
    for item in data:
        raw_root = item.get('root', '')
        root = format_latex(raw_root)
        
        initial = get_initial(raw_root)
        
        if initial != current_initial:
            current_initial = initial
            display_initial = format_latex(initial)
            latex_out.append(rf"\section*{{{display_initial}}}")
        
        stems = item.get('stems', [])
        
        stem_strs = []
        for stem in stems:
            stem_strs.append(process_stem(stem))
            
        joined_stems = ""
        for i, s in enumerate(stem_strs):
            if i > 0:
                if joined_stems.strip().endswith("."):
                    joined_stems += r"\quad " + s
                else:
                    joined_stems += r".\quad " + s
            else:
                joined_stems = s
                
        root_seen[raw_root] = root_seen.get(raw_root, 0) + 1
        
        if root_counts[raw_root] > 1:
            root_display = rf"{{$\sqrt{{\mbox{{{root}}}}}$}} ({root_seen[raw_root]})"
        else:
            root_display = rf"{{$\sqrt{{\mbox{{{root}}}}}$}}"
            
        entry_str = rf"{root_display}\tabto{{{TAB_LENGTH}em}} " + joined_stems
        latex_out.append(rf"\entry{{{entry_str}}}")
        
    latex_out.append(r"\end{document}")
    
    with open('glossary.tex', 'w', encoding='utf-8') as f:
        f.write("\n".join(latex_out))

    if shutil.which('xelatex'):
        subprocess.run(['xelatex', '-interaction=nonstopmode', 'glossary.tex'], stdin=subprocess.DEVNULL, check=True)
        for ext in ('.aux', '.log', '.tex'):
            aux_file = f'glossary{ext}'
            if os.path.exists(aux_file):
                os.remove(aux_file)
    else:
        print("Warning: xelatex not found in PATH; generated glossary.tex only.", file=sys.stderr)

if __name__ == '__main__':
    main()
