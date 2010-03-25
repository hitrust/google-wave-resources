PAPER = wave

all:	$(PAPER).tex 
	pdflatex $(PAPER).tex
	bibtex $(PAPER)
	pdflatex $(PAPER).tex

v:	$(PAPER).pdf
	xpdf $(PAPER).pdf &

clean:
	rm *.ps *.pdf $(PAPER).log $(PAPER).out $(PAPER).bbl $(PAPER).toc $(PAPER).blg $(PAPER).dvi $(PAPER).aux *~
