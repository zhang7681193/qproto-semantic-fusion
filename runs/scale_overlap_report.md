# Scale and Observable-Overlap Report

## CIFAR-10 clients

### clients=50

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.4529 | 0.0127 | 0.4533 | 24364 |
| qproto_chop | 3 | 0.4490 | 0.0123 | 0.4493 | 11564 |
| qproto_cproto | 3 | 0.4485 | 0.0114 | 0.4488 | 7724 |
| fedadam_schema | 3 | 0.3201 | 0.0427 | 0.3186 | 7720 |
| fedproto_schema | 3 | 0.3254 | 0.0337 | 0.3253 | 7724 |
| shared_observable | 3 | 0.4238 | 0.0444 | 0.4242 | 7724 |
| no_schema | 3 | 0.1477 | 0.0217 | 0.1479 | 7724 |
| wrong_schema | 3 | 0.1114 | 0.0039 | 0.1115 | 11564 |

### clients=100

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.4550 | 0.0066 | 0.4553 | 24364 |
| qproto_chop | 3 | 0.4511 | 0.0082 | 0.4514 | 11564 |
| qproto_cproto | 3 | 0.4504 | 0.0082 | 0.4507 | 7724 |
| fedadam_schema | 3 | 0.3421 | 0.0452 | 0.3425 | 7720 |
| fedproto_schema | 3 | 0.3485 | 0.0265 | 0.3489 | 7724 |
| shared_observable | 3 | 0.4240 | 0.0446 | 0.4243 | 7724 |
| no_schema | 3 | 0.1368 | 0.0181 | 0.1372 | 7724 |
| wrong_schema | 3 | 0.1096 | 0.0033 | 0.1096 | 11564 |

## CIFAR-10 overlap

### overlap=0.20

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.4525 | 0.0095 | 0.4528 | 24364 |
| qproto_chop | 3 | 0.4247 | 0.0140 | 0.4252 | 11564 |
| qproto_cproto | 3 | 0.4244 | 0.0138 | 0.4249 | 7724 |
| fedadam_schema | 3 | 0.1482 | 0.0308 | 0.1477 | 7720 |
| fedproto_schema | 3 | 0.1429 | 0.0388 | 0.1433 | 7724 |
| shared_observable | 3 | 0.3254 | 0.0412 | 0.3261 | 7724 |
| no_schema | 3 | 0.1566 | 0.0149 | 0.1568 | 7724 |
| wrong_schema | 3 | 0.1124 | 0.0024 | 0.1125 | 11564 |

### overlap=0.60

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.4619 | 0.0450 | 0.4622 | 24364 |
| qproto_chop | 3 | 0.4528 | 0.0445 | 0.4532 | 11564 |
| qproto_cproto | 3 | 0.4523 | 0.0451 | 0.4527 | 7724 |
| fedadam_schema | 3 | 0.2026 | 0.0546 | 0.2021 | 7720 |
| fedproto_schema | 3 | 0.1926 | 0.0642 | 0.1931 | 7724 |
| shared_observable | 3 | 0.4225 | 0.0439 | 0.4231 | 7724 |
| no_schema | 3 | 0.1608 | 0.0164 | 0.1609 | 7724 |
| wrong_schema | 3 | 0.1136 | 0.0098 | 0.1140 | 11564 |

### overlap=1.00

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.4597 | 0.0172 | 0.4601 | 24364 |
| qproto_chop | 3 | 0.4601 | 0.0189 | 0.4604 | 11564 |
| qproto_cproto | 3 | 0.4588 | 0.0188 | 0.4591 | 7724 |
| fedadam_schema | 3 | 0.4195 | 0.0639 | 0.4200 | 7720 |
| fedproto_schema | 3 | 0.4381 | 0.0234 | 0.4387 | 7724 |
| shared_observable | 3 | 0.4376 | 0.0306 | 0.4382 | 7724 |
| no_schema | 3 | 0.1558 | 0.0101 | 0.1558 | 7724 |
| wrong_schema | 3 | 0.1136 | 0.0135 | 0.1141 | 11564 |

## Fashion-10 clients

### clients=50

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.6715 | 0.0568 | 0.6712 | 24364 |
| qproto_chop | 3 | 0.6692 | 0.0640 | 0.6690 | 11564 |
| qproto_cproto | 3 | 0.6685 | 0.0625 | 0.6683 | 7724 |
| fedadam_schema | 3 | 0.5901 | 0.0439 | 0.5906 | 7720 |
| fedproto_schema | 3 | 0.6016 | 0.0306 | 0.6015 | 7724 |
| shared_observable | 3 | 0.6596 | 0.0564 | 0.6591 | 7724 |
| no_schema | 3 | 0.2087 | 0.0427 | 0.2094 | 7724 |
| wrong_schema | 3 | 0.1419 | 0.0137 | 0.1423 | 11564 |

