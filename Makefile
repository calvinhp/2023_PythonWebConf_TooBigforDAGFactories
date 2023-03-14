.PHONY: build
build: down ## refresh the configs and dags
	rm -rf configs/[a-z]/
	rm -rf dags/[a-z]/
	python ./build_configs.py
	python ./build_dags.py
	docker-compose build

## Local cluster:
.PHONY: up
up: # build
	## Start the airflow cluster
	docker-compose up

down:  ## Stop the airflow cluster
	docker-compose down

## Debugging:
.PHONY: shell
shell:  ## Open a shell on the airflow webserver
	docker-compose exec -it airflow-webserver bash

.PHONY: browser
browser:  ## Open airflow in a browser - username:airflow password:airflow
	@echo log in with username airflow, password airflow
	@open http://localhost:8080


## Documentation:
usage: ## This list of targets.  Run `make help` for more indepth assistance.
	@awk 'BEGIN     { FS = ":.*##"; target="";printf "\nUsage:\n  make \033[36m<target>\033[33m\n\nTargets:\033[0m\n" } \
		/^[.a-zA-Z_-]+:.*?##/ { if(target=="")print ""; target=$$1; printf " \033[36m%-10s\033[0m %s\n\n", $$1, $$2 } \
		/^([.a-zA-Z_-]+):/ {if(target=="")print "";match($$0, "(.*):"); target=substr($$0,RSTART,RLENGTH) } \
		/^\t## (.*)/ { match($$0, "[^\t#:\\\\]+"); txt=substr($$0,RSTART,RLENGTH);printf " \033[36m%-10s\033[0m", target; printf " %s\n", txt ; target=""} \
		/^## (.*)/ {match($$0, "[^\t#\\\\]+"); txt=substr($$0,RSTART,RLENGTH);printf "\n\033[33m%s\033[0m\n", txt ; target=""} \
	' $(MAKEFILE_LIST)
	@# based on https://gist.github.com/gfranxman/73b5dc6369dc684db6848198290330c7#file-makefile


.DEFAULT_GOAL := usage
