# bash ./tools/dist_test.sh \
#     projects/configs/sparsedrive_small_stage2.py \
#     ckpt/sparsedrive_stage2.pth \
#     8 \
#     --deterministic \
#     --ev/data/songziying/workspace/SparseDrive/scriptsal bbox
#     # --result_file ./work_dirs/sparsedrive_small_stage2/results.pkl
bash ./tools/dist_test.sh \
    projects/configs/sparsedrive_small_stage2_roboAD_6s.py \
    work_dirs/sparsedrive_small_stage2_roboAD_6s/iter_5860.pth\
    1 \
    --deterministic \
    --eval bbox
    # --result_file ./work_dirs/sparsedrive_small_stage2_roboAD/results.pkl