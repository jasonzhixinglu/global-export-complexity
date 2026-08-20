"""Emit exports/chart_pack.tex -- a hand-editable LaTeX version of the chart pack.

The Python builder (build_chart_pack.py) holds titles and captions inside a
Python list, which is awkward to edit. This writes the same content out as a
LaTeX document whose body is plain text: one \\chartpage{title}{caption}{figure}
per page, grouped by \\sectionpage. After that the .tex is the source of truth
for the desktop pack -- edit it directly and recompile.

Figures are included as the VECTOR .pdf sibling wherever one exists, so the
compiled pack stays sharp at any zoom. Default layout is phone-friendly:
6-inch-wide pages, each page's height measured to fit its own chart. Comment
out \mobiletrue in the .tex for wide landscape pages.

Usage:
  python scripts/build_chart_pack_tex.py          # write the .tex (refuses to
                                                  # clobber an edited one)
  python scripts/build_chart_pack_tex.py --force  # overwrite it anyway
  python scripts/build_chart_pack_tex.py --compile  # write (if absent) + pdflatex

Compile by hand with:  cd exports && pdflatex chart_pack.tex
"""
from __future__ import annotations
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gec import config as cfg
import build_chart_pack as bcp

EX = cfg.ROOT / "exports"
TEX = EX / "chart_pack.tex"

PREAMBLE = r"""% Chart pack -- editable source.
% Compile:  cd exports && pdflatex chart_pack.tex
% Figures are the vector PDFs written by the generator scripts; rerun those to
% refresh a chart, then recompile. Text below is yours to edit freely.
\documentclass[11pt]{article}

% ---- layout switch -------------------------------------------------------
% Mobile (default): narrow pages, each page sized to its own chart, so every
% figure fills a phone screen with no pinching. Comment out \mobiletrue for
% wide landscape pages meant for a desktop screen or printing.
\newif\ifmobile
\mobiletrue
% --------------------------------------------------------------------------

\ifmobile
  \usepackage[paperwidth=6in,paperheight=9in,
              top=0.30in,bottom=0.30in,left=0.30in,right=0.30in]{geometry}
\else
  \usepackage[a4paper,landscape,top=1.1cm,bottom=1.0cm,left=1.4cm,right=1.4cm]{geometry}
\fi
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{microtype}
\setlength{\parindent}{0pt}
\pagestyle{empty}
% pages never break by themselves: each macro below ships exactly one page
\ifmobile\setlength{\textheight}{200in}\fi

\definecolor{captiongrey}{HTML}{444444}
\definecolor{sectiongrey}{HTML}{888888}

\newsavebox{\gecfig}
\newsavebox{\gechdr}
\newlength{\gecpad}\setlength{\gecpad}{0.30in}
\newlength{\gecgap}\setlength{\gecgap}{11pt}

% \chartpage{title}{caption}{figure path}  -- one chart per page
\newcommand{\chartpage}[3]{%
  \clearpage
  \sbox{\gecfig}{\includegraphics[width=\linewidth]{#3}}%
  \sbox{\gechdr}{\begin{minipage}{\linewidth}\raggedright
      {\large\bfseries #1\par}%
      \ifx\relax#2\relax\else\vspace{4pt}{\small\color{captiongrey}#2\par}\fi
    \end{minipage}}%
  \ifmobile
    % page height = padding + header + gap + figure + padding
    \pdfpageheight=\dimexpr\gecpad+\ht\gechdr+\dp\gechdr+\gecgap
                          +\ht\gecfig+\dp\gecfig+\gecpad\relax
    \noindent\usebox{\gechdr}\par\vspace{\gecgap}\noindent\usebox{\gecfig}%
  \else
    \noindent\usebox{\gechdr}\vfill
    \begin{center}%
      \includegraphics[width=\linewidth,height=0.80\textheight,keepaspectratio]{#3}%
    \end{center}\vfill
  \fi
}

% \textpage{title}{body}  -- a slide with no figure (equations, explanation)
\newcommand{\textpage}[2]{%
  \clearpage
  \sbox{\gechdr}{\begin{minipage}{\linewidth}\raggedright
      {\large\bfseries #1\par}\vspace{7pt}{\small\color{captiongrey}#2\par}
    \end{minipage}}%
  \ifmobile
    \pdfpageheight=\dimexpr\gecpad+\ht\gechdr+\dp\gechdr+\gecpad\relax
  \fi
  \noindent\usebox{\gechdr}%
}

% \sectionpage{title}{blurb}
\newcommand{\sectionpage}[2]{%
  \clearpage
  \ifmobile\pdfpageheight=4in\fi
  \vspace*{\ifmobile 0.9in\else 0.30\textheight\fi}%
  \begin{center}%
    {\ifmobile\LARGE\else\Huge\fi\bfseries #1\par}%
    \vspace{14pt}%
    {\ifmobile\normalsize\else\large\fi\color{captiongrey}%
     \begin{minipage}{\ifmobile 0.92\else 0.78\fi\linewidth}\centering #2\end{minipage}\par}%
  \end{center}%
}

\begin{document}

% ---------------------------------------------------------------- title page
\ifmobile\pdfpageheight=5in\fi
\vspace*{\ifmobile 1.1in\else 0.28\textheight\fi}
\begin{center}
  {\ifmobile\LARGE\else\Huge\fi\bfseries AI-compute supply chain: chart pack\par}
  \vspace{18pt}
  \begin{minipage}{\ifmobile 0.92\else 0.80\fi\linewidth}\centering
    \ifmobile\small\else\large\fi\color{captiongrey}
    TITLEBLURB
  \end{minipage}
  \vspace{22pt}

  {\color{sectiongrey}DATESTAMP}
\end{center}
"""

