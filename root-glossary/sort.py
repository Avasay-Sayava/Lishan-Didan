import yaml
import unicodedata
import re

class MyDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)

def str_presenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(str, str_presenter, Dumper=MyDumper)

def main():
    print("Loading roots.yaml...")
    with open('roots.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    print("Normalizing and standardizing structure...")
    def normalize_data(item):
        if isinstance(item, str):
            return unicodedata.normalize('NFC', item)
        elif isinstance(item, list):
            return [normalize_data(x) for x in item]
        elif isinstance(item, dict):
            # Enforce a specific key order for consistency
            ordered_dict = {}
            for k in ['root', 'class', 'pretendant', 'transitivity', 'telicity', 'bases', 'forms', 'meanings', 'lishan_didan', 'meaning_en', 'meaning_he', 'idioms', 'phrases', 'examples']:
                if k in item:
                    ordered_dict[k] = normalize_data(item[k])
            for k in item.keys():
                if k not in ordered_dict:
                    ordered_dict[k] = normalize_data(item[k])
            return ordered_dict
        return item

    data = normalize_data(data)

    print("Sorting roots...")
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

    print("Writing formatted yaml...")
    import io
    stream = io.StringIO()
    yaml.dump(data, stream, Dumper=MyDumper, allow_unicode=True, sort_keys=False, width=1000)
    
    text = stream.getvalue()
    
    # Post-process to remove quotes from dictionary keys and add blank lines
    text = re.sub(r'^(\s*)- "(.*?)":', r'\1- \2:', text, flags=re.MULTILINE)
    text = re.sub(r'^(\s*)"(.*?)":', r'\1\2:', text, flags=re.MULTILINE)
    text = re.sub(r'\n- root:', r'\n\n- root:', text)
    text = re.sub(r'([^\n:]+)\n(\s*)- class:', r'\1\n\n\2- class:', text)
    
    # Ensure file ends with exactly one newline
    text = text.strip() + '\n'

    with open('roots.yaml', 'w', encoding='utf-8') as f:
        f.write(text)
        
    print("Done! roots.yaml has been sorted, normalized, and correctly indented.")

if __name__ == '__main__':
    main()
