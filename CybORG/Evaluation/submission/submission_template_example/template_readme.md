
## Description:

The project hosts a simple LaTeX style suitable for "preprint" publications such as arXiv and bio-arXiv, etc. 
It is based on the [**nips_2018.sty**](https://media.nips.cc/Conferences/NIPS2018/Styles/nips_2018.sty) style.

This styling maintains the aesthetic of NIPS but with modifications to make it (IMO) even better and more suitable for preprints.
The result looks fairly different from NIPS style so that readers won't get confused in thinking that the preprint was published in NIPS. 

## Usage:
1. Use Document class **article**. 
2. Copy **arxiv.sty** to the folder containing your tex file.
3. Add `\usepackage{arxiv}` after `\documentclass{article}`.
4. The only packages used in the style file are **geometry** and **fancyheader**. Do not reimport them.

See **template.tex** 

## Project files:
1. **arxiv.sty** - the style file.
2. **template.tex** - a sample template that uses the **arxiv style**.
3. **references.bib** - the bibliography source file for template.tex.
4. **template.pdf** - a sample output of the template file that demonstrates the design provided by the arxiv style.

## General Notes:
1. For help, comments, praise, bug reporting or change requests, you can contact the author at: kourgeorge/at/gmail.com.
2. You can use, redistribute and do whatever with this project, however, the author takes no responsibility on whatever usage of this project.
3. If you start another project based on this project, it would be nice to mention/link to this project.
4. You are very welcome to contribute to this project.
5. A good looking 2 column template can be found in https://github.com/brenhinkeller/preprint-template.tex.
