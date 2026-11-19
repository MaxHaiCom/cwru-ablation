# Bot playbook

Bot 一次只领一个失败的格子。它可以改这个格子的配置，或者改这个格子用到的特征或模型。它不能改 `splits/`、`src/cwru/metrics.py`、`src/cwru/ladder.py` 和 `harness/check.py`。

跑之前先执行 `python3 harness/check.py`。检查失败就停，不开始训练。

每一档从父提交拉分支 `bot/cell-<id>-rung-N`，只改白名单里的一个字段，然后只重跑这一格。结果写到 `results/<cell>-rung-N.json`，里面有 git 版本、划分哈希、种子、采样率、窗长、模型、macro-F1、各类 F1 和误报率。

作废的档执行回到父提交，删掉该档权重，只留那份 json。通过才把配置写回父提交。6 档仍失败时，PR 只许新增结果 json。

熔断：

- 损失出现非有限值，或裁剪前梯度范数大于 100：杀掉，记 `fuse:nan`，学习率降一档，不从这份权重续训。梯度裁剪固定为全局范数 1.0。
- 内存或显存爆掉：记 `fuse:oom`，批大小降一档。批大小降到 8 仍爆就停，不交成功 PR。
- 单次运行超过 15 分钟：记 `fuse:timeout`，同一配置不许重试。

仓库里没有 Devin API 密钥，工作流也不调用 Devin API。