FOOTER = r"""
\end{document}
"""


def esc(s: str) -> str:
    """Escape LaTeX specials in caption/title text."""
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                 ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"),
                 ("}", r"\}"), ("~", r"\textasciitilde{}"),
                 ("^", r"\textasciicircum{}")]:
        s = s.replace(a, b)
    return s


def figpath(p: Path) -> str:
    """Path relative to exports/, preferring the vector sibling; forward slashes."""
    vec = p.with_suffix(".pdf")
    use = vec if vec.exists() else p
    try:
        rel = use.relative_to(EX)
    except ValueError:
        rel = Path("..") / use.relative_to(cfg.ROOT)
    return str(rel).replace("\\", "/")


def build_tex() -> str:
    import datetime
    blurb = ("Current state of the analysis. Data: UN Comtrade + TDM monthly panel "
             "(60 HS6 codes, 2017-01 to 2026-04, checked against Atlas) and Atlas "
             "annual data. Sections 3 and 4 use the AI-compute codes only. "
             "Details: docs/data.md, docs/supply-chain-narrative.md, results/.")
    out = [PREAMBLE.replace("TITLEBLURB", esc(blurb))
                   .replace("DATESTAMP", datetime.date.today().isoformat())]
    for title, sec_blurb, items in bcp.SECTIONS:
        out.append("\n%% " + "-" * 62 + f" {title}\n")
        out.append("\\sectionpage{%s}{%s}\n" % (esc(title), esc(sec_blurb)))
        for path, ptitle, caption in items:
            out.append("\n\\chartpage{%s}{%s}{%s}\n"
                       % (esc(ptitle), esc(caption), figpath(path)))
    out.append(FOOTER)
    return "".join(out)


def main():
    args = sys.argv[1:]
    if TEX.exists() and "--force" not in args:
        print(f"{TEX} already exists -- edit it directly, or pass --force to "
              "regenerate from build_chart_pack.py")
    else:
        TEX.write_text(build_tex(), encoding="utf-8")
        print(f"-> {TEX}")
    if "--compile" in args:
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode",
                            "-halt-on-error", "chart_pack.tex"],
                           cwd=EX, capture_output=True, text=True)
        if r.returncode:
            tail = "\n".join(r.stdout.splitlines()[-25:])
            sys.exit(f"pdflatex failed:\n{tail}")
        for junk in ("chart_pack.aux", "chart_pack.log"):
            (EX / junk).unlink(missing_ok=True)
        print(f"-> {EX / 'chart_pack.pdf'} (compiled from the .tex)")


if __name__ == "__main__":
    main()
