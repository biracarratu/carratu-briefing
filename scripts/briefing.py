#!/usr/bin/env python3
"""Briefing com escuta ativa: roteiro de perguntas, registro das respostas e régua de clareza.

Uso:
  python3 briefing.py types                                      # tipos disponíveis
  python3 briefing.py questions --type campanha [--lang pt]      # roteiro (núcleo + campos do tipo), por bloco
  python3 briefing.py init --type campanha --out briefing_data --project "Nome" --client "Cliente"
  python3 briefing.py score briefing_data [--today AAAA-MM-DD]   # nota de clareza, lacunas e próximas perguntas

briefing_data/briefing.json guarda as respostas (answers: o que a pessoa disse, nas palavras dela) e a leitura do
Claude (understood: o que eu entendi, para devolver e confirmar). score gera metrics.json e auto_sections.json.

Active-listening briefing: interview script, answer log and clarity score.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from carratu_data import dump, parse_date  # noqa

TPL = os.path.join(HERE, "..", "references", "templates.json")
BLOCKS = {"pt": {"negocio": "Negócio", "publico": "Público", "mensagem": "Mensagem e prova", "entrega": "Entrega e métricas",
                 "restricoes": "Prazo, orçamento e restrições", "aprovacao": "Aprovação"},
          "en": {"negocio": "Business", "publico": "Audience", "mensagem": "Message and proof", "entrega": "Deliverables and metrics",
                 "restricoes": "Timing, budget and constraints", "aprovacao": "Approval"}}
L = {"pt": {"q": "Pergunta", "a": "Resposta", "st": "Status", "score": "Clareza por bloco", "gaps": "Lacunas e próximas perguntas",
            "field": "Campo", "issue": "O que falta", "next": "Pergunte", "empty": "sem resposta", "vague": "termo vago: {t}",
            "number": "falta número", "date": "falta data", "aud": "público genérico", "brief": "O briefing", "kpis": "Clareza do briefing",
            "answered": "Respondidos", "specific": "Específicos", "open": "Em aberto", "flags": "Termos vagos", "understood": "O que eu entendi",
            "conf": "Confirmado pelo cliente", "notconf": "A confirmar"},
     "en": {"q": "Question", "a": "Answer", "st": "Status", "score": "Clarity by block", "gaps": "Gaps and next questions",
            "field": "Field", "issue": "Missing", "next": "Ask", "empty": "no answer", "vague": "vague term: {t}",
            "number": "needs a number", "date": "needs a date", "aud": "generic audience", "brief": "The brief", "kpis": "Brief clarity",
            "answered": "Answered", "specific": "Specific", "open": "Open", "flags": "Vague terms", "understood": "What I understood",
            "conf": "Confirmed by client", "notconf": "To be confirmed"}}
CRITICAL = {"objetivo_negocio", "publico", "metricas", "prazo", "orcamento", "aprovacao"}
MONTHS = r"(jan|fev|feb|mar|abr|apr|mai|may|jun|jul|ago|aug|set|sep|out|oct|nov|dez|dec)[a-z]*"


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(c) != "Mn")


def fields(tpl, typ):
    return tpl["core"] + tpl["types"][typ]["fields"]


def check(f, ans, vague, lang):
    t = L[lang]
    a = (ans or "").strip()
    if not a or fold(a).strip(" .!") in ("a definir", "tbd", "nao sei", "not sure", "n/a", "-", "depois vemos", "a combinar"):
        return 0, [t["empty"]]
    issues = []
    fa = fold(a)
    hits = [v for v in vague if re.search(r"(?<![a-z])" + re.escape(fold(v)) + r"(?![a-z])", fa)]
    if hits:
        issues.append(t["vague"].format(t=", ".join(hits[:3])))
    for n in f.get("needs", []):
        if n == "number" and not re.search(r"\d", a):
            issues.append(t["number"])
        if n == "date" and not (re.search(r"\d{1,2}/\d{1,2}", a) or re.search(r"\b20\d\d\b", a) or re.search(MONTHS, fa)
                                or re.search(r"\d+\s*(dias|semanas|meses|days|weeks|months)", fa)):
            issues.append(t["date"])
        if n == "specific_audience" and (len(a) < 40 or hits):
            issues.append(t["aud"])
    if len(a) < 12:
        issues.append(t["empty"] if not a else ("resposta curta" if lang == "pt" else "short answer"))
    score = 100 if not issues else max(10, 100 - 35 * len(issues))
    return score, issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["types", "questions", "init", "score"])
    ap.add_argument("dir", nargs="?")
    ap.add_argument("--type", default="campanha")
    ap.add_argument("--lang", default="pt")
    ap.add_argument("--out", default="briefing_data")
    ap.add_argument("--project", default="")
    ap.add_argument("--client", default="")
    ap.add_argument("--today", default=None)
    a = ap.parse_args()
    tpl = json.load(open(TPL, encoding="utf-8"))
    lang = a.lang if a.lang in L else "pt"

    if a.cmd == "types":
        print(json.dumps({k: v["name"][lang] for k, v in tpl["types"].items()}, ensure_ascii=False, indent=1))
        return
    if a.cmd == "questions":
        out = {}
        for f in fields(tpl, a.type):
            out.setdefault(BLOCKS[lang][f["block"]], []).append({"id": f["id"], "q": f["q"][lang], "why": f["why"][lang],
                                                                  "required": f["required"], "probes": f["probes"][lang]})
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    if a.cmd == "init":
        os.makedirs(a.out, exist_ok=True)
        p = os.path.join(a.out, "briefing.json")
        if os.path.exists(p):
            raise SystemExit(f"{p} já existe.")
        b = {"type": a.type, "lang": lang, "project": a.project, "client": a.client, "date": (a.today or date.today().isoformat()),
             "answers": {f["id"]: "" for f in fields(tpl, a.type)}, "understood": {f["id"]: "" for f in fields(tpl, a.type)},
             "confirmed": False, "notes": ""}
        json.dump(b, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(p)
        return

    d = a.dir or a.out
    b = json.load(open(os.path.join(d, "briefing.json"), encoding="utf-8"))
    lang = b.get("lang", lang)
    t = L[lang]
    fl = fields(tpl, b["type"])
    vague = tpl["vague_terms"][lang]
    res, by_block, gaps, flags = [], {}, [], 0
    num = den = 0
    for f in fl:
        ans = b["answers"].get(f["id"], "")
        s, issues = check(f, ans, vague, lang)
        w = 3 if f["required"] else 1
        num += s * w
        den += w
        flags += sum(1 for i in issues if i.startswith(t["vague"].split("{")[0]))
        st = "pass" if s == 100 else "warn" if s else ("fail" if f["required"] else "na")
        res.append({"id": f["id"], "block": f["block"], "score": s, "issues": issues, "status": st})
        by_block.setdefault(f["block"], []).append(s)
        if issues and (f["required"] or ans):
            gaps.append([f["q"][lang], "; ".join(issues), f["probes"][lang][0] if f["probes"][lang] else ""])
    clarity = round(num / den) if den else 0
    # Regra de prontidão: com campo crítico aberto, o briefing não está pronto para produzir (nota máxima 74)
    critical_open = [r["id"] for r in res if r["id"] in CRITICAL and r["score"] < 100]
    if critical_open:
        clarity = min(clarity, 74)
    ready = clarity >= 80 and not critical_open
    m = re.search(r"\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}", b["answers"].get("prazo", "") or "")
    deadline = parse_date(m.group(0)) if m else None
    days_left = (deadline - (parse_date(a.today) if a.today else date.today())).days if deadline else None
    metrics = {"clarity": clarity, "fields": res, "answered": sum(1 for r in res if r["score"] > 0),
               "specific": sum(1 for r in res if r["score"] == 100), "total": len(res), "vague_flags": flags,
               "open_required": sum(1 for r, f in zip(res, fl) if f["required"] and r["score"] < 100), "days_to_deadline": days_left,
               "confirmed": b.get("confirmed", False), "critical_open": critical_open, "ready_to_produce": ready}
    dump(metrics, os.path.join(d, "metrics.json"))

    S = [{"title": t["kpis"], "blocks": [{"type": "kpis", "items": [
        {"label": t["answered"], "value": f"{metrics['answered']}/{len(res)}"},
        {"label": t["specific"], "value": f"{metrics['specific']}/{len(res)}", "status": "pass" if metrics["specific"] >= 0.8 * len(res) else "warn"},
        {"label": t["open"], "value": str(metrics["open_required"]), "status": "fail" if metrics["open_required"] > 2 else "warn" if metrics["open_required"] else "pass"},
        {"label": t["flags"], "value": str(flags), "status": "warn" if flags else "pass"}]},
        {"type": "scores", "items": [{"name": BLOCKS[lang][k], "score": round(sum(v) / len(v))} for k, v in by_block.items()]}]}]
    for blk in BLOCKS[lang]:
        rows = []
        for f, r in zip(fl, res):
            if f["block"] != blk:
                continue
            ans = b["answers"].get(f["id"], "") or f"({t['empty']})"
            und = b.get("understood", {}).get(f["id"], "")
            rows.append([f"**{f['q'][lang]}**", ans + (f"\n\n**{t['understood']}:** {und}" if und else ""), r["status"]])
        if rows:
            S.append({"title": f"{t['brief']}: {BLOCKS[lang][blk]}", "blocks": [{"type": "table", "header": [t["q"], t["a"], t["st"]],
                      "rows": rows, "widths": [5, 10, 2], "status_col": 2, "size": 9}]})
    if gaps:
        S.append({"title": t["gaps"], "page_break_before": True, "blocks": [{"type": "table", "header": [t["field"], t["issue"], t["next"]],
                  "rows": gaps, "widths": [6, 4.5, 6.5], "size": 8.5}]})
    dump({"sections": S}, os.path.join(d, "auto_sections.json"))
    print(json.dumps({**{k: v for k, v in metrics.items() if k != "fields"},
                      "gaps": [{"field": g[0], "issue": g[1], "ask": g[2]} for g in gaps]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
