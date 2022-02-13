# 模型概述

![统计语言模型SLM](https://user-images.githubusercontent.com/68272577/153758202-b27c73d3-8159-4d99-97f4-bb1eccef5c97.png)

![统计语言模型SLM2](https://user-images.githubusercontent.com/68272577/153758263-a4e03b5b-3a8e-49be-88a6-bcc4f7a92ae8.png)


马尔可夫性：马尔可夫性质（Markov property）是概率论中的一个概念，因为俄国数学家安德雷·马尔可夫得名。当一个随机过程在给定现在状态及所有过去状态情况下，其未来状态的条件概率分布仅依赖于当前状态；换句话说，在给定现在状态时，它与过去状态（即该过程的历史路径）是条件独立的，那么此随机过程即具有马尔可夫性质。具有马尔可夫性质的过程通常称之为马尔可夫过程。

---
# 策略逻辑

由于盘口价差的幅度在2015年9月后迅速放大，传统的日内交易策略对*流动性*的要求越来越高，而降低交易频率则会增加回撤的风险。因此，通过历史数据对未来做预测的T+1策略既可以克服流动性要求，又可以一定程度上缓解回撤风险。SLM策略就是T+1策略之一。

![SLM策略交易逻辑](https://user-images.githubusercontent.com/68272577/153758278-a4e4c422-16be-4f8f-8137-ac08002d900f.png)


## 原策略
- 选取1995-2004上证指数日频数据作为语料库
- 2005-2009年作为样本确定最佳模型阶数（n=6）
- 2005-2013年作为回测区间

![SLM仓位调整规则](https://user-images.githubusercontent.com/68272577/153758288-fb7b014a-d63a-4263-9806-ba73b738b4e4.png)

<br/>

## 现策略

参数寻优结果：结果显示，SLM模型阶数`lookback_period=6`的时候，策略的年化收益率最佳，这也符合回测的样本数量。当符号数量m确定为2时（上涨、下跌），模型阶数为3表示序列中可能的符号类别总共为8（$2^3$）。而本次回测的时间段仅为一年多，即只有400多天的回测样本，训练样本

寻优结果显示，模型阶数为6时，策略在样本内的表现最佳。该结果与研报结论*一致*

![Pasted image 20220121092755](https://user-images.githubusercontent.com/68272577/153758303-c05a4eb6-942d-41bf-bd7b-26ad19dc7093.png)

---
# 回测结果

## IF00

1. IF00样本内回测

参数设置
- 起始时间：2010-4-16
- 终止时间：2020-12-31
- 历史片段区间：8
- ATR计算区间：14

返回指标

|                     | 0           |
| ------------------- | ----------- |
| Annual return       | 0.17096644  |
| Cumulative returns  | 4.11169136  |
| Annual volatility   | 0.11732735  |
| Sharpe ratio        | 1.40408199  |
| Calmar ratio        | 1.37066609  |
| Stability           | 0.95798861  |
| Max drawdown        | \-0.1247324 |
| Omega ratio         | 1.28816428  |
| Sortino ratio       | 2.23267672  |
| Skew                | 0.55586794  |
| Kurtosis            | 5.4125818   |
| Tail ratio          | 1.24808105  |
| Daily value at risk | \-0.0141281 |
| Gross leverage      | 0.06439878  |
| Daily turnover      | 0.02750215  |

⚠️ 错误的使用未来数据预测当下

解决方法，滚动扩展历史数据库，将数据库时间线限制为-1

2. IF00样本外回测

参数设置
- 起始时间：2020-1-1
- 终止时间：2021-12-21
- 历史片段区间：6
- ATR计算区间：14

返回指标

|                     | 0           |
| ------------------- | ----------- |
| Annual return       | 0.23306876  |
| Cumulative returns  | 0.48794545  |
| Annual volatility   | 0.12096074  |
| Sharpe ratio        | 1.79251214  |
| Calmar ratio        | 2.80057421  |
| Stability           | 0.81448     |
| Max drawdown        | \-0.0832218 |
| Omega ratio         | 1.41002107  |
| Sortino ratio       | 3.25248818  |
| Skew                | 1.80424812  |
| Kurtosis            | 12.5063696  |
| Tail ratio          | 1.50698891  |
| Daily value at risk | \-0.0143792 |
| Gross leverage      | 0.05778883  |
| Daily turnover      | 0.02208321  |

![SLM out-sample dd_price](https://user-images.githubusercontent.com/68272577/153758331-6aed4b91-144e-4c28-80ed-7e62712958d2.png)

![SLM out-sample ann_rets](https://user-images.githubusercontent.com/68272577/153758340-f15a0573-77d4-4165-996a-4516cf3f244d.png)

## IH00

采用相同参数对IH、IC进行回测，效果均不佳

---
# 改进思路

通过*模式识别*寻找历史中是否存在与当前区间相似的时间段，计算相似区间上涨/下跌的概率，得到当前区间价格最有可能的走势

标准化数据后用[[Support Vector Machine]]（data classification）模型根据涨跌幅幅度对历史数据**精细化**

❓ Dynamic Timeseries Warping (DTW) 动态时间规整算法，提高与历史片段匹配的准确度
