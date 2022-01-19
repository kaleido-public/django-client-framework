# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
.EXPORT_ALL_VARIABLES:
DOC_VERSION   = $(shell sed -n 's/version = "\(\d.\d\).*"/\1/p' < /pyproject.toml).x
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = /_output/$(DOC_VERSION)

# Put it first so that "make" without argument is like "make help".
help:
	$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile serve

serve:
	nginx -g "daemon off;"

typedoc:
	typedoc --options typedoc.json

sass:
	sass "$(SOURCEDIR)/_static/custom.scss" "$(BUILDDIR)/html/_static/custom.css"

clean:
	$(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O) -t internal


# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%:
	$(MAKE) -f sphinx.Makefile clean
	$(MAKE) -f sphinx.Makefile sass
	$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O) -t internal
	touch /_output/.nojekyll
