# ================ base config ===================
version = "mini"
version = "base"
length = {'base': 234769, 'mini': 1933}

plugin = True
plugin_dir = "mmdet3d_plugin/"
dist_params = dict(backend="nccl")
log_level = "INFO"
work_dir = None

total_batch_size = 48
num_gpus = 8
batch_size = total_batch_size // num_gpus
num_iters_per_epoch = int(length[version] // (num_gpus * batch_size))
num_epochs = 6
checkpoint_epoch_interval = 2

checkpoint_config = dict(
    interval=num_iters_per_epoch * checkpoint_epoch_interval
)
log_config = dict(
    interval=51,
    hooks=[
        dict(type="TextLoggerHook", by_epoch=False),
        dict(type="TensorboardLoggerHook"),
    ],
)
load_from = None
resume_from = None
workflow = [("train", 1)]
fp16 = dict(loss_scale=32.0)
input_shape = (704, 384)

# ================== model ========================
class_names = [
    'car',
    'van',
    'truck',
    'bicycle',
    'traffic_sign',
    'traffic_cone',
    'traffic_light',
    'pedestrian',
    'others',
]
map_class_names = [
    'Broken',
    'Solid',
    'SolidSolid',
    # 'Center',
    # 'TrafficLight',
    # 'StopSign',
]
NameMapping = {
    #=================vehicle=================
    # bicycle
    'vehicle.bh.crossbike': 'bicycle',
    "vehicle.diamondback.century": 'bicycle',
    "vehicle.gazelle.omafiets": 'bicycle',
    # car
    "vehicle.chevrolet.impala": 'car',
    "vehicle.dodge.charger_2020": 'car',
    "vehicle.dodge.charger_police": 'car',
    "vehicle.dodge.charger_police_2020": 'car',
    "vehicle.lincoln.mkz_2017": 'car',
    "vehicle.lincoln.mkz_2020": 'car',
    "vehicle.mini.cooper_s_2021": 'car',
    "vehicle.mercedes.coupe_2020": 'car',
    "vehicle.ford.mustang": 'car',
    "vehicle.nissan.patrol_2021": 'car',
    "vehicle.audi.tt": 'car',
    "vehicle.audi.etron": 'car',
    "vehicle.ford.crown": 'car',
    "vehicle.ford.mustang": 'car',
    "vehicle.tesla.model3": 'car',
    "/Game/Carla/Static/Car/4Wheeled/ParkedVehicles/FordCrown/SM_FordCrown_parked.SM_FordCrown_parked": 'car',
    "/Game/Carla/Static/Car/4Wheeled/ParkedVehicles/Charger/SM_ChargerParked.SM_ChargerParked": 'car',
    "/Game/Carla/Static/Car/4Wheeled/ParkedVehicles/Lincoln/SM_LincolnParked.SM_LincolnParked": 'car',
    "/Game/Carla/Static/Car/4Wheeled/ParkedVehicles/MercedesCCC/SM_MercedesCCC_Parked.SM_MercedesCCC_Parked": 'car',
    "/Game/Carla/Static/Car/4Wheeled/ParkedVehicles/Mini2021/SM_Mini2021_parked.SM_Mini2021_parked": 'car',
    "/Game/Carla/Static/Car/4Wheeled/ParkedVehicles/NissanPatrol2021/SM_NissanPatrol2021_parked.SM_NissanPatrol2021_parked": 'car',
    "/Game/Carla/Static/Car/4Wheeled/ParkedVehicles/TeslaM3/SM_TeslaM3_parked.SM_TeslaM3_parked": 'car',
    "/Game/Carla/Static/Car/4Wheeled/ParkedVehicles/VolkswagenT2/SM_VolkswagenT2_2021_Parked.SM_VolkswagenT2_2021_Parked": 'car',
    # bus
    # van
    "/Game/Carla/Static/Car/4Wheeled/ParkedVehicles/VolkswagenT2/SM_VolkswagenT2_2021_Parked.SM_VolkswagenT2_2021_Parked": "van",
    "vehicle.ford.ambulance": "van",
    # truck
    "vehicle.carlamotors.firetruck": 'truck',
    #=========================================

    #=================traffic sign============
    # traffic.speed_limit
    "traffic.speed_limit.30": 'traffic_sign',
    "traffic.speed_limit.40": 'traffic_sign',
    "traffic.speed_limit.50": 'traffic_sign',
    "traffic.speed_limit.60": 'traffic_sign',
    "traffic.speed_limit.90": 'traffic_sign',
    "traffic.speed_limit.120": 'traffic_sign',
    
    "traffic.stop": 'traffic_sign',
    "traffic.yield": 'traffic_sign',
    "traffic.traffic_light": 'traffic_light',
    #=========================================

    #===================Construction===========
    "static.prop.warningconstruction" : 'traffic_cone',
    "static.prop.warningaccident": 'traffic_cone',
    "static.prop.trafficwarning": "traffic_cone",

    #===================Construction===========
    "static.prop.constructioncone": 'traffic_cone',

    #=================pedestrian==============
    "walker.pedestrian.0001": 'pedestrian',
    "walker.pedestrian.0004": 'pedestrian',
    "walker.pedestrian.0005": 'pedestrian',
    "walker.pedestrian.0007": 'pedestrian',
    "walker.pedestrian.0013": 'pedestrian',
    "walker.pedestrian.0014": 'pedestrian',
    "walker.pedestrian.0017": 'pedestrian',
    "walker.pedestrian.0018": 'pedestrian',
    "walker.pedestrian.0019": 'pedestrian',
    "walker.pedestrian.0020": 'pedestrian',
    "walker.pedestrian.0022": 'pedestrian',
    "walker.pedestrian.0025": 'pedestrian',
    "walker.pedestrian.0035": 'pedestrian',
    "walker.pedestrian.0041": 'pedestrian',
    "walker.pedestrian.0046": 'pedestrian',
    "walker.pedestrian.0047": 'pedestrian',

    # ==========================================
    "static.prop.dirtdebris01": 'others',
    "static.prop.dirtdebris02": 'others',
}
num_classes = len(class_names)
num_map_classes = len(map_class_names)
roi_size = (30, 60)

num_sample = 20
fut_ts = 6
fut_mode = 6
ego_fut_ts = 6
ego_fut_mode = 6
num_cmd = 1
queue_length = 4 # history + current

embed_dims = 256
num_groups = 8
num_decoder = 6
num_single_frame_decoder = 1
num_single_frame_decoder_map = 1
use_deformable_func = True  # mmdet3d_plugin/ops/setup.py needs to be executed
strides = [4, 8, 16, 32]
num_levels = len(strides)
num_depth_layers = 3
drop_out = 0.1
temporal = True
temporal_map = True
decouple_attn = True
decouple_attn_map = False
decouple_attn_motion = True
with_quality_estimation = True

task_config = dict(
    with_det=True,
    with_map=True,
    with_motion_plan=True,
)

model = dict(
    type="MomAD",
    use_grid_mask=True,
    use_deformable_func=use_deformable_func,
    img_backbone=dict(
        type="ResNet",
        depth=50,
        num_stages=4,
        frozen_stages=-1,
        norm_eval=False,
        style="pytorch",
        with_cp=True,
        out_indices=(0, 1, 2, 3),
        norm_cfg=dict(type="BN", requires_grad=True),
        pretrained="ckpt/resnet50-19c8e357.pth",
    ),
    img_neck=dict(
        type="FPN",
        num_outs=num_levels,
        start_level=0,
        out_channels=embed_dims,
        add_extra_convs="on_output",
        relu_before_extra_convs=True,
        in_channels=[256, 512, 1024, 2048],
    ),
    # depth_branch=dict(  # for auxiliary supervision only
    #     type="DenseDepthNet",
    #     embed_dims=embed_dims,
    #     num_depth_layers=num_depth_layers,
    #     loss_weight=0.2,
    # ),
    head=dict(
        type="SparseDriveHead",
        task_config=task_config,
        det_head=dict(
            type="Sparse4DHead",
            cls_threshold_to_reg=0.05,
            decouple_attn=decouple_attn,
            instance_bank=dict(
                type="InstanceBank",
                num_anchor=900,
                embed_dims=embed_dims,
                anchor="data/kmeans/kmeans_det_900.npy",
                anchor_handler=dict(type="SparseBox3DKeyPointsGenerator"),
                num_temp_instances=600 if temporal else -1,
                confidence_decay=0.9,
                feat_grad=False,
            ),
            anchor_encoder=dict(
                type="SparseBox3DEncoder",
                vel_dims=3,
                embed_dims=[128, 32, 32, 64] if decouple_attn else 256,
                mode="cat" if decouple_attn else "add",
                output_fc=not decouple_attn,
                in_loops=1,
                out_loops=4 if decouple_attn else 2,
            ),
            num_single_frame_decoder=num_single_frame_decoder,
            operation_order=(
                [
                    "gnn",
                    "norm",
                    "deformable",
                    "ffn",
                    "norm",
                    "refine",
                ]
                * num_single_frame_decoder
                + [
                    "temp_gnn",
                    "gnn",
                    "norm",
                    "deformable",
                    "ffn",
                    "norm",
                    "refine",
                ]
                * (num_decoder - num_single_frame_decoder)
            )[2:],
            temp_graph_model=dict(
                type="MultiheadFlashAttention",
                embed_dims=embed_dims if not decouple_attn else embed_dims * 2,
                num_heads=num_groups,
                batch_first=True,
                dropout=drop_out,
            )
            if temporal
            else None,
            graph_model=dict(
                type="MultiheadFlashAttention",
                embed_dims=embed_dims if not decouple_attn else embed_dims * 2,
                num_heads=num_groups,
                batch_first=True,
                dropout=drop_out,
            ),
            norm_layer=dict(type="LN", normalized_shape=embed_dims),
            ffn=dict(
                type="AsymmetricFFN",
                in_channels=embed_dims * 2,
                pre_norm=dict(type="LN"),
                embed_dims=embed_dims,
                feedforward_channels=embed_dims * 4,
                num_fcs=2,
                ffn_drop=drop_out,
                act_cfg=dict(type="ReLU", inplace=True),
            ),
            deformable_model=dict(
                type="DeformableFeatureAggregation",
                embed_dims=embed_dims,
                num_groups=num_groups,
                num_levels=num_levels,
                num_cams=6,
                attn_drop=0.15,
                use_deformable_func=use_deformable_func,
                use_camera_embed=True,
                residual_mode="cat",
                kps_generator=dict(
                    type="SparseBox3DKeyPointsGenerator",
                    num_learnable_pts=6,
                    fix_scale=[
                        [0, 0, 0],
                        [0.45, 0, 0],
                        [-0.45, 0, 0],
                        [0, 0.45, 0],
                        [0, -0.45, 0],
                        [0, 0, 0.45],
                        [0, 0, -0.45],
                    ],
                ),
            ),
            refine_layer=dict(
                type="SparseBox3DRefinementModule",
                embed_dims=embed_dims,
                num_cls=num_classes,
                refine_yaw=True,
                with_quality_estimation=with_quality_estimation,
            ),
            sampler=dict(
                type="SparseBox3DTarget",
                num_dn_groups=0,
                num_temp_dn_groups=0,
                dn_noise_scale=[2.0] * 3 + [0.5] * 7,
                max_dn_gt=32,
                add_neg_dn=True,
                cls_weight=2.0,
                box_weight=0.25,
                reg_weights=[2.0] * 3 + [0.5] * 3 + [0.0] * 4,
                cls_wise_reg_weights={
                    class_names.index("traffic_cone"): [
                        2.0,
                        2.0,
                        2.0,
                        1.0,
                        1.0,
                        1.0,
                        0.0,
                        0.0,
                        1.0,
                        1.0,
                    ],
                },
            ),
            loss_cls=dict(
                type="FocalLoss",
                use_sigmoid=True,
                gamma=2.0,
                alpha=0.25,
                loss_weight=2.0,
            ),
            loss_reg=dict(
                type="SparseBox3DLoss",
                loss_box=dict(type="L1Loss", loss_weight=0.25),
                loss_centerness=dict(type="CrossEntropyLoss", use_sigmoid=True),
                loss_yawness=dict(type="GaussianFocalLoss"),
                # cls_allow_reverse=[class_names.index("barrier")],
            ),
            decoder=dict(type="SparseBox3DDecoder"),
            reg_weights=[2.0] * 3 + [1.0] * 7,
        ),
        map_head=dict(
            type="Sparse4DHead",
            cls_threshold_to_reg=0.05,
            decouple_attn=decouple_attn_map,
            instance_bank=dict(
                type="InstanceBank",
                num_anchor=100,
                embed_dims=embed_dims,
                anchor="data/kmeans/kmeans_map_100.npy",
                anchor_handler=dict(type="SparsePoint3DKeyPointsGenerator"),
                num_temp_instances=0 if temporal_map else -1,
                confidence_decay=0.9,
                feat_grad=True,
            ),
            anchor_encoder=dict(
                type="SparsePoint3DEncoder",
                embed_dims=embed_dims,
                num_sample=num_sample,
            ),
            num_single_frame_decoder=num_single_frame_decoder_map,
            operation_order=(
                [
                    "gnn",
                    "norm",
                    "deformable",
                    "ffn",
                    "norm",
                    "refine",
                ]
                * num_single_frame_decoder_map
                + [
                    "temp_gnn",
                    "gnn",
                    "norm",
                    "deformable",
                    "ffn",
                    "norm",
                    "refine",
                ]
                * (num_decoder - num_single_frame_decoder_map)
            )[:],
            temp_graph_model=dict(
                type="MultiheadFlashAttention",
                embed_dims=embed_dims if not decouple_attn_map else embed_dims * 2,
                num_heads=num_groups,
                batch_first=True,
                dropout=drop_out,
            )
            if temporal_map
            else None,
            graph_model=dict(
                type="MultiheadFlashAttention",
                embed_dims=embed_dims if not decouple_attn_map else embed_dims * 2,
                num_heads=num_groups,
                batch_first=True,
                dropout=drop_out,
            ),
            norm_layer=dict(type="LN", normalized_shape=embed_dims),
            ffn=dict(
                type="AsymmetricFFN",
                in_channels=embed_dims * 2,
                pre_norm=dict(type="LN"),
                embed_dims=embed_dims,
                feedforward_channels=embed_dims * 4,
                num_fcs=2,
                ffn_drop=drop_out,
                act_cfg=dict(type="ReLU", inplace=True),
            ),
            deformable_model=dict(
                type="DeformableFeatureAggregation",
                embed_dims=embed_dims,
                num_groups=num_groups,
                num_levels=num_levels,
                num_cams=6,
                attn_drop=0.15,
                use_deformable_func=use_deformable_func,
                use_camera_embed=True,
                residual_mode="cat",
                kps_generator=dict(
                    type="SparsePoint3DKeyPointsGenerator",
                    embed_dims=embed_dims,
                    num_sample=num_sample,
                    num_learnable_pts=3,
                    fix_height=(0, 0.25, -0.25, 0.5, -0.5),
                    ground_height=-1.84, # ground height in lidar frame
                ),
            ),
            refine_layer=dict(
                type="SparsePoint3DRefinementModule",
                embed_dims=embed_dims,
                num_sample=num_sample,
                num_cls=num_map_classes,
            ),
            sampler=dict(
                type="SparsePoint3DTarget",
                assigner=dict(
                    type='HungarianLinesAssigner',
                    cost=dict(
                        type='MapQueriesCost',
                        cls_cost=dict(type='FocalLossCost', weight=1.0),
                        reg_cost=dict(type='LinesL1Cost', weight=10.0, beta=0.01, permute=True),
                    ),
                ),
                num_cls=num_map_classes,
                num_sample=num_sample,
                roi_size=roi_size,
            ),
            loss_cls=dict(
                type="FocalLoss",
                use_sigmoid=True,
                gamma=2.0,
                alpha=0.25,
                loss_weight=1.0,
            ),
            loss_reg=dict(
                type="SparseLineLoss",
                loss_line=dict(
                    type='LinesL1Loss',
                    loss_weight=10.0,
                    beta=0.01,
                ),
                num_sample=num_sample,
                roi_size=roi_size,
            ),
            decoder=dict(
                type="SparsePoint3DDecoder",
                score_threshold=0.5,
            ),
            reg_weights=[1.0] * 40,
            gt_cls_key="gt_map_labels",
            gt_reg_key="gt_map_pts",
            gt_id_key="map_instance_id",
            with_instance_id=False,
            task_prefix='map',
        ),
        motion_plan_head=dict(
            type='MomADMotionPlanningHead',
            fut_ts=fut_ts,
            fut_mode=fut_mode,
            ego_fut_ts=ego_fut_ts,
            ego_fut_mode=ego_fut_mode,
            motion_anchor=f'data/kmeans/kmeans_motion_{fut_mode}.npy',
            plan_anchor=None,
            # plan_anchor=f'data/kmeans/kmeans_plan_{ego_fut_mode}_b2d.npy',
            embed_dims=embed_dims,
            decouple_attn=decouple_attn_motion,
            instance_queue=dict(
                type="InstanceQueue",
                embed_dims=embed_dims,
                queue_length=queue_length,
                frame_rate=1,
                tracking_threshold=0.2,
                feature_map_scale=(input_shape[1]/strides[-1], input_shape[0]/strides[-1]),
                use_ego_status=False,
                use_tp=['near',],
            ),
            operation_order=(
                [
                    "temp_gnn",
                    "gnn",
                    "norm",
                    "cross_gnn",
                    "norm",
                    "ffn",                    
                    "norm",
                ] * 3 +
                [
                    "refine",
                ]
            ),
            temp_graph_model=dict(
                type="MultiheadAttention",
                embed_dims=embed_dims if not decouple_attn_motion else embed_dims * 2,
                num_heads=num_groups,
                batch_first=True,
                dropout=drop_out,
            ),
            graph_model=dict(
                type="MultiheadFlashAttention",
                embed_dims=embed_dims if not decouple_attn_motion else embed_dims * 2,
                num_heads=num_groups,
                batch_first=True,
                dropout=drop_out,
            ),
            cross_graph_model=dict(
                type="MultiheadFlashAttention",
                embed_dims=embed_dims,
                num_heads=num_groups,
                batch_first=True,
                dropout=drop_out,
            ),
            norm_layer=dict(type="LN", normalized_shape=embed_dims),
            ffn=dict(
                type="AsymmetricFFN",
                in_channels=embed_dims,
                pre_norm=dict(type="LN"),
                embed_dims=embed_dims,
                feedforward_channels=embed_dims * 2,
                num_fcs=2,
                ffn_drop=drop_out,
                act_cfg=dict(type="ReLU", inplace=True),
            ),
            refine_layer=dict(
                type="MotionPlanningRefinementModule",
                embed_dims=embed_dims,
                fut_ts=fut_ts,
                fut_mode=fut_mode,
                ego_fut_ts=ego_fut_ts,
                ego_fut_mode=ego_fut_mode,
                num_cmd=num_cmd,
                use_gru=False,
            ),
            motion_sampler=dict(
                type="MotionTarget",
            ),
            motion_loss_cls=dict(
                type='FocalLoss',
                use_sigmoid=True,
                gamma=2.0,
                alpha=0.25,
                loss_weight=0.2
            ),
            motion_loss_reg=dict(type='L1Loss', loss_weight=0.2),
            planning_sampler=dict(
                type="PlanningTarget",
                ego_fut_ts=ego_fut_ts,
                ego_fut_mode=ego_fut_mode,
                num_cmd=num_cmd,
            ),
            plan_loss_cls=dict(
                type='FocalLoss',
                use_sigmoid=True,
                gamma=2.0,
                alpha=0.25,
                loss_weight=0.5,
            ),
            plan_loss_reg=dict(type='L1Loss', loss_weight=1.0),
            plan_loss_status=dict(type='L1Loss', loss_weight=1.0),
            motion_decoder=dict(type="SparseBox3DMotionDecoder"),
            planning_decoder=dict(
                type="HierarchicalPlanningDecoder",
                ego_fut_ts=ego_fut_ts,
                ego_fut_mode=ego_fut_mode,
                num_cmd=num_cmd,
                use_rescore=True,
            ),
            num_det=50,
            num_map=10,
        ),
    ),
)

# ================== data ========================
dataset_type = "B2D3DDataset"
data_root = "data/bench2drive/"
anno_root = "data/infos/" if version == 'base' else "data/infos/mini/"
file_client_args = dict(backend="disk")

img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True
)
train_pipeline = [
    dict(type="LoadMultiViewImageFromFiles", to_float32=True),
    dict(type="ResizeCropFlipImage"),
    # dict(
    #     type="DenseDepthMapGenerator",
    #     downsample=strides[:num_depth_layers],
    # ),
    dict(type="BBoxRotation"),
    dict(type="PhotoMetricDistortionMultiViewImage"),
    dict(type="NormalizeMultiviewImage", **img_norm_cfg),
    dict(
        type="CircleObjectRangeFilter",
        class_dist_thred=[55] * len(class_names),
    ),
    dict(type="InstanceNameFilter", classes=class_names),
    dict(
        type='VectorizeMap',
        roi_size=roi_size,
        simplify=False,
        normalize=False,
        sample_num=num_sample,
        permute=True,
    ),
    dict(type="NuScenesSparse4DAdaptor"),
    dict(
        type="Collect",
        keys=[
            "img",
            "timestamp",
            "projection_mat",
            "image_wh",
            # "gt_depth",
            "focal",
            "gt_bboxes_3d",
            "gt_labels_3d",
            'gt_map_labels', 
            'gt_map_pts',
            'gt_agent_fut_trajs',
            'gt_agent_fut_masks',
            'gt_ego_fut_trajs',
            'gt_ego_fut_masks',
            'gt_ego_fut_cmd',
            'ego_status',
            'ego_his_trajs',
            'tp_near',
            'tp_far',
        ],
        meta_keys=["T_global", "T_global_inv", "timestamp", "instance_id"],
    ),
]
test_pipeline = [
    dict(type="LoadMultiViewImageFromFiles", to_float32=True),
    dict(type="ResizeCropFlipImage"),
    dict(type="NormalizeMultiviewImage", **img_norm_cfg),
    dict(type="NuScenesSparse4DAdaptor"),
    dict(
        type="Collect",
        keys=[
            "img",
            "timestamp",
            "projection_mat",
            "image_wh",
            'ego_status',
            'ego_his_trajs',
            'gt_ego_fut_cmd',
            'tp_near',
            'tp_far',
        ],
        meta_keys=["T_global", "T_global_inv", "timestamp"],
    ),
]
eval_pipeline = [
    dict(
        type="CircleObjectRangeFilter",
        class_dist_thred=[55] * len(class_names),
    ),
    dict(type="InstanceNameFilter", classes=class_names),
    dict(
        type='VectorizeMap',
        roi_size=roi_size,
        simplify=True,
        normalize=False,
    ),
    dict(
        type='Collect', 
        keys=[
            'vectors',
            "gt_bboxes_3d",
            "gt_labels_3d",
            'gt_agent_fut_trajs',
            'gt_agent_fut_masks',
            'gt_ego_fut_trajs',
            'gt_ego_fut_masks', 
            'gt_ego_fut_cmd',
            # 'fut_boxes'
        ],
        meta_keys=['token', 'timestamp']
    ),
]

