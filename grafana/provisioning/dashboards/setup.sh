echo "waiting to set up dashboards"
curl --retry 10 --retry-delay 6 --retry-connrefused -o /dev/null \
  "http://airflow-grafana:3000/api/dashboards/db" --user grafana:grafana

#echo
#echo "adding json api plugin"
#grafana cli plugins install marcusolsson-json-datasource

echo
echo "setting up dashboards"
for f in /grafana/provisioning/dashboards/*.json; do
  echo "setting up dashboard $f"
  curl http://airflow-grafana:3000/api/dashboards/db \
    -X POST \
    -H "Content-Type: application/json" \
    --user grafana:grafana \
    -d @$f
done

echo "done."