### clients=100

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.6730 | 0.0514 | 0.6727 | 24364 |
| qproto_chop | 3 | 0.6714 | 0.0594 | 0.6710 | 11564 |
| qproto_cproto | 3 | 0.6703 | 0.0573 | 0.6699 | 7724 |
| fedadam_schema | 3 | 0.6143 | 0.0489 | 0.6148 | 7720 |
| fedproto_schema | 3 | 0.6202 | 0.0431 | 0.6199 | 7724 |
| shared_observable | 3 | 0.6597 | 0.0539 | 0.6592 | 7724 |
| no_schema | 3 | 0.1978 | 0.0352 | 0.1982 | 7724 |
| wrong_schema | 3 | 0.1309 | 0.0126 | 0.1313 | 11564 |

## Fashion-10 overlap

### overlap=0.20

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.6696 | 0.0101 | 0.6694 | 24364 |
| qproto_chop | 3 | 0.6509 | 0.0213 | 0.6508 | 11564 |
| qproto_cproto | 3 | 0.6506 | 0.0215 | 0.6504 | 7724 |
| fedadam_schema | 3 | 0.2379 | 0.0634 | 0.2395 | 7720 |
| fedproto_schema | 3 | 0.2201 | 0.0299 | 0.2216 | 7724 |
| shared_observable | 3 | 0.5978 | 0.0281 | 0.5984 | 7724 |
| no_schema | 3 | 0.2285 | 0.0145 | 0.2295 | 7724 |
| wrong_schema | 3 | 0.1504 | 0.0341 | 0.1510 | 11564 |

### overlap=0.60

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.6736 | 0.0165 | 0.6730 | 24364 |
| qproto_chop | 3 | 0.6697 | 0.0241 | 0.6689 | 11564 |
| qproto_cproto | 3 | 0.6693 | 0.0254 | 0.6685 | 7724 |
| fedadam_schema | 3 | 0.3669 | 0.1543 | 0.3698 | 7720 |
| fedproto_schema | 3 | 0.3629 | 0.1157 | 0.3646 | 7724 |
| shared_observable | 3 | 0.6658 | 0.0194 | 0.6651 | 7724 |
| no_schema | 3 | 0.2190 | 0.0288 | 0.2201 | 7724 |
| wrong_schema | 3 | 0.1530 | 0.0112 | 0.1538 | 11564 |

### overlap=1.00

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.6714 | 0.0455 | 0.6712 | 24364 |
| qproto_chop | 3 | 0.6718 | 0.0414 | 0.6715 | 11564 |
| qproto_cproto | 3 | 0.6698 | 0.0431 | 0.6694 | 7724 |
| fedadam_schema | 3 | 0.6729 | 0.0468 | 0.6721 | 7720 |
| fedproto_schema | 3 | 0.6684 | 0.0465 | 0.6682 | 7724 |
| shared_observable | 3 | 0.6670 | 0.0485 | 0.6668 | 7724 |
| no_schema | 3 | 0.2439 | 0.0338 | 0.2452 | 7724 |
| wrong_schema | 3 | 0.1414 | 0.0196 | 0.1419 | 11564 |

## MNIST-10 clients

### clients=10

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.7518 | 0.0347 | 0.7478 | 24364 |
| qproto_chop | 3 | 0.7479 | 0.0359 | 0.7439 | 11564 |
| qproto_cproto | 3 | 0.7473 | 0.0382 | 0.7433 | 7724 |
| fedadam_schema | 3 | 0.3709 | 0.1218 | 0.3646 | 7720 |
| fedavg_schema | 3 | 0.1944 | 0.0614 | 0.1791 | 7720 |
| fedproto_schema | 3 | 0.3602 | 0.0480 | 0.3567 | 7724 |
| shared_observable | 3 | 0.6977 | 0.0210 | 0.6934 | 7724 |
| no_schema | 3 | 0.2498 | 0.0322 | 0.2474 | 7724 |
| wrong_schema | 3 | 0.1435 | 0.0211 | 0.1446 | 11564 |

### clients=20

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.7524 | 0.0351 | 0.7483 | 24364 |
| qproto_chop | 3 | 0.7486 | 0.0403 | 0.7444 | 11564 |
| qproto_cproto | 3 | 0.7474 | 0.0402 | 0.7433 | 7724 |
| fedadam_schema | 3 | 0.4294 | 0.0845 | 0.4229 | 7720 |
| fedavg_schema | 3 | 0.2970 | 0.2591 | 0.2806 | 7720 |
| fedproto_schema | 3 | 0.4238 | 0.0610 | 0.4209 | 7724 |
| shared_observable | 3 | 0.7016 | 0.0306 | 0.6972 | 7724 |
| no_schema | 3 | 0.2243 | 0.0251 | 0.2209 | 7724 |
| wrong_schema | 3 | 0.1261 | 0.0033 | 0.1269 | 11564 |