input_modality = dict(
    use_lidar=False,
    use_camera=True,
    use_radar=False,
    use_map=False,
    use_external=False,
)

data_basic_config = dict(
    type=dataset_type,
    data_root=data_root,
    classes=class_names,
    map_classes=map_class_names,
    name_mapping=NameMapping,
    modality=input_modality,
    sample_interval=5,
    past_frames=6,
    future_frames=6,
    use_cmd=num_cmd>1,
)
eval_config = dict(
    **data_basic_config,
    ann_file=anno_root + 'b2d_infos_val.pkl',
    pipeline=eval_pipeline,
    test_mode=True,
)
data_aug_conf = {
    "resize_lim": (0.40, 0.47),
    "final_dim": input_shape[::-1],
    "bot_pct_lim": (0.0, 0.0),
    "rot_lim": (-5.4, 5.4),
    "H": 900,
    "W": 1600,
    "rand_flip": True,
    "rot3d_range": [0, 0],
}

data = dict(
    samples_per_gpu=batch_size,
    workers_per_gpu=batch_size,
    train=dict(
        **data_basic_config,
        ann_file=anno_root + "b2d_infos_train.pkl",
        pipeline=train_pipeline,
        test_mode=False,
        data_aug_conf=data_aug_conf,
        with_seq_flag=True,
        sequences_split_num=5,
        keep_consistent_seq_aug=True,
    ),
    val=dict(
        **data_basic_config,
        ann_file=anno_root + "b2d_infos_val.pkl",
        pipeline=test_pipeline,
        data_aug_conf=data_aug_conf,
        test_mode=True,
        eval_config=eval_config,
    ),
    test=dict(
        **data_basic_config,
        ann_file=anno_root + "b2d_infos_val.pkl",
        pipeline=test_pipeline,
        data_aug_conf=data_aug_conf,
        test_mode=True,
        eval_config=eval_config,
    ),
)

