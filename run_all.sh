#!/bin/bash

echo "Running ad_mono_vs_lateral..."
source startup.sh ad_mono_vs_lateral 8080
sleep 1

echo "Running ad_diagnosis..."
source startup.sh ad_diagnosis 8081
sleep 1

echo "Running ad_amy..."
source startup.sh ad_amy 8082
sleep 1

echo "Running ob_er..."
source startup.sh ob_er 8083
sleep 1

echo "Running ob_her2..."
source startup.sh ob_her2 8084
sleep 1

echo "Running ob_ki67..."
source startup.sh ob_ki67 8085
sleep 1

echo "Running ob_pr..."
source startup.sh ob_pr 8086
sleep 1

echo "Running oc_lymphnodes..."
source startup.sh oc_lymphnodes 8087