### clients=50

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.7522 | 0.0358 | 0.7480 | 24364 |
| qproto_chop | 3 | 0.7468 | 0.0385 | 0.7426 | 11564 |
| qproto_cproto | 3 | 0.7449 | 0.0407 | 0.7407 | 7724 |
| fedadam_schema | 3 | 0.5183 | 0.0315 | 0.5078 | 7720 |
| fedavg_schema | 3 | 0.2696 | 0.1277 | 0.2533 | 7720 |
| fedproto_schema | 3 | 0.5317 | 0.0288 | 0.5263 | 7724 |
| shared_observable | 3 | 0.7018 | 0.0341 | 0.6973 | 7724 |
| no_schema | 3 | 0.1992 | 0.0075 | 0.1940 | 7724 |
| wrong_schema | 3 | 0.1151 | 0.0099 | 0.1154 | 11564 |

### clients=100

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.7525 | 0.0337 | 0.7482 | 24364 |
| qproto_chop | 3 | 0.7479 | 0.0363 | 0.7436 | 11564 |
| qproto_cproto | 3 | 0.7456 | 0.0402 | 0.7412 | 7724 |
| fedadam_schema | 3 | 0.5533 | 0.0383 | 0.5439 | 7720 |
| fedavg_schema | 3 | 0.2754 | 0.0618 | 0.2588 | 7720 |
| fedproto_schema | 3 | 0.5840 | 0.0299 | 0.5785 | 7724 |
| shared_observable | 3 | 0.7008 | 0.0366 | 0.6962 | 7724 |
| no_schema | 3 | 0.1885 | 0.0305 | 0.1829 | 7724 |
| wrong_schema | 3 | 0.1160 | 0.0062 | 0.1155 | 11564 |

## MNIST-10 overlap

### overlap=0.20

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.7372 | 0.0108 | 0.7326 | 24364 |
| qproto_chop | 3 | 0.6888 | 0.0217 | 0.6832 | 11564 |
| qproto_cproto | 3 | 0.6881 | 0.0228 | 0.6825 | 7724 |
| fedadam_schema | 3 | 0.1727 | 0.0187 | 0.1702 | 7720 |
| fedavg_schema | 3 | 0.1574 | 0.0310 | 0.1465 | 7720 |
| fedproto_schema | 3 | 0.1580 | 0.0161 | 0.1581 | 7724 |
| shared_observable | 3 | 0.5554 | 0.0464 | 0.5485 | 7724 |
| no_schema | 3 | 0.2168 | 0.0129 | 0.2143 | 7724 |
| wrong_schema | 3 | 0.1198 | 0.0168 | 0.1211 | 11564 |

### overlap=0.40

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.7395 | 0.0215 | 0.7351 | 24364 |
| qproto_chop | 3 | 0.7098 | 0.0368 | 0.7046 | 11564 |
| qproto_cproto | 3 | 0.7085 | 0.0371 | 0.7033 | 7724 |
| fedadam_schema | 3 | 0.1945 | 0.0318 | 0.1921 | 7720 |
| fedavg_schema | 3 | 0.1652 | 0.0737 | 0.1529 | 7720 |
| fedproto_schema | 3 | 0.1820 | 0.0275 | 0.1823 | 7724 |
| shared_observable | 3 | 0.6616 | 0.0471 | 0.6558 | 7724 |
| no_schema | 3 | 0.2203 | 0.0306 | 0.2181 | 7724 |
| wrong_schema | 3 | 0.1264 | 0.0175 | 0.1268 | 11564 |

### overlap=0.60

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.7369 | 0.0273 | 0.7323 | 24364 |
| qproto_chop | 3 | 0.7219 | 0.0274 | 0.7170 | 11564 |
| qproto_cproto | 3 | 0.7203 | 0.0291 | 0.7153 | 7724 |
| fedadam_schema | 3 | 0.2685 | 0.0989 | 0.2629 | 7720 |
| fedavg_schema | 3 | 0.2192 | 0.1935 | 0.2037 | 7720 |
| fedproto_schema | 3 | 0.2549 | 0.0667 | 0.2526 | 7724 |
| shared_observable | 3 | 0.6733 | 0.0199 | 0.6677 | 7724 |
| no_schema | 3 | 0.2254 | 0.0095 | 0.2231 | 7724 |
| wrong_schema | 3 | 0.1262 | 0.0037 | 0.1267 | 11564 |

