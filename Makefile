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
	docker-compose build dag-storm # needed because it gets skipped because it's replicas are 0.

.PHONY: build_worst_case
build_worst_case:
	python ./build_configs.py
	cp ./worst_case_factory.py dags/
	docker-compose build

.PHONY: worst_case
worst_case: down clean_dags build_worst_case  ## Worst case scenario: a single dag factory with external dependencies for each dag.
	# scales to only less than 50 dags with a .1 sec delay
	# scales to about 2400 without the delay
	@docker-compose up

.PHONY: better_case
better_case: build  ## Better -- every dag gets its own file, should be well within single file limits
	# scales beyond 10k dags on stock config
	@docker-compose up

.PHONY: build_mock_api
build_mock_api:
	docker build -t mock_api -f ./mock_api/Dockerfile ./docker/mock_api

## Local cluster:
.PHONY: up
up:
	## Start the airflow cluster
	@docker-compose up

down:  ## Stop the airflow cluster
	@docker-compose down

.phony: storm
storm:  ## start a storm of dags
	docker-compose run --rm dag-storm

## Debugging:
.PHONY: shell
shell:  ## Open a shell on the airflow webserver
	@docker-compose exec -it airflow-webserver bash

#.PHONY: shell-root
#shell-root:  ## Open a shell on the airflow webserver as root
#	@docker-compose exec -it -u 0 airflow-webserver bash

.PHONY: reset
reset:  ## Reset the airflow database
	@#docker-compose exec -it  airflow-webserver airflow db reset --yes
	@docker volume rm dag_talk_examples_postgres-db-volume

# deprecated after improved reset:
#.PHONY: fix
#fix:  ## Fix the airflow database
#	@docker-compose cp ./fix_for_unserialized_dags.py airflow-webserver:/opt/airflow/fix.py
#	@docker-compose exec -it airflow-webserver python /opt/airflow/fix.py

.PHONY: browser
browser:  ## Open airflow in a browser - username:airflow password:airflow
	@echo log in to airflow with username airflow, password airflow
	@open http://localhost:8080 # airflow
	@open http://localhost:8080/admin/metrics/ # airflow
	@open http://localhost:9102/metrics # statsd-exported metrics
	@open http://localhost:9090/graph # prometheus
	@echo log in to grafana with username grafana, password grafana
	@open http://localhost:3000 # grafana
	@open http://localhost:8025 # mailhog

.PHONY: dag-log
dag-log:  # Watch the dag processor manager logs
	@tail -f ./logs/dag_processor_manager/dag_processor_manager.log

.PHONY: mock_api
mock_api:  ## start the mock api on internal port 5000, localhost port 8000.
	@docker run -it -p 8000:5000 mock_api


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

## Presentation:

slide-theme := minions_white

index.html: slides.md js/reveal.js dist/theme/$(slide-theme).css ## build presentation and theme
	pandoc -t revealjs -s -V revealjs-url=. \
		-V theme=$(slide-theme) \
		-V width=1200 \
		-V center=false \
		-V autoPlayMedia=false \
		-V hash=true \
		-o "$@" "$<"

js/reveal.js:
	curl -LO https://github.com/hakimel/reveal.js/archive/master.zip
	bsdtar --strip-components=1 --exclude .gitignore --exclude LICENSE --exclude README.md --exclude demo.html --exclude index.html -xf master.zip
	rm master.zip
	npm install

css/theme/source/$(slide-theme).scss: themes/$(slide-theme).scss
	cp "$<" "$@"

dist/theme/$(slide-theme).css: css/theme/source/$(slide-theme).scss
	npm run build -- css-themes

.PHONY: start
start: index.html ## bulid presentation and start server
	@echo "Starting the local presentation server 🚀"
	@npm start

.PHONY: clean
clean: ## clean up the working directory
	rm CONTRIBUTING.md || true
	rm LICENSE || true
	rm .npmignore || true
	rm -rf css/ || true
	rm gulpfile.js || true
	rm index.html || true
	rm -rf examples/ || true
	rm -rf js/ || true
	rm -rf lib/ || true
	rm package-lock.json || true
	rm package.json || true
	rm -rf plugin/ || true
	rm -rf test/ || true
	rm -rf node_modules/ || true
	rm -rf dist/ || true

.PHONY: watch
watch: ## Watch for changes and rebuild
	@echo "♻️ Watching for changes..."
	@watchmedo tricks-from tricks.yaml

.PHONY: clean start watch
