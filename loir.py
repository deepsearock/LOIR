import ast
import sys
import os
import tiktoken
import re
import openai
import difflib
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def expr_max(e):
    try:

        return re.sub(r"\s+","",ast.unparse(e))
    except Exception:
        return "E"

def stmt_max(s):
    if isinstance(s,ast.Assign):
        tgts = ",".join(re.sub(r"\s+","",ast.unparse(t)) for t in s.targets)
        return f"A{tgts}={expr_max(s.value)}"
    elif isinstance(s,ast.Return):
        return f"R{expr_max(s.value) if s.value else ''}"
    elif isinstance(s,ast.If):
        cond = expr_max(s.test)
        then = "|".join(stmt_max(st) for st in s.body)
        els = "|".join(stmt_max(st) for st in s.orelse) if s.orelse else ""
        return f"I{cond}{{{then}}}:E{els}"
    elif isinstance(s,ast.For):
        tgt = re.sub(r"\s+","",ast.unparse(s.target))
        it = expr_max(s.iter)
        bod = "|".join(stmt_max(st) for st in s.body)
        return f"F{tgt}in{it}{{{bod}}}"
    elif isinstance(s,ast.While):
        cond = expr_max(s.test)
        bod = "|".join(stmt_max(st) for st in s.body)
        return f"W{cond}{{{bod}}}"
    else:
        try:
            return re.sub(r"\s+","",ast.unparse(s))
        except Exception:
            return "s"

def func_max(f):
    args = ",".join(arg.arg for arg in f.args.args)
    bod = "|".join(stmt_max(s) for s in f.body)
    return f"{f.name}({args}){{{bod}}}"

def class_max(cls):
    bases = ",".join(re.sub(r"\s+","",ast.unparse(b)) for b in cls.bases) if cls.bases else ""
    meths = "|".join(func_max(item) for item in cls.body if isinstance(item,ast.FunctionDef))
    return f"{cls.name}({bases}){{{meths}}}"

def imp_max(tree):
    imps = []
    for node in tree.body:
        if isinstance(node,ast.Import):
            for a in node.names:
                imps.append(f"imp:{a.name}" + (f"as{a.asname}" if a.asname else ""))
        elif isinstance(node,ast.ImportFrom):
            mod = node.module if node.module else ""
            for a in node.names:
                imps.append(f"frm:{mod}imp:{a.name}" + (f"as{a.asname}" if a.asname else ""))
    return imps

def parse_file_max(fn):
    with open(fn,"r") as fp:
        code = fp.read()
    tree = ast.parse(code)
    mod = os.path.splitext(os.path.basename(fn))[0]
    imps = imp_max(tree)
    classes = []
    funcs = []
    for node in tree.body:
        if isinstance(node,ast.ClassDef):
            classes.append(class_max(node))
        elif isinstance(node,ast.FunctionDef):
            funcs.append(func_max(node))
    I = "I=" + ",".join(imps) if imps else "I="
    C = "C=" + ",".join(classes) if classes else "C="
    F = "F=" + ";".join(funcs) if funcs else "F="
    loir = f"M={mod};{I};{C};{F}"
    return re.sub(r"\s+","",loir)

def max_compress(loir):

    mapping = {
        "M=":"M:",  "I=":"I:",  "C=":"C:",  "F=":"F:",
        "imp:":"i:", "frm:":"f:",
        "assign":"A", "return":"R",
        "A":"A", "R":"R", "I":"i", "F":"f", "W":"w",
        "(":"", ")":"", "{" : "", "}": "", "," : "", ";" : "|", ":" : ":"
    }
    for k, v in mapping.items():
        loir = loir.replace(k, v)
    return loir

def count_tokens(txt, model="gpt-4"):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(txt))

def clean(txt):
    lines = txt.strip().splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines)
def extract(txt):
    m = re.search(r"```(?:python)?\n([\s\S]*?)\n```", txt)
    return m.group(1) if m else txt

def recreate(loir):
    legend = ("Legend: M:module; I:imports(i: for imp:, f: for frm:); C:classes; F:functions; "
              "A:assignment; R:return; i:if; e:else; f:for; w:while; '|' separates statements; "
              "All parentheses, braces, commas are removed.")
    prompt = ("Recreate the original Python code from the following ultra-aggressively compressed LOIR:\n\n"
              f"{loir}\n\nLegend: {legend}\n\nReconstruct full Python code with proper formatting.")
    resp = openai.chat.completions.create(model="gpt-4o",
           messages=[{"role":"user","content":prompt}], temperature=0)
    return resp.choices[0].message.content

def compare_logic(orig, rec):
    o = clean(orig)
    r = extract(clean(rec))
    try:
        oa = ast.parse(o)
        ra = ast.parse(r)
        od = ast.dump(oa, annotate_fields=False, include_attributes=False)
        rd = ast.dump(ra, annotate_fields=False, include_attributes=False)
        return difflib.SequenceMatcher(None,od,rd).ratio()*100
    except Exception as e:
        print("Logic compare error:", e)
        return 0.0

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 script.py <python_file.py>")
        sys.exit(1)
    fn = sys.argv[1]
    loir = parse_file_max(fn)
    loir = max_compress(loir)
    print("Ultra-Aggressive LOIR:\n", loir)
    print("\nLOIR tokens:", count_tokens(loir))
    with open(fn,"r") as f:
        orig = f.read()
    print("\nOriginal Code:\n", orig)
    print("\nOriginal tokens:", count_tokens(orig))
    print(f"\nPercentage of original code in LOIR: {(count_tokens(loir)/count_tokens(orig))*100:.2f}%")
    rec = recreate(loir)
    print("\nRecreated Code:\n", rec)
    print("\nRecreated tokens:", count_tokens(rec))
    sim = compare_logic(orig, rec)
    print(f"\nLogic similarity: {sim:.2f}%")
if __name__=="__main__":
    main()