# ================== training ========================
optimizer = dict(
    type="AdamW",
    lr=2e-4,
    weight_decay=0.001,
    paramwise_cfg=dict(
        custom_keys={
            "img_backbone": dict(lr_mult=0.1),
        }
    ),
)
optimizer_config = dict(grad_clip=dict(max_norm=25, norm_type=2))
lr_config = dict(
    policy="CosineAnnealing",
    warmup="linear",
    warmup_iters=500,
    warmup_ratio=1.0 / 3,
    min_lr_ratio=1e-3,
)
runner = dict(
    type="IterBasedRunner",
    max_iters=num_iters_per_epoch * num_epochs,
)

# ================== eval ========================
eval_mode = dict(
    with_det=True,
    with_tracking=False,
    with_map=False,
    with_motion=False,
    with_planning=True,
    tracking_threshold=0.2,
    motion_threshhold=0.2,
)
evaluation = dict(
    interval=num_iters_per_epoch*checkpoint_epoch_interval,
    eval_mode=eval_mode,
)
# ================== pretrained model ========================
# load_from = 'http://svcspawner.bcloud-beijing.hobot.cc/user/homespace/wenchao.sun/plat_gpu/sparsedrive_small_b2d_stage1_20e-20240903-225131.954333/output/work_dirs/latest.pth'
load_from = "ckpt/sparsedrive_small_b2d_stage1.pth"