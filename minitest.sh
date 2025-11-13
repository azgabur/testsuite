#!/bin/bash
# Small script to run smoke on all clusters with kuadrant
source ~/work/ocp-tool/ocp.sh

CLUSTERS="$(ocp list | grep "kua" | cut -d' ' -f1)"

for i in $CLUSTERS;
do
	echo "$i" | grep "hub" && continue
	echo "$i" | grep "unstable" && continue
    ocp use "$i" > /dev/null 2> /dev/null
    echo "Cluster $i has version $(oc get --ignore-not-found -n kuadrant-system catalogsource kuadrant-upstream -o jsonpath=\"{.spec.image}\")"
    KUADRANT_READY="$(oc get --ignore-not-found -n kuadrant-system kuadrant kuadrant-sample -o jsonpath=\"{.status.conditions\[0\].status}\")"
    echo "Kuadrant CR is ready? $KUADRANT_READY"
    if [[ $KUADRANT_READY == "\"True\"" ]]; then
        echo "Will run smoke test"
        make smoke
    fi
done
