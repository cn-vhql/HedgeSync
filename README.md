# 📊 期货套保策略分析工具

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-Educational-green.svg)

**专业的期货套保策略分析平台**
基于历史数据评估现货与期货的套保效果，助力企业风险管理

[功能特性](#-核心功能) • [快速开始](#-快速开始) • [使用指南](#-使用指南) • [API文档](#-技术文档)

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [核心功能](#-核心功能)
- [项目结构](#-项目结构)
- [快速开始](#-快速开始)
- [使用指南](#-使用指南)
- [技术文档](#-技术文档)
- [常见问题](#-常见问题)
- [贡献指南](#-贡献指南)

---

## 🎯 项目简介

期货套保策略分析工具是一个专业的量化分析平台，旨在帮助企业和投资者评估期货套保策略的有效性。该工具基于现代金融工程理论，提供完整的套保策略分析流程，从数据处理到风险量化，从历史回测到压力测试。

### 应用场景

- **库存管理**：生产企业持有现货，通过卖出期货对冲价格下跌风险
- **采购管理**：加工企业计划未来采购，通过买入期货锁定成本
- **投资分析**：金融机构评估套保策略的风险收益特征
- **学术研究**：高校和研究院所的金融工程研究

### 技术特色

- 🧠 **智能算法**：基于最小方差法的最优套保比例计算
- 📊 **全面分析**：涵盖套保比例计算、历史回测、风险量化
- 🎨 **可视化丰富**：多维度图表展示分析结果
- 🚀 **易于使用**：Streamlit构建的交互式Web界面
- 🧪 **压力测试**：评估极端行情下的套保效果

---

## ⭐ 核心功能

### 1. 📁 数据处理模块
- **现货数据导入**：支持CSV文件上传，自动验证数据格式
- **数据清洗**：处理缺失值，异常值检测
- **期货数据获取**：通过akshare库获取实时和历史数据
- **数据对齐**：智能对齐现货和期货的时间维度
- **缓存机制**：本地缓存避免重复请求

### 2. 🧮 套保比例计算
- **最小方差法**：h = cov(Δspot, Δfuture) / var(Δfuture)
- **多种方法**：OLS回归法、相关系数调整法
- **窗口选择**：支持全数据或指定时间窗口
- **有效性评估**：R²、F统计量、相关性分析
- **敏感性分析**：评估不同套保比例的效果

### 3. 📈 历史回测引擎
- **双向套保**：支持库存管理和采购管理两种模式
- **精确计算**：每日盈亏、累计收益、风险指标
- **绩效评估**：夏普比率、最大回撤、VaR、波动率
- **对比分析**：套保vs未套保的完整对比
- **滚动分析**：动态评估策略表现

### 4. 📊 可视化分析
- **价格走势图**：现货与期货价格叠加对比
- **盈亏曲线图**：套保组合累计收益曲线
- **风险雷达图**：多维度风险收益指标对比
- **敏感性分析图**：不同套保比例的效果展示
- **交互式图表**：基于Plotly的动态可视化

### 5. 🧪 压力测试模块
- **自动识别**：基于价格变化阈值识别压力时期
- **自定义测试**：支持用户指定时间区间
- **极端分析**：评估套保策略在极端行情下的表现
- **对比报告**：压力时期vs正常时期的详细对比
- **结果导出**：支持多种格式的结果导出

---

## 📂 项目结构

```
HedgeSync/
├── 📄 app.py                    # Streamlit主界面应用
├── 📄 run.py                    # 应用启动脚本
├── 📄 requirements.txt          # 依赖库清单
├── 📄 README.md                 # 项目说明文档
├── 📄 sample_data.csv           # 示例数据文件
│
├── 🧠 核心模块/
│   ├── 📄 data_processor.py      # 数据处理模块
│   ├── 📄 hedge_ratio_calculator.py  # 套保比例计算
│   ├── 📄 backtest_engine.py     # 历史回测引擎
│   ├── 📄 visualizer.py          # 可视化模块
│   └── 📄 stress_test.py         # 压力测试模块
│
└── 📁 cache/                     # 数据缓存目录
    └── 📄 future_*.csv           # 期货数据缓存文件
```

### 模块说明

| 模块 | 功能 | 主要类 |
|------|------|--------|
| `data_processor.py` | 数据获取、清洗、对齐 | `DataProcessor` |
| `hedge_ratio_calculator.py` | 套保比例计算、敏感性分析 | `HedgeRatioCalculator` |
| `backtest_engine.py` | 历史回测、绩效评估 | `BacktestEngine` |
| `visualizer.py` | 图表生成、可视化展示 | `Visualizer` |
| `stress_test.py` | 压力测试、极端分析 | `StressTestAnalyzer` |

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows, macOS, Linux
- **网络连接**: 用于获取期货数据
- **浏览器**: Chrome, Firefox, Safari, Edge (推荐Chrome)

### 安装步骤

#### 1️⃣ 克隆项目
```bash
git clone https://github.com/your-username/HedgeSync.git
cd HedgeSync
```

#### 2️⃣ 创建虚拟环境 (推荐)
```bash
# 使用 venv
python -m venv hedge_env

# 激活虚拟环境
# Windows
hedge_env\Scripts\activate
# macOS/Linux
source hedge_env/bin/activate
```

#### 3️⃣ 安装依赖
```bash
pip install -r requirements.txt
```

#### 4️⃣ 运行应用
```bash
# 方法1: 使用启动脚本
python run.py

# 方法2: 直接使用Streamlit
streamlit run app.py
```

#### 5️⃣ 访问应用
打开浏览器访问 `http://localhost:8501`

### Docker部署 (可选)

```bash
# 构建镜像
docker build -t hedge-sync .

# 运行容器
docker run -p 8501:8501 hedge-sync
```

---

## 📖 使用指南

### 数据准备

#### CSV文件格式要求
```csv
date,spot_price
2023-01-01,68000.0
2023-01-02,68200.0
2023-01-03,68500.0
```

**数据要求：**
- ✅ 必须包含 `date` 和 `spot_price` 两列
- ✅ 日期格式：YYYY-MM-DD
- ✅ 价格：数值型，不能为负数
- ✅ 建议至少包含60天以上的数据
- ✅ 数据按日期排序

### 操作流程

#### 第一步：数据上传
1. 访问"数据上传"页面
2. 上传现货价格CSV文件
3. 选择缺失值处理方式：
   - **删除**：直接删除含有缺失值的行
   - **线性插值**：使用相邻值进行插值填充
4. 验证数据格式和统计摘要

#### 第二步：配置参数
在侧边栏配置分析参数：
- **套保方向**：
  - 库存管理（现货多头）：持有现货，卖出期货对冲
  - 采购管理（现货空头）：计划采购，买入期货对冲
- **现货数量**：您持有或计划交易的现货数量
- **期货合约代码**：如CU0（沪铜主力）、AL0（沪铝主力）
- **计算窗口**：套保比例计算的历史数据窗口

#### 第三步：运行分析
1. 点击"获取期货数据并开始分析"
2. 系统自动：
   - 获取对应期货数据
   - 对齐现货和期货数据
   - 计算最优套保比例
   - 运行历史回测
3. 查看分析结果和关键指标

#### 第四步：查看结果
- **套保分析页面**：详细的盈亏和风险指标
- **可视化页面**：各类分析图表
- **压力测试页面**：极端行情分析
- **结果导出页面**：下载分析数据和报告

### 关键指标解读

#### 套保比例 (Hedge Ratio)
- **定义**：期货合约数量与现货数量的最优比率
- **计算公式**：h = cov(Δspot, Δfuture) / var(Δfuture)
- **解读**：
  - h = 1.0：1单位现货需要1单位期货对冲
  - h = 0.8：1单位现货需要0.8单位期货对冲
  - h < 0：现货与期货价格负相关

#### 套保有效性 (Hedge Effectiveness)
- **定义**：套保降低方差的程度
- **计算公式**：(未套保方差 - 套保方差) / 未套保方差
- **解读**：
  - > 80%：套保效果优秀
  - 60%-80%：套保效果良好
  - 40%-60%：套保效果一般
  - < 40%：套保效果较差

#### 风险降低率 (Risk Reduction Rate)
- **定义**：套保后波动率的降低程度
- **解读**：50%表示套保将投资组合风险降低了一半

#### 最大回撤 (Maximum Drawdown)
- **定义**：累计盈亏从峰值到谷值的最大跌幅
- **解读**：数值越小，风险控制越好

#### 夏普比率 (Sharpe Ratio)
- **定义**：单位风险的超额收益
- **解读**：数值越大，风险调整后收益越好

---

## 📚 技术文档

### 核心算法

#### 最优套保比例计算
```python
def calculate_optimal_hedge_ratio(spot_changes, future_changes):
    """使用最小方差法计算最优套保比例"""
    covariance = np.cov(spot_changes, future_changes)[0, 1]
    variance = np.var(future_changes)
    hedge_ratio = covariance / variance
    return hedge_ratio
```

#### 套保有效性评估
```python
def calculate_hedge_effectiveness(unhedged_returns, hedged_returns):
    """计算套保有效性"""
    unhedged_variance = np.var(unhedged_returns)
    hedged_variance = np.var(hedged_returns)
    effectiveness = 1 - (hedged_variance / unhedged_variance)
    return effectiveness
```

### API参考

#### DataProcessor类
```python
class DataProcessor:
    def load_spot_data(self, file_path, handle_missing="drop")
    def get_future_data(self, future_code, start_date, end_date)
    def align_data(self, spot_df, future_df)
    def get_data_summary(self, df)
```

#### HedgeRatioCalculator类
```python
class HedgeRatioCalculator:
    def calculate_optimal_hedge_ratio(self, aligned_data, window_size=None)
    def calculate_hedge_effectiveness(self, aligned_data, hedge_ratio)
    def sensitivity_analysis(self, aligned_data, base_ratio)
```

#### BacktestEngine类
```python
class BacktestEngine:
    def run_backtest(self, aligned_data, hedge_ratio, spot_quantity, hedge_direction)
    def generate_performance_summary(self)
    def calculate_rolling_metrics(self, window_size=30)
```

### 数据源

#### 期货数据获取
- **数据源**：akshare库
- **支持交易所**：上海期货交易所(SHFE)、大连商品交易所(DCE)、郑州商品交易所(CZCE)
- **数据类型**：主力合约、历史价格、结算价
- **更新频率**：日度数据

#### 缓存机制
- **缓存目录**：`./cache/`
- **缓存策略**：基于期货代码和时间范围
- **缓存格式**：CSV文件
- **自动清理**：30天后自动过期

---

## ❓ 常见问题

### Q1: 期货数据获取失败怎么办？
**A:** 检查以下几个方面：
- 网络连接是否正常
- 期货合约代码格式是否正确（如CU0、AL0等）
- 是否在交易时间内
- 稍后重试，可能是数据源临时问题

### Q2: 套保比例为负数或异常大怎么办？
**A:** 可能的原因：
- 现货和期货品种不匹配
- 数据时间范围有问题
- 市场出现异常情况
建议检查数据质量和品种对应关系

### Q3: 压力测试没有识别到压力时期？
**A:** 尝试调整参数：
- 降低价格变化阈值（如从5%降到3%）
- 减少最少连续天数要求（如从3天降到2天）
- 使用自定义压力测试功能

### Q4: 计算结果与实际交易有差异？
**A:** 本工具的局限性：
- 忽略交易成本和滑点
- 不考虑保证金要求
- 基于历史数据，未来可能不同
- 建议结合实际情况调整参数

### Q5: 如何选择合适的期货合约？
**A:** 选择原则：
- 品种匹配：期货品种应与现货品种高度相关
- 流动性好：选择交易活跃的主力合约
- 期限匹配：合约到期时间应与套保期限匹配
- 基差稳定：选择基差相对稳定的品种

---

## 🤝 贡献指南

我们欢迎社区贡献！以下是参与方式：

### 开发环境搭建

```bash
# 1. Fork项目并克隆
git clone https://github.com/your-username/HedgeSync.git

# 2. 创建开发分支
git checkout -b feature/your-feature

# 3. 安装开发依赖
pip install -r requirements.txt
pip install black flake8 pytest

# 4. 进行开发
# ...

# 5. 运行测试
pytest tests/

# 6. 提交代码
git commit -m "feat: add new feature"
git push origin feature/your-feature
```

### 代码规范

- 使用 **Python Black** 进行代码格式化
- 遵循 **PEP 8** 编码规范
- 添加详细的函数文档字符串
- 为新功能编写单元测试

### 贡献类型

- 🐛 **Bug修复**：修复现有功能问题
- ✨ **新功能**：添加新的分析功能
- 📚 **文档**：完善文档和说明
- 🎨 **界面**：改进用户界面和体验
- ⚡ **性能**：优化算法和性能

### 问题反馈

如果您发现问题或有改进建议，请：

1. 查看现有Issues是否有类似问题
2. 创建新的Issue，详细描述问题
3. 提供复现步骤和环境信息
4. 添加相关标签便于分类

---

## 📄 许可证

本项目采用 **教育用途许可证**，仅供学习和研究使用。

### 使用限制

- ✅ 教育、学习、研究用途
- ✅ 个人投资分析参考
- ❌ 商业用途
- ❅ 投资建议（本工具不构成投资建议）

### 免责声明

- 本工具基于历史数据，历史表现不代表未来结果
- 投资决策请谨慎，建议咨询专业投资顾问
- 开发者不对使用本工具造成的投资损失负责

---

## 📞 联系方式

- **项目主页**：https://github.com/your-username/HedgeSync
- **问题反馈**：https://github.com/your-username/HedgeSync/issues
- **邮箱**：your-email@example.com

---

## 🙏 致谢

感谢以下开源项目和服务：

- [Streamlit](https://streamlit.io/) - 快速构建数据应用的框架
- [Plotly](https://plotly.com/) - 交互式可视化库
- [akshare](https://www.akshare.xyz/) - 金融数据接口
- [pandas](https://pandas.pydata.org/) - 数据分析库
- [statsmodels](https://www.statsmodels.org/) - 统计建模库

---

<div align="center">

**📊 期货套保策略分析工具 | 专业的套保效果评估平台**

*构建于 ❤️ 和 ☕ 之上*

[![Star](https://img.shields.io/github/stars/your-username/HedgeSync.svg?style=social)](https://github.com/your-username/HedgeSync)
[![Fork](https://img.shields.io/github/forks/your-username/HedgeSync.svg?style=social)](https://github.com/your-username/HedgeSync/fork)

</div>