### overlap=0.80

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.7524 | 0.0351 | 0.7483 | 24364 |
| qproto_chop | 3 | 0.7486 | 0.0403 | 0.7444 | 11564 |
| qproto_cproto | 3 | 0.7474 | 0.0402 | 0.7433 | 7724 |
| fedadam_schema | 3 | 0.4294 | 0.0845 | 0.4229 | 7720 |
| fedavg_schema | 3 | 0.2970 | 0.2591 | 0.2806 | 7720 |
| fedproto_schema | 3 | 0.4238 | 0.0610 | 0.4209 | 7724 |
| shared_observable | 3 | 0.7016 | 0.0306 | 0.6972 | 7724 |
| no_schema | 3 | 0.2243 | 0.0251 | 0.2209 | 7724 |
| wrong_schema | 3 | 0.1261 | 0.0033 | 0.1269 | 11564 |

### overlap=1.00

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.7455 | 0.0462 | 0.7415 | 24364 |
| qproto_chop | 3 | 0.7454 | 0.0472 | 0.7415 | 11564 |
| qproto_cproto | 3 | 0.7443 | 0.0477 | 0.7403 | 7724 |
| fedadam_schema | 3 | 0.6812 | 0.1043 | 0.6752 | 7720 |
| fedavg_schema | 3 | 0.4252 | 0.2482 | 0.4079 | 7720 |
| fedproto_schema | 3 | 0.7194 | 0.0591 | 0.7153 | 7724 |
| shared_observable | 3 | 0.7183 | 0.0598 | 0.7143 | 7724 |
| no_schema | 3 | 0.2226 | 0.0603 | 0.2203 | 7724 |
| wrong_schema | 3 | 0.1304 | 0.0076 | 0.1313 | 11564 |

## PennyLane high-order overlap

### overlap=0.20

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.5584 | 0.1350 | 0.5584 | 3476 |
| qproto_chop | 3 | 0.5927 | 0.1446 | 0.5927 | 2324 |
| qproto_cproto | 3 | 0.3849 | 0.0877 | 0.3849 | 788 |
| fedadam_schema | 3 | 0.2986 | 0.0466 | 0.2986 | 1552 |
| fedproto_schema | 3 | 0.2800 | 0.0417 | 0.2800 | 1556 |
| shared_observable | 3 | 0.4253 | 0.1093 | 0.4252 | 1556 |
| no_schema | 3 | 0.3418 | 0.0287 | 0.3418 | 1556 |
| wrong_schema | 3 | 0.2738 | 0.0144 | 0.2738 | 3092 |

### overlap=0.35

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.5430 | 0.0125 | 0.5430 | 3476 |
| qproto_chop | 3 | 0.5922 | 0.0900 | 0.5922 | 2324 |
| qproto_cproto | 3 | 0.4044 | 0.0594 | 0.4044 | 788 |
| fedadam_schema | 3 | 0.3124 | 0.0171 | 0.3124 | 1552 |
| fedproto_schema | 3 | 0.2850 | 0.0172 | 0.2850 | 1556 |
| shared_observable | 3 | 0.4414 | 0.0447 | 0.4414 | 1556 |
| no_schema | 3 | 0.3459 | 0.0373 | 0.3459 | 1556 |
| wrong_schema | 3 | 0.2675 | 0.0177 | 0.2675 | 3092 |

### overlap=0.50

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.6158 | 0.0548 | 0.6158 | 3476 |
| qproto_chop | 3 | 0.6615 | 0.0727 | 0.6615 | 2324 |
| qproto_cproto | 3 | 0.4330 | 0.0190 | 0.4330 | 788 |
| fedadam_schema | 3 | 0.3137 | 0.0394 | 0.3137 | 1552 |
| fedproto_schema | 3 | 0.2907 | 0.0413 | 0.2907 | 1556 |
| shared_observable | 3 | 0.4745 | 0.1708 | 0.4745 | 1556 |
| no_schema | 3 | 0.3496 | 0.0454 | 0.3496 | 1556 |
| wrong_schema | 3 | 0.2837 | 0.0442 | 0.2837 | 3092 |

### overlap=0.80

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.6620 | 0.1198 | 0.6620 | 3476 |
| qproto_chop | 3 | 0.6913 | 0.0559 | 0.6913 | 2324 |
| qproto_cproto | 3 | 0.4397 | 0.1017 | 0.4397 | 788 |
| fedadam_schema | 3 | 0.4290 | 0.0429 | 0.4290 | 1552 |
| fedproto_schema | 3 | 0.3936 | 0.0075 | 0.3936 | 1556 |
| shared_observable | 3 | 0.5967 | 0.0478 | 0.5967 | 1556 |
| no_schema | 3 | 0.3589 | 0.0858 | 0.3589 | 1556 |
| wrong_schema | 3 | 0.2838 | 0.0482 | 0.2838 | 3092 |

