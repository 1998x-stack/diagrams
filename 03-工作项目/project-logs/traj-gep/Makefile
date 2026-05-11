# `TRAJ` is the canonical input. `PROJECT` defaults to its basename.
# Back-compat: passing `PROJECT=foo` alone still works (TRAJ defaults to ../traj-data-new/foo).
PROJECT ?= wzp
TRAJ    ?= ../traj-data-new/$(PROJECT)
ifeq ($(origin TRAJ), command line)
PROJECT := $(notdir $(patsubst %/,%,$(TRAJ)))
endif
PYTHON  ?= python3

.PHONY: verify-wrapper load extract cluster build clean-genes pipeline \
        pipeline-wzp pipeline-zzj pipeline-all test clean

verify-wrapper:
	@echo '{"userSnippet":"please add a button","todayLog":""}' \
	  | node scripts/extract_signals.js

load:
	$(PYTHON) -m scripts.load_trajectories \
	  --traj    $(TRAJ) \
	  --project $(PROJECT) \
	  --output  output/$(PROJECT)/sessions.jsonl

extract: load
	$(PYTHON) -m scripts.extract_signals \
	  --sessions-file output/$(PROJECT)/sessions.jsonl \
	  --wrapper       scripts/extract_signals.js \
	  --output        output/$(PROJECT)/signals.jsonl \
	  --config        config.yaml

cluster: extract
	$(PYTHON) -m scripts.cluster_patterns \
	  --signals-file output/$(PROJECT)/signals.jsonl \
	  --config       config.yaml \
	  --project      $(PROJECT) \
	  --output       output/$(PROJECT)/clusters.json

build: cluster
	$(PYTHON) -m scripts.build_genes \
	  --clusters output/$(PROJECT)/clusters.json \
	  --project  $(PROJECT) \
	  --config   config.yaml \
	  --output   output/$(PROJECT)/genes.json

clean-genes: build
	$(PYTHON) -m scripts.clean_genes \
	  --genes   output/$(PROJECT)/genes.json \
	  --project $(PROJECT) \
	  --config  config.yaml \
	  --output  output/$(PROJECT)/cleaned_genes.json

pipeline: clean-genes

pipeline-wzp:
	$(MAKE) pipeline TRAJ=../traj-data-new/wzp PROJECT=wzp

pipeline-zzj:
	$(MAKE) pipeline TRAJ=../traj-data-new/zzj PROJECT=zzj

pipeline-all: pipeline-wzp pipeline-zzj

test:
	$(PYTHON) -m pytest tests/ -v

clean:
	rm -rf output/$(PROJECT)
