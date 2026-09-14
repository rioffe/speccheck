# Makefile -- publishing targets for the speccheck repository.
#
#   make article     -> docs/introducing-speccheck.html: the article as ONE self-contained
#                       page (CSS inlined, the mermaid diagram rendered to an embedded SVG),
#                       so it opens offline and serves from GitHub Pages at any sub-path;
#                       a floating table of contents sits left of the text on wide screens.
#                       docs/index.html points at it.
#   make pdf         -> the four rendered PDFs (SPEC, ARCHITECTURE, README, the article)
#                       via spec2pdf.sh.
#   make clean       -> remove the generated article HTML.
#
# Needs: pandoc, and for the diagram, mermaid-filter with a Chrome/Chromium
# (install.sh sets both up; without them the diagram is left as a code block).

ARTICLE_MD   := docs/introducing-speccheck.md
ARTICLE_HTML := docs/introducing-speccheck.html
ARTICLE_CSS  := docs/article.css

# mermaid-filter: crisp, embeddable SVG; find a browser for puppeteer the way spec2pdf.sh does.
export MERMAID_FILTER_FORMAT ?= svg
CHROME := $(firstword $(wildcard /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
                                  /Applications/Chromium.app/Contents/MacOS/Chromium \
                                  /usr/bin/google-chrome /usr/bin/chromium /usr/bin/chromium-browser))
ifneq ($(CHROME),)
export PUPPETEER_EXECUTABLE_PATH ?= $(CHROME)
endif
MERMAID_FLAG := $(if $(shell command -v mermaid-filter 2>/dev/null),--filter mermaid-filter,)

.PHONY: article pdf clean help

article: $(ARTICLE_HTML)

$(ARTICLE_HTML): $(ARTICLE_MD) $(ARTICLE_CSS) docs/title-from-h1.lua Makefile
	@echo "article: building $@ (self-contained; mermaid: $(if $(MERMAID_FLAG),svg inlined,filter not found -- diagram left as code))"
	@printf '<style>\n' > $@.style.tmp; cat $(ARTICLE_CSS) >> $@.style.tmp; printf '</style>\n' >> $@.style.tmp
	pandoc $(ARTICLE_MD) --from=markdown-raw_tex --to=html5 --standalone \
	    --lua-filter=docs/title-from-h1.lua --toc --toc-depth=2 --metadata "toc-title=Contents" \
	    --include-in-header=$@.style.tmp \
	    --embed-resources $(MERMAID_FLAG) --output $@
	@rm -f $@.style.tmp mermaid-filter.err
	@echo "Success! Created '$@'."

pdf:
	./spec2pdf.sh SPEC.md
	./spec2pdf.sh ARCHITECTURE.md
	./spec2pdf.sh README.md
	./spec2pdf.sh --no-click $(ARTICLE_MD)

clean:
	rm -f $(ARTICLE_HTML) docs/introducing-speccheck.pdf mermaid-filter.err

help:
	@echo "make targets: article, pdf, clean, help"
