.PHONY: clean_dags
clean_dags:
	@rm -rf configs/[a-z]/
	@rm -rf dags/[a-z]/
	@rm -f dags/worst_case_factory.py

.PHONY: build
build: down clean_dags  ## refresh the configs and dags
	python ./build_configs.py
	python ./build_dags.py
	docker-compose build

.PHONY: build_worst_case
build_worst_case:
	python ./build_configs.py
	cp ./worst_case_factory.py dags/
	docker-compose build

.PHONY: worst_case
worst_case: down clean_dags build_worst_case  ## Worst case scenario: a single dag factory with external dependencies for each dage
	# scales to only less than 50 dags with a .1 sec delay
	# scales to about 2400 without the delay
	@docker-compose up

.PHONY: better_case
better_case: build  ## Better -- every dag gets its own file, should be well within single file limits
	# scales beyond 10k dags on stock config
	@docker-compose up

## Local cluster:
.PHONY: up
up: # build
	## Start the airflow cluster
	@docker-compose up

down:  ## Stop the airflow cluster
	@docker-compose down

## Debugging:
.PHONY: shell
shell:  ## Open a shell on the airflow webserver
	@docker-compose exec -it airflow-webserver bash

.PHONY: browser
browser:  ## Open airflow in a browser - username:airflow password:airflow
	@echo log in with username airflow, password airflow
	@open http://localhost:8080

.PHONY: dag-log
dag-log:  # Watch the dag processor manager logs
	@tail -f ./logs/dag_processor_manager/dag_processor_manager.log


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
