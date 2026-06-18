# Real Image Dataset Tables

## mnist4

| Method | n | Acc. mean | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| centralized_qproto | 5 | 0.7007 | 0.0379 | 0.6984 | 0 |
| qproto_full | 5 | 0.7045 | 0.0376 | 0.7017 | 4632 |
| qproto_hop | 5 | 0.7094 | 0.0542 | 0.7073 | 4628 |
| qproto_proto | 5 | 0.7087 | 0.0544 | 0.7067 | 3092 |
| no_schema | 5 | 0.4410 | 0.0293 | 0.4372 | 3092 |
| forced_canonical | 5 | 0.4374 | 0.0390 | 0.4338 | 3092 |
| wrong_schema | 5 | 0.2796 | 0.0229 | 0.2782 | 4628 |
| fedavg_forced | 5 | 0.3743 | 0.0781 | 0.3677 | 3088 |
| fedprox_forced | 5 | 0.3741 | 0.0786 | 0.3675 | 3088 |
| local_only | 5 | 0.7378 | 0.0374 | 0.7350 | 0 |
| classical_kernel | 5 | 0.6710 | 0.0257 | 0.6669 | 3092 |

## fashion4

| Method | n | Acc. mean | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| centralized_qproto | 5 | 0.7343 | 0.0473 | 0.7343 | 0 |
| qproto_full | 5 | 0.7338 | 0.0466 | 0.7336 | 4632 |
| qproto_hop | 5 | 0.7459 | 0.0374 | 0.7459 | 4628 |
| qproto_proto | 5 | 0.7453 | 0.0375 | 0.7453 | 3092 |
| no_schema | 5 | 0.4306 | 0.0237 | 0.4300 | 3092 |
| forced_canonical | 5 | 0.4293 | 0.0216 | 0.4285 | 3092 |
| wrong_schema | 5 | 0.2990 | 0.0269 | 0.2981 | 4628 |
| fedavg_forced | 5 | 0.3358 | 0.0635 | 0.3389 | 3088 |
| fedprox_forced | 5 | 0.3352 | 0.0640 | 0.3383 | 3088 |
| local_only | 5 | 0.7344 | 0.0383 | 0.7345 | 0 |
| classical_kernel | 5 | 0.6635 | 0.0172 | 0.6630 | 3092 |

## cifar4

| Method | n | Acc. mean | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| centralized_qproto | 5 | 0.4887 | 0.0453 | 0.4891 | 0 |
| qproto_full | 5 | 0.4842 | 0.0404 | 0.4842 | 4632 |
| qproto_hop | 5 | 0.4859 | 0.0521 | 0.4855 | 4628 |
| qproto_proto | 5 | 0.4856 | 0.0521 | 0.4852 | 3092 |
| no_schema | 5 | 0.3389 | 0.0171 | 0.3388 | 3092 |
| forced_canonical | 5 | 0.3388 | 0.0191 | 0.3387 | 3092 |
| wrong_schema | 5 | 0.2679 | 0.0146 | 0.2672 | 4628 |
| fedavg_forced | 5 | 0.2981 | 0.0457 | 0.2989 | 3088 |
| fedprox_forced | 5 | 0.2983 | 0.0458 | 0.2991 | 3088 |
| local_only | 5 | 0.5331 | 0.0221 | 0.5330 | 0 |
| classical_kernel | 5 | 0.4112 | 0.0097 | 0.4112 | 3092 |
| centralized_kernel | 5 | 0.4123 | 0.0094 | 0.4123 | 0 |

