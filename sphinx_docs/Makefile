# Minimal makefile for Sphinx documentation

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD  ?= sphinx-build
SOURCEDIR    = .
BUILDDIR     = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx-Makefile.
# The $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Custom targets for Pili documentation

.PHONY: clean-all
clean-all:
	rm -rf $(BUILDDIR)/*

.PHONY: livehtml
livehtml:
	sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)

.PHONY: dev
dev: clean-all html
	@echo "Documentation built successfully!"
	@echo "Open file://$(PWD)/$(BUILDDIR)/html/index.html in your browser"

.PHONY: serve
serve: html
	@echo "Starting local server at http://localhost:8080"
	cd $(BUILDDIR)/html && python -m http.server 8080

.PHONY: check
check:
	$(SPHINXBUILD) -b linkcheck "$(SOURCEDIR)" "$(BUILDDIR)/linkcheck" $(SPHINXOPTS) $(O)
	$(SPHINXBUILD) -b spelling "$(SOURCEDIR)" "$(BUILDDIR)/spelling" $(SPHINXOPTS) $(O)

.PHONY: pdf
pdf:
	$(SPHINXBUILD) -b latex "$(SOURCEDIR)" "$(BUILDDIR)/latex" $(SPHINXOPTS) $(O)
	@echo "Running LaTeX files through pdflatex..."
	$(MAKE) -C $(BUILDDIR)/latex all-pdf
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."

.PHONY: install-deps
install-deps:
	pip install sphinx>=7.0.0 sphinx-rtd-theme>=2.0.0 sphinx-autodoc-typehints>=1.25.0 sphinx-copybutton>=0.5.2 myst-parser>=2.0.0 sphinx-autoapi>=3.0.0

.PHONY: install-dev-deps
install-dev-deps: install-deps
	pip install sphinx-autobuild pyspelling

.PHONY: auto
auto: install-dev-deps
	sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" --host 0.0.0.0 --port 8080 --open-browser 