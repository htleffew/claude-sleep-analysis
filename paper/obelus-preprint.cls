%% obelus-preprint.cls
%% A clean academic preprint document class for the Obelus Institute.
%% Original code using standard LaTeX packages, written to produce
%% conventional journal-style typography suitable for arxiv / PsyArXiv
%% preprints that may later be submitted to high-impact journals.
%%
%% Options:
%%   referee   double line spacing for editorial review
%%   lineno    line numbers in the margin (for review)
%%   twocolumn two-column layout (single-column by default)
%%   numbib    numeric citations (default is author-year)
%%
%% Author: Heather Leffew, Obelus Institute
%% This file is released under the LaTeX Project Public License v1.3c.

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{obelus-preprint}[2026/05/16 v1.0 Obelus preprint class]

% --- Options -----------------------------------------------------------
\newif\if@refereemode \@refereemodefalse
\newif\if@linenumbers \@linenumbersfalse
\newif\if@twocol \@twocolfalse
\newif\if@numbib \@numbibfalse

\DeclareOption{referee}{\@refereemodetrue}
\DeclareOption{lineno}{\@linenumberstrue}
\DeclareOption{twocolumn}{\@twocoltrue}
\DeclareOption{numbib}{\@numbibtrue}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax

\if@twocol
  \LoadClass[11pt,letterpaper,twocolumn]{article}
\else
  \LoadClass[11pt,letterpaper]{article}
\fi

% --- Page geometry -----------------------------------------------------
\RequirePackage[letterpaper,
  top=1in,
  bottom=1in,
  left=1in,
  right=1in,
  headheight=14pt,
  footskip=0.5in]{geometry}

% --- Fonts -------------------------------------------------------------
% Serif body, sans headings, mono for code: conventional academic mix.
\RequirePackage[T1]{fontenc}
\RequirePackage[utf8]{inputenc}
\RequirePackage{mathptmx}     % Times-like serif
\RequirePackage[scaled=0.92]{helvet}  % Helvetica-like sans
\RequirePackage{courier}      % Mono for code
\renewcommand{\familydefault}{\rmdefault}

% --- Microtype + line breaks ------------------------------------------
\RequirePackage{microtype}
\RequirePackage[english]{babel}

% --- Spacing -----------------------------------------------------------
\if@refereemode
  \RequirePackage{setspace}
  \doublespacing
\else
  \RequirePackage{setspace}
  \onehalfspacing
\fi

% --- Section heads -----------------------------------------------------
\RequirePackage{titlesec}
\titleformat{\section}
  {\normalfont\sffamily\bfseries\large}{\thesection}{0.75em}{}
\titleformat{\subsection}
  {\normalfont\sffamily\bfseries\normalsize}{\thesubsection}{0.6em}{}
\titleformat{\subsubsection}
  {\normalfont\sffamily\bfseries\small}{\thesubsubsection}{0.5em}{}
\titleformat{\paragraph}[runin]
  {\normalfont\sffamily\bfseries\small}{}{0pt}{}[.]

\titlespacing*{\section}{0pt}{1.4em}{0.5em}
\titlespacing*{\subsection}{0pt}{1.1em}{0.4em}
\titlespacing*{\subsubsection}{0pt}{0.8em}{0.3em}

% --- Captions ----------------------------------------------------------
\RequirePackage[font=small,labelfont=bf,skip=4pt]{caption}

% --- Tables ------------------------------------------------------------
\RequirePackage{booktabs}
\RequirePackage{array}
\RequirePackage{tabularx}
\renewcommand{\arraystretch}{1.15}

% --- Lists -------------------------------------------------------------
\RequirePackage{enumitem}
\setlist{topsep=0.3em,itemsep=0.15em,leftmargin=1.5em}

% --- Math --------------------------------------------------------------
\RequirePackage{amsmath,amssymb}

% --- Graphics ----------------------------------------------------------
\RequirePackage{graphicx}

% --- Hyperref ----------------------------------------------------------
\RequirePackage{xcolor}
\definecolor{obelus@link}{HTML}{0F52BA}  % sapphire (matches portfolio site)
\RequirePackage[colorlinks=true,
  linkcolor=black,
  urlcolor=obelus@link,
  citecolor=obelus@link,
  filecolor=obelus@link]{hyperref}

% --- Line numbers ------------------------------------------------------
\if@linenumbers
  \RequirePackage[modulo,switch*]{lineno}
  \AtBeginDocument{\linenumbers}
\fi

% --- Bibliography ------------------------------------------------------
% By default uses natbib in author-year mode; switch to numeric with
% the [numbib] option.
\RequirePackage[round,authoryear]{natbib}
\if@numbib
  \setcitestyle{numbers,square,comma}
\fi

% --- Title block -------------------------------------------------------
% Author-facing macros: \title, \author, \affiliation, \email, \date
% (standard LaTeX-style, no journal-specific syntax).
\def\@affiliation{}
\newcommand{\affiliation}[1]{\def\@affiliation{#1}}
\def\@email{}
\newcommand{\email}[1]{\def\@email{#1}}
\def\@runninghead{}
\newcommand{\runninghead}[1]{\def\@runninghead{#1}}
\def\@keywords{}
\newcommand{\keywords}[1]{\def\@keywords{#1}}

\renewcommand{\maketitle}{%
  \begin{center}%
    {\Large\bfseries\sffamily\@title\par}%
    \vspace{0.6em}%
    {\large\@author\par}%
    \ifx\@affiliation\@empty\else
      \vspace{0.2em}{\normalsize\itshape\@affiliation\par}%
    \fi
    \ifx\@email\@empty\else
      \vspace{0.1em}{\small\texttt{\@email}\par}%
    \fi
    \vspace{0.2em}{\small\@date\par}%
  \end{center}%
  \vspace{0.8em}\hrule\vspace{0.8em}%
}

% --- Abstract ----------------------------------------------------------
\renewenvironment{abstract}
  {\small\noindent\textbf{\sffamily Abstract.}\quad}
  {\par\ifx\@keywords\@empty\else
     \vspace{0.4em}\noindent\textbf{\sffamily Keywords:} \small\@keywords\par
   \fi
   \vspace{0.6em}\hrule\vspace{0.6em}}

% --- Headers / footers -------------------------------------------------
\RequirePackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\itshape\@runninghead}
\fancyhead[R]{\small\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}
\fancypagestyle{plain}{%
  \fancyhf{}%
  \fancyfoot[C]{\small\thepage}%
  \renewcommand{\headrulewidth}{0pt}%
}

% --- Paragraph indentation --------------------------------------------
% Most academic articles use indented paragraphs with no extra spacing.
\setlength{\parindent}{1.5em}
\setlength{\parskip}{0pt}

\endinput
