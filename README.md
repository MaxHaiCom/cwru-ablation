# cwru-ablation

可复现的凯斯西储轴承振动消融实验。第一版只做故障直径 0.007 英寸，类是正常、内圈、外圈、滚动体。四个负载分开评分。

实验矩阵在 [PLAN.md](PLAN.md)。Bot 的退避、熔断和 PR 限制在 [PLAYBOOK.md](PLAYBOOK.md)。

```sh
python3 harness/check.py
```

这条命令不需要数据，也不需要训练。它锁住划分、种子和算分函数，并检查降采样、陷波和搜索阶梯。

振动 mat 不进 git。下载方式和文件号在 [data/README.md](data/README.md)。
