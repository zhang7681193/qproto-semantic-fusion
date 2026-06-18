# MHEALTH Fairness Audit

## Payload equality
- chop_equal_bytes: [13876]
- cproto_equal_bytes: [13876]
- group_cproto_equal_bytes: [13876]
- random_key_cproto_equal_bytes: [13876]
- random_key_hop_equal_bytes: [13876]
- shared_view_rff_equal_bytes: [13876]
- zero_fill_rff_equal_bytes: [13876]

## Paired deltas by seed
- chop_equal_bytes - cproto_equal_bytes: deltas=[0.0171, 0.0312, 0.0274, 0.0291, 0.0435], mean=0.0297, wins=5/5
- chop_equal_bytes - zero_fill_rff_equal_bytes: deltas=[0.1027, 0.1729, 0.1155, 0.1012, 0.102], mean=0.1189, wins=5/5
- chop_equal_bytes - shared_view_rff_equal_bytes: deltas=[0.1038, 0.1465, 0.178, 0.213, 0.3507], mean=0.1984, wins=5/5
- chop_equal_bytes - mask_aware_mlp_pooled: deltas=[0.0303, 0.0406, 0.0377, 0.0053, 0.0906], mean=0.0409, wins=5/5
- random_key_hop_equal_bytes - random_key_cproto_equal_bytes: deltas=[-0.0003, 0.0004, 0.0, -0.0002, 0.0004], mean=0.0001, wins=3/5

## Interpretation
- Strict-budget rows all use 13,876 bytes/client/round.
- CProto equal bytes uses the automatically derived larger low-order key budget, so CHOP is not compared against an under-budget low-order prototype.
- Random-key HOP does not improve over random-key CProto, so the observed CHOP gain is not attributed to arbitrary extra HOP payload; it depends on schema/anchor-selected keys and pairs.

