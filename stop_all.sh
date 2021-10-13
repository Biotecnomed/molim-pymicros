#!/bin/bash

echo "Shutting down ad_mono_vs_lateral..."
source shutdown.sh 8080
sleep 1

echo "Shutting down ad_diagnosis..."
source shutdown.sh 8081
sleep 1

echo "Shutting down ad_amy..."
source shutdown.sh 8082
sleep 1

echo "Shutting down ob_er..."
source shutdown.sh 8083
sleep 1

echo "Shutting down ob_her2..."
source shutdown.sh 8084
sleep 1

echo "Shutting down ob_ki67..."
source shutdown.sh 8085
sleep 1

echo "Shutting down ob_pr..."
source shutdown.sh 8086
sleep 1

echo "Shutting down oc_lymphnodes..."
source shutdown.sh 8087