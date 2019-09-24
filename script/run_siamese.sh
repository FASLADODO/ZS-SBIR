python ./src/main_siamese.py --sketch_dir_train /home/jiangtongli/Lab_Work/ZS-SBIR/data/preprocessed/sketch_train \
                              --image_dir_train /home/jiangtongli/Lab_Work/ZS-SBIR/data/preprocessed/photo_train \
                              --sketch_dir_test /home/jiangtongli/Lab_Work/ZS-SBIR/data/preprocessed/sketch_test \
                              --image_dir_test /home/jiangtongli/Lab_Work/ZS-SBIR/data/preprocessed/photo_test \
                              --stats_file_train /home/jiangtongli/Lab_Work/ZS-SBIR/data/preprocessed/stats_train.csv \
                              --stats_file_test /home/jiangtongli/Lab_Work/ZS-SBIR/data/preprocessed/stats_test.csv \
                              --packed_pkl /home/jiangtongli/Lab_Work/ZS-SBIR/data/preprocessed/packed.pkl \
                              --log_file /home/jiangtongli/Lab_Work/ZS-SBIR/log/run1.log \
                              --shuffle \
                              --mode 0 \
                              --margin 2 \
                              --loss_type 0 \
                              --distance_type 0 \
                              --patience 10 \
                              --batch_size 32 \
                              --num_worker 16 \
                              --dropout 0.2 \
                              --warmup_steps 0 \
                              --lr 5e-5 \
                              --print_every 50 \
                              --save_every 200 \
                              --save_dir /home/jiangtongli/Lab_Work/ZS-SBIR/model/run1/ \
                              --gpu_id 0