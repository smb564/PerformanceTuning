#!/usr/bin/env bash
source venv/bin/activate

q_folder="rl_models"
model_folder="polynomials"

for mix in "browsing" "shopping" "ordering"
do
    for ebs in 50 100 150 200
    do
        python3 rl_optimizer.py pretrain ${model_folder} ${mix}_${ebs} ${q_folder}
    done
done