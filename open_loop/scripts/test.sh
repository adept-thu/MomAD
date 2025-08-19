CUDA_VISIBLE_DEVICES=0\ 
   bash ./tools/dist_test.sh \
    projects/configs/sparsedrive_small_stage2.py \
    work_dirs/sparsedrive_small_stage2/iter_5860.pth \
    1 \
    --deterministic \
    --eval bbox
    # --result_file ./work_dirs/sparsedrive_small_stage2/results.pkl