#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convierte un test en texto (P1., A) B) C) D), Correcta: X) a formato Moodle GIFT.

Uso:
  python convert.py input.txt -o output.gift
"""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class Question:
    name: str
    prompt: str
    options: List[Tuple[str, str]]  # (letter, text)
    correct_letter: str


QUESTION_START_RE = re.compile(r"^(::\s*(P\d+)\s*::|P(\d+)\.)\s*(.*)$", re.IGNORECASE)
OPTION_RE = re.compile(r"^([A-Da-d])\)\s*(.+?)\s*$")
CORRECT_RE = re.compile(r"^(?:✅\s*)?(?:Correcta|Respuesta\s+correcta)\s*:\s*([A-Da-d])\s*$", re.IGNORECASE)


def parse_questions(text: str) -> List[Question]:
    lines = [ln.rstrip("\n") for ln in text.splitlines()]
    i = 0
    questions: List[Question] = []

    def skip_blanks(idx: int) -> int:
        while idx < len(lines) and lines[idx].strip() == "":
            idx += 1
        return idx

    i = skip_blanks(i)
    while i < len(lines):
        m = QUESTION_START_RE.match(lines[i].strip())
        if not m:
            raise ValueError(f"No encuentro inicio de pregunta en línea {i+1}: {lines[i]!r}")

        pnum = m.group(2) or (m.group(3) and f"P{m.group(3)}")
        if not pnum:
            raise ValueError(f"No pude determinar número de pregunta en línea {i+1}: {lines[i]!r}")
        name = pnum.upper()

        first_prompt = (m.group(4) or "").strip()
        prompt_lines = [first_prompt] if first_prompt else []

        i += 1

        # Enunciado (puede tener varias líneas) hasta que empiecen opciones A)...
        while i < len(lines):
            ln = lines[i].strip()
            if ln == "":
                i += 1
                continue
            if OPTION_RE.match(ln):
                break
            if QUESTION_START_RE.match(ln):
                raise ValueError(f"Pregunta {name}: faltan opciones antes de la línea {i+1}")
            prompt_lines.append(ln)
            i += 1

        if not prompt_lines:
            raise ValueError(f"Pregunta {name}: enunciado vacío.")

        # Opciones
        options: List[Tuple[str, str]] = []
        while i < len(lines):
            ln = lines[i].strip()
            if ln == "":
                i += 1
                continue
            om = OPTION_RE.match(ln)
            if not om:
                break
            letter = om.group(1).upper()
            opt_text = om.group(2).strip()
            options.append((letter, opt_text))
            i += 1

        if len(options) < 2:
            raise ValueError(f"Pregunta {name}: necesito al menos 2 opciones, encontré {len(options)}.")

        # Línea "Correcta: X"
        correct_letter: Optional[str] = None
        while i < len(lines):
            ln = lines[i].strip()
            if ln == "":
                i += 1
                continue
            if QUESTION_START_RE.match(ln):
                break
            cm = CORRECT_RE.match(ln)
            if cm:
                correct_letter = cm.group(1).upper()
                i += 1
                break
            i += 1

        if not correct_letter:
            raise ValueError(f"Pregunta {name}: no encontré línea 'Correcta: X'.")

        letters = [l for (l, _) in options]
        if correct_letter not in letters:
            raise ValueError(f"Pregunta {name}: correcta {correct_letter} no está en opciones {letters}.")

        prompt = " ".join(prompt_lines).strip()
        questions.append(Question(name=name, prompt=prompt, options=options, correct_letter=correct_letter))
        i = skip_blanks(i)

    return questions


def to_gift(questions: List[Question]) -> str:
    out_lines: List[str] = []
    for q in questions:
        out_lines.append(f"::{q.name}::")
        out_lines.append(q.prompt)
        out_lines.append("{")
        for letter, text in q.options:
            prefix = "=" if letter == q.correct_letter else "~"
            out_lines.append(f"{prefix}{text}")
        out_lines.append("}")
        out_lines.append("")  # línea en blanco entre preguntas
    return "\n".join(out_lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Convierte test (A/B/C/D + Correcta) a Moodle GIFT.")
    ap.add_argument("input", type=Path, help="Archivo .txt de entrada (UTF-8)")
    ap.add_argument("-o", "--output", type=Path, required=True, help="Archivo .gift de salida")
    args = ap.parse_args()

    text = args.input.read_text(encoding="utf-8")
    questions = parse_questions(text)
    gift = to_gift(questions)
    args.output.write_text(gift, encoding="utf-8")

    print(f"OK: {len(questions)} preguntas -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
