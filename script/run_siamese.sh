python ./src/main_siamese.py  --sketch_dir /home/jiangtongli/Lab_Work/ZS-SBIR/data/256x256/sketch/tx_000100000000 \
                              --image_dir /home/jiangtongli/Lab_Work/ZS-SBIR/data/256x256/EXTEND_image_sketchy \
                              --stats_file /home/jiangtongli/Lab_Work/ZS-SBIR/data/info/stats.csv \
                              --packed_pkl_nozs /home/jiangtongli/Lab_Work/ZS-SBIR/data/preprocessed/nozs_packed.pkl \
                              --packed_pkl_zs /home/jiangtongli/Lab_Work/ZS-SBIR/data/preprocessed/zs_packed.pkl \
                              --log_file /home/jiangtongli/Lab_Work/ZS-SBIR/log/run4.log \
                              --shuffle \
                              --mode 0 \
                              --margin 300 \
                              --loss_type 1 \
                              --distance_type 0 \
                              --patience 10 \
                              --batch_size 32 \
                              --num_worker 16 \
                              --dropout 0.5 \
                              --warmup_steps 500 \
                              --lr 5e-3 \
                              --print_every 50 \
                              --save_every 500 \
                              --save_dir /home/jiangtongli/Lab_Work/ZS-SBIR/model/run4/ \
                              --gpu_id 0 \
                              --cum_num 4 \
                              --zs
